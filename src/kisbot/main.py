from __future__ import annotations
import asyncio
from pathlib import Path
import typer, yaml
from pydantic import BaseModel
from kisbot.services.trader import run_bot
from kisbot.infra import logger as logmod
from kisbot.db.base import init_db
from kisbot.infra.backtest import backtest
import json, csv

app = typer.Typer(help="KIS 3x ETF bot")

class AppConfig(BaseModel):
    mode: str = "paper"
    universe: list[str] = []
    ws: dict = {}
    bars: dict = {}
    strategy: dict = {}
    slices: dict = {}
    risk: dict = {}
    execution: dict | None = None
    postgres: dict | None = None
    opensearch: dict | None = None
    slack: dict | None = None
    symbols: dict | None = None

@app.command()
def run(config: Path = typer.Option(..., exists=True, readable=True)):
    cfg = AppConfig.model_validate(yaml.safe_load(config.read_text()))
    if cfg.opensearch:
        logmod.configure_json_logging(cfg.opensearch.get("index_prefix", "bot-logs"))
    cfg_dict = cfg.model_dump()
    if cfg.postgres and cfg.postgres.get("dsn"):
        asyncio.run(init_db(cfg.postgres["dsn"]))
    asyncio.run(run_bot(cfg_dict))

@app.command()
def backtest(config: Path,
             from_: str,
             to: str,
             symbols: str = "TQQQ",
             out_json: Path | None = None,
             out_csv: Path | None = None):
    cfg = AppConfig.model_validate(yaml.safe_load(config.read_text()))
    if cfg.opensearch:
        logmod.configure_json_logging(cfg.opensearch.get("index_prefix", "bot-logs"))
    res = asyncio.run(backtest(cfg.model_dump(), from_, to, symbols.split(",")))
    if out_json is not None:
        out_json.write_text(json.dumps(res, indent=2))
    if out_csv is not None:
        rows = res.get("metrics", [])
        with out_csv.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["symbol", "realized_pnl", "unrealized_pnl", "position_qty_end", "slices_in_use_end"])
            for m in rows:
                w.writerow([
                    m.get("symbol"),
                    m.get("realized_pnl"),
                    m.get("unrealized_pnl"),
                    m.get("position_qty_end"),
                    m.get("slices_in_use_end"),
                ])
            agg = res.get("aggregate", {})
            if agg:
                w.writerow([
                    "__TOTAL__",
                    agg.get("total_realized_pnl"),
                    agg.get("total_unrealized_pnl"),
                    "",
                    "",
                ])

if __name__ == "__main__":
    app()
