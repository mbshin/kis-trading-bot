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
