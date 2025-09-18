from __future__ import annotations
import math
from collections import deque
from typing import Optional, Tuple

class WilderRSI:
    def __init__(self, period: int = 14):
        self.period = period
        self.prev = None
        self.gain = None
        self.loss = None
        self.count = 0
        self.last = None
    def update(self, price: float) -> Optional[float]:
        if self.prev is None:
            self.prev = price
            return None
        change = price - self.prev
        self.prev = price
        up = max(change, 0.0)
        down = -min(change, 0.0)
        if self.count < self.period:
            self.gain = (0.0 if self.gain is None else self.gain) + up
            self.loss = (0.0 if self.loss is None else self.loss) + down
            self.count += 1
            return None
        elif self.count == self.period:
            avg_gain = (self.gain or 0.0) / self.period
            avg_loss = (self.loss or 0.0) / self.period
            rs = math.inf if avg_loss == 0 else (avg_gain / avg_loss)
            self.last = 100.0 - 100.0 / (1.0 + rs)
            self.count += 1
            return self.last
        else:
            assert self.gain is not None and self.loss is not None
            self.gain = (self.gain * (self.period - 1) + up) / self.period
            self.loss = (self.loss * (self.period - 1) + down) / self.period
            rs = math.inf if self.loss == 0 else (self.gain / self.loss)
            self.last = 100.0 - 100.0 / (1.0 + rs)
            return self.last

class RollingSMA:
    def __init__(self, period: int):
        self.period = period
        self.buf = deque(maxlen=period)
        self.sum = 0.0
    def update(self, x: float):
        if len(self.buf) == self.period:
            self.sum -= self.buf[0]
        self.buf.append(x)
        self.sum += x
        if len(self.buf) < self.period:
            return None
        return self.sum / self.period

class StochRSI:
    def __init__(self, rsi_period=14, stoch_period=14, k_period=3, d_period=3):
        self.rsi = WilderRSI(rsi_period)
        self.stoch_period = stoch_period
        self.rsi_window = deque(maxlen=stoch_period)
        self.k_sma = RollingSMA(k_period)
        self.d_sma = RollingSMA(d_period)
        self.prev_k = None
        self.prev_d = None
    def update(self, price: float) -> Tuple[Optional[float], Optional[float]]:
        rsi_val = self.rsi.update(price)
        if rsi_val is None:
            return None, None
        self.rsi_window.append(rsi_val)
        if len(self.rsi_window) < self.stoch_period:
            return None, None
        rsi_min, rsi_max = min(self.rsi_window), max(self.rsi_window)
        stoch = 50.0 if rsi_max == rsi_min else (rsi_val - rsi_min) / (rsi_max - rsi_min) * 100.0
        k = self.k_sma.update(stoch)
        if k is None:
            return None, None
        d = self.d_sma.update(k)
        if d is None:
            return None, None
        self.prev_k, self.prev_d = k, d
        return k, d
