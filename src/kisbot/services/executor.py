from __future__ import annotations
import uuid
from kisbot.infra.logger import log
from kisbot.infra.slack import notify
from kisbot.infra.rest_client import OrderRouter
from kisbot.db import crud

class Executor:
    def __init__(self, cfg):
        self.cfg = cfg
        self.router = OrderRouter(cfg['mode'])
    async def place(self, symbol: str, side: str, qty: int, type_: str = "MKT", price: float | None = None):
        clordid = str(uuid.uuid4())
        res = await self.router.place(symbol, side, qty, type_, price)
        await crud.insert_order(clordid, symbol, side, qty, type_, price, status="SUBMITTED", mode=self.cfg['mode'])
        log("order.submit", symbol=symbol, side=side, qty=qty, type=type_, mode=self.cfg['mode'])
        text = f"[{self.cfg['mode']}] {symbol} {side} {qty} {type_}"
        await notify(self.cfg['slack'].get('webhook_url', ''), text)
        return clordid
