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
kisbot backtest --config config.yaml --from 2024-01-01 --to 2025-01-31 --symbols TQQQ
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
