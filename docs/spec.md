# KIS US 3x ETF Trading Bot — Spec (v0.6)

**Owner:** Mobum Shin · **Date:** 2025‑09‑18 (KST)

## Objective
Trade **3× US ETFs** via **KIS API** using **StochRSI K/D** and a slice-based bankroll (default 60 slices, configurable). Persist to **PostgreSQL** (SQLAlchemy 2 async), JSON logs to **OpenSearch**, **Slack** alerts, and a **CLI** for live run and historical backtests.

## Strategy Rules (Slice Model)
- Buy — RSI batch (always enabled):
  - Bankroll sizing: default 60 slices (configurable via `slices.total`); `slice_value = floor(equity / slices.total)`.
  - Slice allocation inside the batch:
    - `RSI < 20` → consume `slices.per_entry_lt20` slices.
    - `20 ≤ RSI < 80` → consume `slices.per_entry_20_80` slices.
  - Batch trigger: bot is flat, `RSI < rsi_buy_threshold`, and the latest close is bearish vs the prior close (`last_px < prev_px`).
  - Kick-off order: place a market BUY so the first allocation executes immediately.
  - Follow-up orders: continue buying using LOC priced at `avg_px × rsi_buy_multiplier`; `avg_px` is the current volume-weighted average entry price.
  - Batch lifetime: keep allocating slices without re-checking RSI until either all configured slices are committed or a SELL clears the position.
  - Batch reset: any SELL that flattens the position (KD sell, take-profit, stop-loss) or exhausting all slices ends the batch and frees the bankroll.

- Sell:
  - K↓D and K > overbought and `RSI > 80` → sell all
  - Take-Profit: sell all if `last_px ≥ avg_px × (1 + take_profit_pct)`
  - Stop-Loss: sell all if `last_px ≤ avg_px × (1 − stop_loss_pct)`

## Backtesting
- Data: synthetic or CSV (`bars: { type: csv, data_dir, column }`); supports daily and intraday (e.g., 1h) bars.
- Loader: Yahoo CSV (`Date` + `Close`/`Adj Close`) or generic (`timestamp` + `close`), UTC-safe parsing.
- PnL: realized on close; end-of-period unrealized = `(last_px - avg_px) × qty`.
- Reports: aggregate totals; CLI supports `--out-json` and `--out-csv`.
- Helpers: `make data` (yfinance), `make backtest`, `scripts/optimize.py` (sweeps TP/SL/bands/slices).

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
- Example: TQQQ uses TP 0.11 with bands 20/80; SOXL uses TP 0.14, SL 0.10, bands 20/85.
- Optional RSI buy keys under `strategy`:
  - `rsi_buy_threshold` (default 50): trigger threshold for RSI buy
  - `rsi_buy_multiplier` (default 1.1): limit price multiplier applied to `base_px`

## Testing & Tooling
- Tests: `pytest` (`tests/`), `make test`
- Dev: `make dev` (installs deps), formatting/lint optional (`black`, `ruff`)
