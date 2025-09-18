from __future__ import annotations
import asyncio, uuid
from dataclasses import dataclass
from typing import Iterable, Tuple, Optional
from kisbot.core.indicators import StochRSI
from kisbot.core.slices import SliceBook
from kisbot.core.signals import KDTrader


def _load_prices_csv(data_dir: str, symbol: str, from_date: str, to_date: str, column: str = "close") -> Iterable[Tuple[float, float]]:
    """Yield (ts, price) from CSV at `{data_dir}/{symbol}.csv`.

    Accepted columns (case-insensitive):
    - Generic: `timestamp` or `datetime` and `<column>` (default: close)
    - Yahoo format: `Date`, `Close` (or `Adj Close` if column == 'adj_close')
    Returns timestamps as float seconds since epoch for simplicity.
    """
    import os
    import pandas as pd

    path = os.path.join(data_dir, f"{symbol}.csv")
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}

    # Determine datetime column
    dt_col = None
    for candidate in ("timestamp", "datetime", "date"):
        if candidate in cols:
            dt_col = cols[candidate]
            break
    if not dt_col:
        raise ValueError(f"No datetime column found in {path}")

    # Determine price column
    price_key = column.lower()
    if price_key == "adj_close" and "adj close" in cols:
        px_col = cols["adj close"]
    elif price_key in cols:
        px_col = cols[price_key]
    elif price_key == "close" and "close" in cols:
        px_col = cols["close"]
    else:
        raise ValueError(f"Price column '{column}' not found in {path}")

    df[dt_col] = pd.to_datetime(df[dt_col], utc=True)
    from_ts = pd.Timestamp(from_date, tz='UTC')
    to_ts = pd.Timestamp(to_date, tz='UTC')
    mask = (df[dt_col] >= from_ts) & (df[dt_col] <= to_ts)
    df = df.loc[mask].sort_values(dt_col)

    for _, row in df.iterrows():
        ts = pd.Timestamp(row[dt_col]).timestamp()
        yield ts, float(row[px_col])


@dataclass
class SimState:
    qty: int = 0
    avg_px: float = 0.0
    realized: float = 0.0

    def buy(self, qty: int, px: float):
        new_notional = self.avg_px * self.qty + px * qty
        self.qty += qty
        self.avg_px = new_notional / max(self.qty, 1)

    def sell_all(self, px: float):
        if self.qty <= 0:
            return
        self.realized += (px - self.avg_px) * self.qty
        self.qty = 0
        self.avg_px = 0.0


def _merge_dicts(base: dict, overlay: dict) -> dict:
    out = dict(base)
    for k, v in (overlay or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dicts(out[k], v)
        else:
            out[k] = v
    return out


async def backtest(cfg, from_date: str, to_date: str, symbols: list[str], quiet: bool = False):
    bars_cfg = cfg.get("bars", {})
    mode = bars_cfg.get("type", "tick")
    data_dir = bars_cfg.get("data_dir")
    price_col = bars_cfg.get("column", "close")

    results = []
    for sym in symbols:
        scfg = _merge_dicts(cfg, (cfg.get('symbols') or {}).get(sym, {}))
        stoch = StochRSI(scfg['strategy']['rsi_period'], scfg['strategy']['stoch_period'], scfg['strategy']['k_period'], scfg['strategy']['d_period'])
        book = SliceBook(scfg['risk']['equity'], scfg['slices']['total'])
        trader = KDTrader(sym, book, scfg)
        sim = SimState()

        def place(symbol: str, side: str, qty: int, type_: str):
            nonlocal sim, last_px
            if side == "BUY":
                sim.buy(qty, last_px)
            else:
                sim.sell_all(last_px)
        def place_rsi(symbol: str, side: str, qty: int, type_: str, price: float):
            # Ignore price in backtest fill; use last_px for execution
            nonlocal sim, last_px
            if side == "BUY":
                sim.buy(qty, last_px)
            else:
                sim.sell_all(last_px)

        last_px: float = 0.0

        if mode == "csv" and data_dir:
            stream = _load_prices_csv(data_dir, sym, from_date, to_date, column=price_col)
        else:
            # Synthetic fallback generator
            def _synthetic():
                px = 100.0
                import time
                now = 0.0
                for i in range(5000):
                    px += (0.05 if i % 2 == 0 else -0.03)
                    now += 1.0
                    yield now, px
            stream = _synthetic()

        for ts, px in stream:
            last_px = px
            k, d = stoch.update(px)
            if k is None or d is None:
                # Even if K/D not ready, RSI might be
                rsi_val = stoch.rsi.last
                if rsi_val is not None:
                    trader.on_rsi(rsi_val, px, ts, place_order=place_rsi)
                continue
            # RSI-based buy path
            rsi_val = stoch.rsi.last
            if rsi_val is not None:
                trader.on_rsi(rsi_val, px, ts, place_order=place_rsi)
            trader.on_kd(k, d, px, ts, place_order=place)

        unrealized = (last_px - sim.avg_px) * sim.qty if sim.qty > 0 else 0.0
        results.append({
            "symbol": sym,
            "realized_pnl": round(sim.realized, 2),
            "unrealized_pnl": round(unrealized, 2),
            "position_qty_end": sim.qty,
            "slices_in_use_end": book.slices_in_use,
        })

    agg_realized = round(sum(m.get("realized_pnl", 0.0) for m in results), 2)
    agg_unrealized = round(sum(m.get("unrealized_pnl", 0.0) for m in results), 2)
    out = {
        "run_id": str(uuid.uuid4()),
        "metrics": results,
        "aggregate": {
            "symbols": len(results),
            "total_realized_pnl": agg_realized,
            "total_unrealized_pnl": agg_unrealized,
        },
    }
    if not quiet:
        print(out)
    return out
