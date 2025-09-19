from __future__ import annotations


class KDTrader:
    def __init__(self, symbol: str, slice_book, cfg):
        self.symbol = symbol
        self.book = slice_book
        self.cfg = cfg
        self.position_qty = 0
        self.avg_px = 0.0
        self.prev_k = None
        self.prev_d = None
        self.last_buy_day = None  # legacy attribute retained for compatibility (unused)
        self.last_px = None
        self.last_rsi = None
        self.batch_active = False
        self.batch_first_order_done = False
        self.batch_slice_allocation = 0

    # Batch helpers -----------------------------------------------------
    def _reset_batch(self) -> None:
        self.batch_active = False
        self.batch_first_order_done = False
        self.batch_slice_allocation = 0

    def _select_batch_slices(self, rsi: float) -> int:
        low_band = float(self.cfg["strategy"].get("rsi_low_band", 20.0))
        mid_band = float(self.cfg["strategy"].get("rsi_mid_band", 80.0))
        if rsi < low_band:
            return int(self.cfg["slices"].get("per_entry_lt20", 0))
        if rsi < mid_band:
            return int(self.cfg["slices"].get("per_entry_20_80", 0))
        return 0

    # Signal handlers ---------------------------------------------------
    def on_rsi(
        self,
        rsi: float,
        last_px: float,
        now: float,
        place_order,
        equity_fetch=None,
        min_lot: int = 1,
    ) -> None:
        self.last_rsi = rsi
        prev_px = self.last_px
        self.last_px = last_px

        if rsi is None or last_px <= 0:
            return
        if equity_fetch:
            self.book.equity = equity_fetch()

        mult = float(self.cfg["strategy"].get("rsi_buy_multiplier", 1.1))
        threshold = float(self.cfg["strategy"].get("rsi_buy_threshold", 50.0))

        if not self.batch_active:
            if self.position_qty != 0:
                return
            if prev_px is None or last_px >= prev_px:
                return
            if rsi >= threshold:
                return
            per_entry = self._select_batch_slices(rsi)
            if per_entry <= 0 or not self.book.can_add(per_entry):
                return
            self.batch_active = True
            self.batch_first_order_done = False
            self.batch_slice_allocation = per_entry

        per_entry = self.batch_slice_allocation
        if per_entry <= 0:
            self._reset_batch()
            return
        if not self.book.can_add(per_entry):
            self._reset_batch()
            return

        notional = self.book.reserve(per_entry)
        if notional <= 0:
            self._reset_batch()
            return

        order_price = last_px if not self.batch_first_order_done else self.avg_px * mult
        if order_price <= 0:
            self.book.slices_in_use -= per_entry
            self._reset_batch()
            return

        qty = max(min_lot, int(notional // max(order_price, 1e-9)))
        if qty <= 0:
            self.book.slices_in_use -= per_entry
            self._reset_batch()
            return

        if self.batch_first_order_done:
            place_order(self.symbol, "BUY", qty, "LOC", order_price)
        else:
            place_order(self.symbol, "BUY", qty, "MKT")

        prev_qty = self.position_qty
        self.position_qty += qty
        # Recalculate VWAP-style average
        self.avg_px = ((self.avg_px * prev_qty) + last_px * qty) / max(self.position_qty, 1)
        self.batch_first_order_done = True

    def on_kd(
        self,
        k: float,
        d: float,
        last_px: float,
        now: float,
        place_order,
        equity_fetch=None,
        min_lot: int = 1,
    ) -> None:
        prev_k, prev_d = self.prev_k, self.prev_d
        self.prev_k, self.prev_d = k, d
        self.last_px = last_px

        if equity_fetch:
            self.book.equity = equity_fetch()

        sl_pct = self.cfg["strategy"].get("stop_loss_pct")
        if self.position_qty > 0 and self.avg_px > 0 and sl_pct:
            if last_px <= self.avg_px * (1.0 - sl_pct):
                place_order(self.symbol, "SELL", self.position_qty, "MKT")
                self.position_qty = 0
                self.avg_px = 0.0
                self.book.free_all()
                self._reset_batch()
                return

        enable_kd_buys = bool(self.cfg["strategy"].get("enable_kd_buys", True))
        if enable_kd_buys and last_px > 0:
            if k < self.cfg["strategy"]["oversold"]:
                per_entry = self.cfg["slices"]["per_entry_lt20"]
                notional = self.book.reserve(per_entry)
                if notional > 0:
                    qty = max(min_lot, int(notional // last_px))
                    if qty > 0:
                        place_order(self.symbol, "BUY", qty, "MKT")
                        self.position_qty += qty
                        self.avg_px = (
                            (self.avg_px * (self.position_qty - qty)) + last_px * qty
                        ) / max(self.position_qty, 1)
            elif self.cfg["strategy"]["oversold"] <= k < self.cfg["strategy"]["overbought"]:
                bullish = (
                    prev_k is not None
                    and prev_d is not None
                    and prev_k <= prev_d
                    and k > d
                )
                if bullish:
                    per_entry = self.cfg["slices"]["per_entry_20_80"]
                    notional = self.book.reserve(per_entry)
                    if notional > 0:
                        qty = max(min_lot, int(notional // last_px))
                        if qty > 0:
                            place_order(self.symbol, "BUY", qty, "MKT")
                            self.position_qty += qty
                            self.avg_px = (
                                (self.avg_px * (self.position_qty - qty)) + last_px * qty
                            ) / max(self.position_qty, 1)

        bearish = prev_k is not None and prev_d is not None and prev_k > prev_d and k <= d
        rsi_ok = self.last_rsi is not None and self.last_rsi > 80.0
        if bearish and k > self.cfg["strategy"]["overbought"] and self.position_qty > 0 and rsi_ok:
            place_order(self.symbol, "SELL", self.position_qty, "MKT")
            self.position_qty = 0
            self.avg_px = 0.0
            self.book.free_all()
            self._reset_batch()

        tp_pct = self.cfg["strategy"].get("take_profit_pct", 0.11)
        if self.position_qty > 0 and self.avg_px > 0 and last_px >= self.avg_px * (1.0 + tp_pct):
            place_order(self.symbol, "SELL", self.position_qty, "MKT")
            self.position_qty = 0
            self.avg_px = 0.0
            self.book.free_all()
            self._reset_batch()
