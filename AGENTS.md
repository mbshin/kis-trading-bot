# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/kisbot/`
  - `core/` indicators, slice model, and signal logic
  - `services/` orchestration (trader, executor)
  - `infra/` integrations (WS/REST, Slack, logging, backtest)
  - `db/` SQLAlchemy async setup, models, CRUD
- Migrations: `alembic/` (uses `PG_DSN` env var)
- Config: `config.yaml`
- Docs: `docs/`

## Build, Test, and Development Commands
- Install deps: `uv sync` (or `pip install -r requirements.txt`)
- Editable install: `pip install -e .`
- DB setup:
  - `createdb kisbot`
  - `alembic revision --autogenerate -m "init"`
  - `alembic upgrade head`
- Run bot: `kisbot run --config config.yaml`
- Backtest: `kisbot backtest --config config.yaml --from 2024-01-01 --to 2025-01-31 --symbols TQQQ`

## Coding Style & Naming Conventions
- Python 3.10+, 4‑space indent, type hints required for public functions.
- Naming: modules `snake_case.py`, functions/vars `snake_case`, classes `PascalCase`.
- Keep side effects in `services/` and integrations in `infra/`; strategy math stays in `core/`.
- Logging: use `kisbot.infra.logger.log(event, **fields)` for structured JSON.
- Optional tools: format with `black`, lint with `ruff` before PRs.

## Testing Guidelines
- Framework: prefer `pytest` under `tests/` mirroring `src/kisbot/...` structure.
- Name tests `test_*.py`; aim to cover core strategy and slice logic.
- Quick run examples:
  - `pytest -q` (all tests)
  - `pytest -k stoch` (subset)

## Commit & Pull Request Guidelines
- Commits: use clear, atomic messages. Recommended Conventional Commits, e.g. `feat(core): add StochRSI` or `fix(db): correct async session use`.
- PRs must include:
  - Purpose summary and scope
  - Linked issue (if any)
  - How to run or reproduce (commands)
  - Screenshots/log snippets for relevant runs (e.g., `order.submit` events)

## Security & Configuration Tips
- Do not commit secrets (e.g., Slack webhook). Use env vars and reference them in `config.yaml` or runtime.
- Database: set `PG_DSN` for Alembic; app uses `postgres.dsn` from `config.yaml`.
- Modes: `mode: paper` vs live; ensure correct mode before placing orders.
- Observability: set `opensearch.index_prefix` and rely on JSON logs emitted to stdout for shipping.

