from __future__ import annotations
class KDTrader:
    def __init__(self, symbol: str, slice_book, cfg):
        self.symbol = symbol
        self.book = slice_book
        self.cfg = cfg
        self.position_qty = 0
        self.prev_k = None
        self.prev_d = None
        self.last_add_ts = 0
    def _cooldown_ok(self, now):
        return (now - self.last_add_ts) >= self.cfg['strategy']['add_cooldown_sec']
    def on_kd(self, k: float, d: float, last_px: float, now: float,
              place_order, equity_fetch=None, min_lot=1):
        prev_k, prev_d = self.prev_k, self.prev_d
        self.prev_k, self.prev_d = k, d
        if equity_fetch:
            self.book.equity = equity_fetch()
        # BUY bands
        if self._cooldown_ok(now) and last_px > 0:
            # K < 20 -> 4 slices
            if k < self.cfg['strategy']['oversold']:
                per_entry = self.cfg['slices']['per_entry_lt20']
                notional = self.book.reserve(per_entry)
                if notional > 0:
                    qty = max(min_lot, int(notional // last_px))
                    if qty > 0:
                        place_order(self.symbol, "BUY", qty, "MKT")
                        self.position_qty += qty
                        self.last_add_ts = now
            # 20 ≤ K < 80 and K↑D -> 1 slice
            elif self.cfg['strategy']['oversold'] <= k < self.cfg['strategy']['overbought']:
                bullish = prev_k is not None and prev_d is not None and prev_k <= prev_d and k > d
                if bullish:
                    per_entry = self.cfg['slices']['per_entry_20_80']
                    notional = self.book.reserve(per_entry)
                    if notional > 0:
                        qty = max(min_lot, int(notional // last_px))
                        if qty > 0:
                            place_order(self.symbol, "BUY", qty, "MKT")
                            self.position_qty += qty
                            self.last_add_ts = now
            # K ≥ 80 -> no buys
        # SELL: K↓D and K>80 -> sell all
        bearish = prev_k is not None and prev_d is not None and prev_k > prev_d and k <= d
        if bearish and k > self.cfg['strategy']['overbought'] and self.position_qty > 0:
            place_order(self.symbol, "SELL", self.position_qty, "MKT")
            self.position_qty = 0
            self.book.free_all()
