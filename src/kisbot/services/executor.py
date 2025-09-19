from __future__ import annotations
import uuid
from kisbot.infra.logger import log
from kisbot.infra.slack import notify
from kisbot.infra.rest_client import OrderRouter
from kisbot.db import crud

class Executor:
    def __init__(self, cfg):
        self.cfg = cfg
        self.mode = cfg.get('mode', 'paper')
        self.router = OrderRouter(self.mode)

    async def place(
        self,
        symbol: str,
        side: str,
        qty: int,
        type_: str = "MKT",
        price: float | None = None,
    ):
        clordid = str(uuid.uuid4())
        await self.router.place(symbol, side, qty, type_, price)
        await crud.insert_order(
            clordid,
            symbol,
            side,
            qty,
            type_,
            price,
            status="SUBMITTED",
            mode=self.mode,
        )
        log("order.submit", symbol=symbol, side=side, qty=qty, type=type_, mode=self.mode)
        slack_cfg = self.cfg.get('slack') or {}
        text = f"[{self.mode}] {symbol} {side} {qty} {type_}"
        await notify(slack_cfg.get('webhook_url', ''), text)
        return clordid
