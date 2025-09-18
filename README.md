# KIS Trading Bot (StochRSI K/D, slices)

## Quickstart
```bash
# 1) install deps
uv sync  # or: pip install -r requirements.txt

# 2) set DB
createdb kisbot
alembic revision --autogenerate -m "init"
alembic upgrade head

# 3) run
kisbot run --config config.yaml

# 4) backtest
kisbot backtest --config config.yaml --from 2024-01-01 --to 2025-01-31 --symbols TQQQ
```

## Developer
```bash
# Install runtime + dev deps, editable package
make dev

# Run tests
make test

# Backtest via Makefile
make backtest FROM=2024-01-01 TO=2025-01-31 SYMBOLS=TQQQ
```

## Historical Backtest (CSV)
- Configure `bars` in `config.yaml`:
```yaml
bars:
  type: csv
  data_dir: data
  column: close   # or adj_close
```
- Place per‑symbol CSVs under `data/`, e.g. `data/TQQQ.csv`.
  Accepted columns (case-insensitive):
  - Generic: `timestamp` or `datetime` and `close`
  - Yahoo format: `Date`, `Close` (or `Adj Close` when column=adj_close)
- Run:
```bash
kisbot backtest --config config.yaml --from 2024-01-01 --to 2025-01-31 --symbols TQQQ,SOXL \
  --out-json reports/backtest.json --out-csv reports/backtest.csv
```
The backtest reports realized/unrealized PnL per symbol using a simple fill model (market at close price per row).

### Fetching CSVs (optional helper)
```bash
# Install data helper dependency
pip install -r requirements-data.txt

# Download OHLCV from Yahoo Finance into data/
make data SYMBOLS="TQQQ,SPXL" FROM=2024-01-01 TO=2025-01-31 INTERVAL=1d

# Then run the backtest with bars.type=csv
make backtest FROM=2024-01-01 TO=2025-01-31 SYMBOLS=TQQQ
```

## Strategy Parameters
- Key fields under `strategy` in `config.yaml`:
  - `rsi_period`, `stoch_period`, `k_period`, `d_period`, `overbought`, `oversold`
  - `add_cooldown_sec`: minimum seconds between buys per symbol
  - `take_profit_pct`: sell all when `last_px >= avg_px * (1 + pct)` (default 0.11)
  - `stop_loss_pct`: sell all when `last_px <= avg_px * (1 - pct)` (optional)
  - `trend_sma_period`: only buy if `last_px > SMA(period)`; disable with `0`
  - `enable_kd_buys`: toggle K/D-based buys (default: true)

### RSI Buy (optional)
- If enabled via config, an additional RSI-based buy path is available:
  - Entry when flat: if `RSI < rsi_buy_threshold`, place a buy using LOC (Limit-On-Close).
  - While in position: continue placing a daily LOC buy (subject to `add_cooldown_sec` and slices) until the position fully exits by sell/stop-loss.
  - Price: LOC limit set to `base_px * rsi_buy_multiplier`, where `base_px = avg_px` if in position else `last_px`.
  - Sizing: uses `slices.per_entry_20_80` for notional.
- Config keys under `strategy`:
  - `rsi_buy_threshold` (default 50)
  - `rsi_buy_multiplier` (default 1.1)
  - Example (defaults shown commented in config.yaml):
    ```yaml
    strategy:
      # rsi_buy_threshold: 50
      # rsi_buy_multiplier: 1.1
      # enable_kd_buys: true
    ```
 - Per‑symbol overrides supported under `symbols.<SYMBOL>`, merged onto globals. Example:
   ```yaml
   symbols:
     TQQQ:
       strategy: { take_profit_pct: 0.11, oversold: 20, overbought: 80 }
       slices:   { per_entry_lt20: 2, per_entry_20_80: 2 }
       risk:     { equity: 100000 }
     SOXL:
       strategy: { take_profit_pct: 0.14, stop_loss_pct: 0.10, trend_sma_period: 100, oversold: 20, overbought: 85 }
       slices:   { per_entry_lt20: 2, per_entry_20_80: 1 }
       risk:     { equity: 40000 }
   ```
  - Risk can be weighted per symbol via `symbols.<SYMBOL>.risk.equity`.

## Aggregated Reports
- The backtest CLI can emit both JSON and CSV:
  - `--out-json reports/backtest.json` writes run_id, per-symbol metrics, and aggregate totals.
  - `--out-csv reports/backtest.csv` writes rows per symbol and a `__TOTAL__` summary line.

## Optimization
- Script: `python3 scripts/optimize.py --symbol TQQQ --from YYYY-MM-DD --to YYYY-MM-DD --config config.yaml`
- Sweeps key params and ranks by realized PnL. The default "small" grid includes:
  - `take_profit_pct`, `stop_loss_pct`, `trend_sma_period`
  - RSI params: `rsi_buy_threshold`, `rsi_buy_multiplier`
  - `enable_kd_buys` toggle
  - You can expand to a broader grid in the script if needed.
- Tip: Use intraday data (e.g., `INTERVAL=1h`) for leveraged tickers like SOXL.

## Recent Changes
- Added optional RSI buy flow with once-per-UTC-day LOC orders and continued daily buys while in position.
- Introduced `strategy.enable_kd_buys` to toggle K/D-based entries.
- Extended optimizer to search RSI parameters and KD toggle.
