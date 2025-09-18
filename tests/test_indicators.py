from __future__ import annotations
from kisbot.core.indicators import StochRSI


def test_stochrsi_warmup_and_range():
    s = StochRSI(rsi_period=14, stoch_period=14, k_period=3, d_period=3)

    k = d = None
    # Feed enough ticks to surpass warmup (~33 for defaults)
    price = 100.0
    for i in range(120):
        # small oscillation to produce RSI variability
        price += (0.3 if i % 2 == 0 else -0.2)
        k, d = s.update(price)

    assert k is not None and d is not None
    assert 0.0 <= k <= 100.0
    assert 0.0 <= d <= 100.0

