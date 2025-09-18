# KIS US 3x ETF Trading Bot — Minimal Spec (v0.3, ORM)

**Owner:** Mobum Shin · **Date:** 2025‑09‑18 (KST)

## Objective
Trade **3× US ETFs** via **KIS API** using **StochRSI K/D** and a **60‑slice bankroll**. Persist to **PostgreSQL** via **SQLAlchemy 2.0 (async + asyncpg)**; ship JSON logs to **OpenSearch**; send **Slack** alerts; provide a **backtesting** CLI.

## Strategy Rules (Slice Model)
- **Bankroll:** 60 slices; `slice_value = floor(equity/60)`.
- **Buy:** K<20 → BUY 4 slices; 20≤K<80 and **K↑D** → BUY 1 slice; K≥80 → no buys.
- **Sell:** **K↓D** and **K>80** → SELL ALL.
- Safeguards: add_cooldown_sec (45s), never exceed 60 slices; optional ATR stop.
