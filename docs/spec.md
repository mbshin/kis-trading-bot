# KIS US 3x ETF Trading Bot — Spec (v0.4)

**Owner:** Mobum Shin · **Date:** 2025‑09‑18 (KST)

## Objective
Trade **3× US ETFs** via **KIS API** using **StochRSI K/D** and a **60‑slice bankroll**. Persist to **PostgreSQL** (SQLAlchemy 2 async), JSON logs to **OpenSearch**, **Slack** alerts, and a **CLI** for live run and historical backtests.

## Strategy Rules (Slice Model)
- Bankroll: 60 slices; `slice_value = floor(equity/60)` (config: `risk.equity`, `slices.total`).
- Buy:
  - K < oversold (default 20) → buy `slices.per_entry_lt20` (default 2)
  - oversold ≤ K < overbought (default 80) and K↑D → buy `slices.per_entry_20_80` (default 2)
  - K ≥ overbought → no buys
- Sell:
  - K↓D and K > overbought → sell all (take profit/exit)
  - Take‑Profit: sell all if `last_px ≥ avg_px × (1 + take_profit_pct)` (default 0.11)
- Safeguards: `add_cooldown_sec` (default 45s), never exceed total slices.

## Backtesting
- Modes: synthetic ticks (no data) or CSV bars (`bars: { type: csv, data_dir, column }`).
- Loader: accepts Yahoo‐style CSV with `Date` + `Close`/`Adj Close` or generic `timestamp` + `close`.
- PnL: realized on position close; unrealized at end as `(last_px - avg_px) × qty`.
- Helpers: `make data` (yfinance fetch), `make backtest`, `scripts/optimize.py` (grid search key params).

## CLI
- `kisbot run --config config.yaml`
- `kisbot backtest --config config.yaml --from YYYY-MM-DD --to YYYY-MM-DD --symbols TQQQ,SOXL`

## Code Layout
- `src/kisbot/core`: indicators (WilderRSI, StochRSI), slice model, trader (KDTrader)
- `src/kisbot/services`: executor, orchestration
- `src/kisbot/infra`: backtest, logger, ws/rest, slack
- `src/kisbot/db`: async engine/session, models, CRUD; Alembic in `alembic/`

## Testing & Tooling
- Tests: `pytest` (`tests/`), `make test`
- Dev: `make dev` (installs deps), formatting/lint optional (`black`, `ruff`)
