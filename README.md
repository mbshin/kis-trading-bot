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
