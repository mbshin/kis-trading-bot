from __future__ import annotations

class OrderRouter:
    def __init__(self, mode: str):
        self.mode = mode
    async def place(self, symbol: str, side: str, qty: int, type_: str = "MKT", price: float | None = None):
        # TODO: implement KIS REST order call for overseas symbols
        return {"ok": True, "paper": self.mode == "paper"}
