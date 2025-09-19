from __future__ import annotations
import asyncio, time
from kisbot.infra.ws_client import WSClient
from kisbot.core.indicators import StochRSI
from kisbot.core.slices import SliceBook
from kisbot.core.signals import KDTrader
from kisbot.infra.logger import log
from kisbot.services.executor import Executor
from kisbot.db import crud

def _merge_dicts(base: dict, overlay: dict) -> dict:
    out = dict(base)
    for k, v in (overlay or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dicts(out[k], v)
        else:
            out[k] = v
    return out


async def run_bot(cfg):
    symbols = cfg.get('universe') or []
    ex = Executor(cfg)

    def cfg_for(sym: str) -> dict:
        return _merge_dicts(cfg, (cfg.get('symbols') or {}).get(sym, {}))

    stoch = {}
    books = {}
    traders = {}
    for s in symbols:
        scfg = cfg_for(s)
        strat = scfg['strategy']
        stoch[s] = StochRSI(strat['rsi_period'], strat['stoch_period'], strat['k_period'], strat['d_period'])
        books[s] = SliceBook(scfg['risk']['equity'], scfg['slices']['total'])
        traders[s] = KDTrader(s, books[s], scfg)

    def on_tick(sym: str, price: float, now: float):
        k, d = stoch[sym].update(price)
        # Attempt RSI-based buy path when RSI is available
        rsi_val = stoch[sym].rsi.last
        if rsi_val is not None:
            traders[sym].on_rsi(
                rsi_val,
                price,
                now,
                place_order=lambda sy, si, q, t, px=None: asyncio.create_task(
                    ex.place(sy, si, q, t, px)
                ),
            )
        if k is None or d is None:
            return
        asyncio.create_task(crud.insert_signal(sym, side="TICK", k=k, d=d))
        traders[sym].on_kd(k, d, price, now, place_order=lambda sy, si, q, t: asyncio.create_task(ex.place(sy, si, q, t)))

    ws = WSClient(symbols, on_tick)
    log("bot.start", symbols=symbols, mode=cfg['mode'])
    await ws.run()
