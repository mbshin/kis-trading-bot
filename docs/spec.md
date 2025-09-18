# KIS US 3x ETF Trading Bot — Spec (v0.5)

**Owner:** Mobum Shin · **Date:** 2025‑09‑18 (KST)

## Objective
Trade **3× US ETFs** via **KIS API** using **StochRSI K/D** and a **60‑slice bankroll**. Persist to **PostgreSQL** (SQLAlchemy 2 async), JSON logs to **OpenSearch**, **Slack** alerts, and a **CLI** for live run and historical backtests.

## Strategy Rules (Slice Model)
- Bankroll: 60 slices; `slice_value = floor(equity/60)` (config: `risk.equity`, `slices.total`).
- Buy:
  - K < oversold → buy `slices.per_entry_lt20`
  - oversold ≤ K < overbought and K↑D → buy `slices.per_entry_20_80`
  - Optional trend filter: only buy if `last_px > SMA(trend_sma_period)`
- Sell:
  - K↓D and K > overbought → sell all
  - Take‑Profit: sell all if `last_px ≥ avg_px × (1 + take_profit_pct)`
  - Stop‑Loss: sell all if `last_px ≤ avg_px × (1 − stop_loss_pct)`
- Safeguards: `add_cooldown_sec` (default 45s), cap at total slices.

## Backtesting
- Data: synthetic or CSV (`bars: { type: csv, data_dir, column }`); supports daily and intraday (e.g., 1h) bars.
- Loader: Yahoo CSV (`Date` + `Close`/`Adj Close`) or generic (`timestamp` + `close`), UTC-safe parsing.
- PnL: realized on close; end-of-period unrealized = `(last_px - avg_px) × qty`.
- Reports: aggregate totals; CLI supports `--out-json` and `--out-csv`.
- Helpers: `make data` (yfinance), `make backtest`, `scripts/optimize.py` (sweeps TP/SL/trend/bands/cooldown/slices).

## CLI
- `kisbot run --config config.yaml`
- `kisbot backtest --config config.yaml --from YYYY-MM-DD --to YYYY-MM-DD --symbols TQQQ,SOXL`

## Code Layout
- `src/kisbot/core`: indicators (WilderRSI, StochRSI), slice model, trader (KDTrader)
- `src/kisbot/services`: executor, orchestration
- `src/kisbot/infra`: backtest, logger, ws/rest, slack
- `src/kisbot/db`: async engine/session, models, CRUD; Alembic in `alembic/`

## Configuration
- Global config with per‑symbol overrides under `symbols.<SYMBOL>` for `strategy`, `slices`, and `risk`.
- Example: TQQQ uses TP 0.11 with bands 20/80; SOXL uses TP 0.14, SL 0.10, trend SMA 100, bands 20/85.

## Testing & Tooling
- Tests: `pytest` (`tests/`), `make test`
- Dev: `make dev` (installs deps), formatting/lint optional (`black`, `ruff`)
