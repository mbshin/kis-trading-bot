from __future__ import annotations
import asyncio, time
from kisbot.infra.ws_client import WSClient
from kisbot.core.indicators import StochRSI
from kisbot.core.slices import SliceBook
from kisbot.core.signals import KDTrader
from kisbot.infra.logger import log
from kisbot.services.executor import Executor
from kisbot.db import crud

async def run_bot(cfg):
    symbols = cfg['universe']
    ex = Executor(cfg)
    stoch = {s: StochRSI(cfg['strategy']['rsi_period'], cfg['strategy']['stoch_period'], cfg['strategy']['k_period'], cfg['strategy']['d_period']) for s in symbols}
    books = {s: SliceBook(cfg['risk']['equity'], cfg['slices']['total']) for s in symbols}
    traders = {s: KDTrader(s, books[s], cfg) for s in symbols}

    def on_tick(sym: str, price: float, now: float):
        k, d = stoch[sym].update(price)
        if k is None or d is None:
            return
        asyncio.create_task(crud.insert_signal(sym, side="TICK", k=k, d=d))
        traders[sym].on_kd(k, d, price, now, place_order=lambda sy, si, q, t: asyncio.create_task(ex.place(sy, si, q, t)))

    ws = WSClient(symbols, on_tick)
    log("bot.start", symbols=symbols, mode=cfg['mode'])
    await ws.run()
