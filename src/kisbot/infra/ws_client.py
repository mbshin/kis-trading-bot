from __future__ import annotations
import asyncio
from typing import Callable, List

class WSClient:
    def __init__(self, symbols: List[str], on_tick: Callable[[str, float, float], None]):
        self.symbols = symbols
        self.on_tick = on_tick
    async def run(self):
        import random, time
        while True:
            for s in self.symbols:
                price = 100 + random.random() * 2
                now = time.time()
                self.on_tick(s, price, now)
            await asyncio.sleep(1)
