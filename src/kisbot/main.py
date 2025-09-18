from __future__ import annotations
import asyncio
from pathlib import Path
import typer, yaml
from pydantic import BaseModel
from kisbot.services.trader import run_bot
from kisbot.infra import logger as logmod
from kisbot.db.base import init_db
from kisbot.infra.backtest import backtest

app = typer.Typer(help="KIS 3x ETF bot")

class AppConfig(BaseModel):
    mode: str
    universe: list[str]
    ws: dict
    bars: dict
    strategy: dict
    slices: dict
    risk: dict
    execution: dict
    postgres: dict
    opensearch: dict
    slack: dict

@app.command()
def run(config: Path = typer.Option(..., exists=True, readable=True)):
    cfg = AppConfig.model_validate(yaml.safe_load(config.read_text()))
    logmod.configure_json_logging(cfg.opensearch.get("index_prefix", "bot-logs"))
    asyncio.run(init_db(cfg.postgres["dsn"]))
    asyncio.run(run_bot(cfg.model_dump()))

@app.command()
def backtest_cmd(config: Path, from_: str, to: str, symbols: str = "TQQQ"):
    cfg = AppConfig.model_validate(yaml.safe_load(config.read_text()))
    logmod.configure_json_logging(cfg.opensearch.get("index_prefix", "bot-logs"))
    asyncio.run(backtest(cfg.model_dump(), from_, to, symbols.split(",")))

if __name__ == "__main__":
    app()
