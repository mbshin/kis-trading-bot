from __future__ import annotations
from kisbot.core.slices import SliceBook
from kisbot.core.signals import KDTrader


def _cfg():
    return {
        "strategy": {
            "rsi_period": 14,
            "stoch_period": 14,
            "k_period": 3,
            "d_period": 3,
            "overbought": 80,
            "oversold": 20,
            "add_cooldown_sec": 1,
            # defaults for new options (disabled unless set)
            # "take_profit_pct": 0.11,
            # "stop_loss_pct": 0.1,
            # "trend_sma_period": 0,
        },
        "slices": {"total": 60, "per_entry_lt20": 4, "per_entry_20_80": 1},
        "risk": {"equity": 6000},
    }


def test_kdtrader_buy_and_sell_all():
    cfg = _cfg()
    book = SliceBook(equity=cfg["risk"]["equity"], slices_total=cfg["slices"]["total"])
    t = KDTrader("TQQQ", book, cfg)

    placed = []

    def place(symbol, side, qty, type_):
        placed.append((symbol, side, qty, type_))

    # Force a BUY: k < oversold
    t.on_kd(k=10.0, d=15.0, last_px=100.0, now=1000.0, place_order=place)

    assert placed, "Expected a BUY order"
    assert placed[-1][1] == "BUY"
    assert t.position_qty > 0
    assert book.slices_in_use > 0

    # Set previous to a bearish crossover state and trigger SELL ALL (k>80 and k <= d)
    t.prev_k, t.prev_d = 85.0, 80.0
    t.on_kd(k=81.0, d=82.0, last_px=101.0, now=2000.0, place_order=place)

    assert placed[-1][1] == "SELL"
    assert t.position_qty == 0
    assert book.slices_in_use == 0


def test_kdtrader_take_profit_sell():
    cfg = _cfg()
    # Set a custom TP to 10% for deterministic test
    cfg["strategy"]["take_profit_pct"] = 0.10
    book = SliceBook(equity=cfg["risk"]["equity"], slices_total=cfg["slices"]["total"])
    t = KDTrader("TQQQ", book, cfg)

    placed = []

    def place(symbol, side, qty, type_):
        placed.append((symbol, side, qty, type_))

    # Trigger a BUY at price 100 (cooldown satisfied)
    t.on_kd(k=10.0, d=15.0, last_px=100.0, now=10.0, place_order=place)
    assert t.position_qty > 0
    avg = t.avg_px
    assert avg == 100.0 or avg > 0

    # Price jumps above TP threshold (use 12% to pass even with default 11%)
    t.prev_k, t.prev_d = 50.0, 40.0  # avoid bearish sell, ensure only TP triggers
    t.on_kd(k=50.0, d=40.0, last_px=112.0, now=20.0, place_order=place)

    assert placed[-1][1] == "SELL"
    assert t.position_qty == 0
    assert book.slices_in_use == 0


def test_kdtrader_stop_loss_sell():
    cfg = _cfg()
    cfg["strategy"]["stop_loss_pct"] = 0.10
    book = SliceBook(equity=cfg["risk"]["equity"], slices_total=cfg["slices"]["total"])
    t = KDTrader("SOXL", book, cfg)

    placed = []

    def place(symbol, side, qty, type_):
        placed.append((symbol, side, qty, type_))

    # Buy at 100
    t.on_kd(k=10.0, d=15.0, last_px=100.0, now=10.0, place_order=place)
    assert t.position_qty > 0
    # Price drops 11% -> stop-loss triggers
    t.on_kd(k=30.0, d=25.0, last_px=89.0, now=20.0, place_order=place)
    assert placed[-1][1] == "SELL"
    assert t.position_qty == 0
    assert book.slices_in_use == 0


def test_kdtrader_trend_filter_blocks_buy():
    cfg = _cfg()
    cfg["strategy"]["trend_sma_period"] = 3
    book = SliceBook(equity=cfg["risk"]["equity"], slices_total=cfg["slices"]["total"])
    t = KDTrader("SOXL", book, cfg)

    placed = []

    def place(symbol, side, qty, type_):
        placed.append((symbol, side, qty, type_))

    # Warm-up SMA with descending prices to keep last_px < SMA
    prices = [100.0, 99.0, 98.5, 98.0]
    k, d = 10.0, 15.0
    now = 0.0
    for p in prices[:-1]:
        now += 10.0
        t.on_kd(k, d, last_px=p, now=now, place_order=place)
    # At last price, SMA exists and last_px is below SMA -> buy should be blocked
    t.on_kd(k, d, last_px=prices[-1], now=now + 10.0, place_order=place)
    assert not placed, "Trend filter should block buy when price < SMA"
