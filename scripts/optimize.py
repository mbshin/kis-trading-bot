from __future__ import annotations
import argparse
import asyncio
import datetime as dt
from copy import deepcopy
from pathlib import Path
import yaml
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kisbot.infra.backtest import backtest


def parse_args():
    p = argparse.ArgumentParser(description="Grid search strategy params for a symbol")
    p.add_argument("--symbol", required=True)
    p.add_argument("--from", dest="from_", required=True)
    p.add_argument("--to", required=False, default=dt.date.today().isoformat())
    p.add_argument("--config", default=str(ROOT / "config.yaml"))
    p.add_argument("--top", type=int, default=10)
    return p.parse_args()


def grid():
    # Keep small to run quickly; adjust as needed
    return {
        "strategy.take_profit_pct": [0.08, 0.10, 0.11, 0.12, 0.14],
        "strategy.oversold": [15, 20, 25],
        "strategy.overbought": [75, 80, 85],
        "strategy.add_cooldown_sec": [30, 45, 60],
        "slices.per_entry_lt20": [2, 4, 6],
        "slices.per_entry_20_80": [1, 2],
    }


def iter_params(g: dict):
    from itertools import product
    keys = list(g.keys())
    for vals in product(*[g[k] for k in keys]):
        yield dict(zip(keys, vals))


def assign(cfg: dict, updates: dict):
    cfg2 = deepcopy(cfg)
    for k, v in updates.items():
        cur = cfg2
        parts = k.split(".")
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = v
    return cfg2


async def main():
    args = parse_args()
    base_cfg = yaml.safe_load(open(args.config))
    base_cfg.setdefault("bars", {}).update({"type": "csv", "data_dir": "data", "column": "close"})

    results = []
    for upd in iter_params(grid()):
        cfg = assign(base_cfg, upd)
        res = await backtest(cfg, args.from_, args.to, [args.symbol])
        m = res["metrics"][0]
        score = float(m.get("realized_pnl", 0.0))
        results.append((score, upd, m))

    # Sort by realized PnL desc
    results.sort(key=lambda x: x[0], reverse=True)
    topn = results[: args.top]
    print("\nTop configurations by realized PnL:")
    for rank, (score, upd, m) in enumerate(topn, 1):
        print(f"{rank:>2}. pnl={score:>10.2f} cfg={upd} metrics={m}")


if __name__ == "__main__":
    asyncio.run(main())

