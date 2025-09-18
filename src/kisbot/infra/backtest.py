from __future__ import annotations
import asyncio, uuid
from kisbot.core.indicators import StochRSI
from kisbot.core.slices import SliceBook
from kisbot.core.signals import KDTrader

async def backtest(cfg, from_date: str, to_date: str, symbols: list[str]):
    # Placeholder synthetic backtest. Replace with real CSV/Parquet loader.
    results = []
    for sym in symbols:
        stoch = StochRSI(cfg['strategy']['rsi_period'], cfg['strategy']['stoch_period'], cfg['strategy']['k_period'], cfg['strategy']['d_period'])
        book = SliceBook(cfg['risk']['equity'], cfg['slices']['total'])
        trader = KDTrader(sym, book, cfg)
        px = 100.0
        for i in range(5000):
            px += (0.05 if i % 2 == 0 else -0.03)
            k, d = stoch.update(px)
            if k is None or d is None:
                continue
            trader.on_kd(k, d, px, i, place_order=lambda s, side, qty, t: None)
        results.append({"symbol": sym, "slices_in_use_end": book.slices_in_use})
    print({"run_id": str(uuid.uuid4()), "metrics": results})
