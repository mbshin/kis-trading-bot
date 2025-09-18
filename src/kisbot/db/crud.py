from __future__ import annotations
from datetime import datetime
from .base import Session
from . import models as M

async def insert_signal(symbol: str, side: str, k: float, d: float, note: str | None = None):
    async with Session() as s:
        s.add(M.Signal(ts=datetime.utcnow(), symbol=symbol, side=side, k=k, d=d, note=note))
        await s.commit()

async def insert_order(clordid: str, symbol: str, side: str, qty: int, type_: str, px: float | None, status: str, mode: str):
    async with Session() as s:
        s.add(M.Order(ts=datetime.utcnow(), clordid=clordid, symbol=symbol, side=side, qty=qty, type=type_, px=px, status=status, mode=mode))
        await s.commit()
