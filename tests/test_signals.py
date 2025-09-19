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
            "rsi_buy_threshold": 50,
            "rsi_buy_multiplier": 1.1,
        },
        "slices": {"total": 60, "per_entry_lt20": 4, "per_entry_20_80": 1},
        "risk": {"equity": 6000},
    }


def test_kd_sell_requires_rsi_confirmation():
    cfg = _cfg()
    book = SliceBook(cfg["risk"]["equity"], cfg["slices"]["total"])
    trader = KDTrader("TQQQ", book, cfg)

    placed = []

    def place(*args):
        placed.append(args)

    # Enter a position via KD oversold buy.
    trader.on_kd(k=10.0, d=15.0, last_px=100.0, now=0.0, place_order=place)
    assert trader.position_qty > 0

    # Attempt bearish crossover without RSI confirmation -> no sell.
    trader.prev_k, trader.prev_d = 85.0, 80.0
    trader.last_rsi = 70.0
    trader.on_kd(k=81.0, d=82.0, last_px=101.0, now=1.0, place_order=place)
    assert placed[-1][1] == "BUY"  # last action still the initial buy
    assert trader.position_qty > 0

    # Now set RSI above 80 and repeat -> expect sell.
    trader.prev_k, trader.prev_d = 85.0, 80.0
    trader.last_rsi = 85.0
    trader.on_kd(k=81.0, d=82.0, last_px=101.0, now=2.0, place_order=place)
    assert placed[-1][1] == "SELL"
    assert trader.position_qty == 0
    assert book.slices_in_use == 0


def test_take_profit_sell_triggers():
    cfg = _cfg()
    cfg["strategy"]["take_profit_pct"] = 0.10
    book = SliceBook(cfg["risk"]["equity"], cfg["slices"]["total"])
    trader = KDTrader("TQQQ", book, cfg)

    placed = []

    def place(*args):
        placed.append(args)

    trader.on_kd(k=10.0, d=15.0, last_px=100.0, now=0.0, place_order=place)
    assert trader.position_qty > 0

    trader.prev_k, trader.prev_d = 50.0, 40.0
    trader.on_kd(k=50.0, d=40.0, last_px=112.0, now=1.0, place_order=place)

    assert placed[-1][1] == "SELL"
    assert trader.position_qty == 0
    assert book.slices_in_use == 0


def test_stop_loss_sell_triggers():
    cfg = _cfg()
    cfg["strategy"]["stop_loss_pct"] = 0.10
    book = SliceBook(cfg["risk"]["equity"], cfg["slices"]["total"])
    trader = KDTrader("SOXL", book, cfg)

    placed = []

    def place(*args):
        placed.append(args)

    trader.on_kd(k=10.0, d=15.0, last_px=100.0, now=0.0, place_order=place)
    assert trader.position_qty > 0

    trader.on_kd(k=30.0, d=25.0, last_px=89.0, now=1.0, place_order=place)
    assert placed[-1][1] == "SELL"
    assert trader.position_qty == 0
    assert book.slices_in_use == 0


def test_rsi_batch_market_then_loc():
    cfg = _cfg()
    book = SliceBook(cfg["risk"]["equity"], cfg["slices"]["total"])
    trader = KDTrader("TQQQ", book, cfg)

    placed = []

    def place(*args):
        placed.append(args)

    # Prime previous price without triggering the batch.
    trader.on_rsi(rsi=60.0, last_px=102.0, now=0.0, place_order=place)

    # Start batch with RSI < 20 (uses per_entry_lt20) and bearish move.
    trader.on_rsi(rsi=18.0, last_px=100.0, now=1.0, place_order=place)
    assert placed[-1][1] == "BUY"
    assert placed[-1][3] == "MKT"
    assert trader.batch_active is True

    # Follow-up call should issue a LOC order at avg_px * multiplier.
    expected_price = trader.avg_px * cfg["strategy"]["rsi_buy_multiplier"]
    trader.on_rsi(rsi=15.0, last_px=99.0, now=2.0, place_order=place)
    assert placed[-1][3] == "LOC"
    assert placed[-1][4] == expected_price


def test_rsi_batch_stops_when_slices_exhausted():
    cfg = _cfg()
    cfg["slices"]["total"] = 2
    cfg["slices"]["per_entry_lt20"] = 1
    cfg["slices"]["per_entry_20_80"] = 1
    book = SliceBook(cfg["risk"]["equity"], cfg["slices"]["total"])
    trader = KDTrader("TQQQ", book, cfg)

    placed = []

    def place(*args):
        placed.append(args)

    trader.on_rsi(rsi=60.0, last_px=101.0, now=0.0, place_order=place)

    trader.on_rsi(rsi=30.0, last_px=100.0, now=1.0, place_order=place)
    trader.on_rsi(rsi=30.0, last_px=99.0, now=2.0, place_order=place)

    prior_orders = len(placed)
    trader.on_rsi(rsi=30.0, last_px=98.0, now=3.0, place_order=place)
    assert len(placed) == prior_orders
    assert trader.batch_active is False
