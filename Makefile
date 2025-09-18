.PHONY: install dev test run backtest data

PY := python3
PIP := pip3
CONFIG ?= config.yaml
FROM ?= 2024-01-01
TO ?= 2025-01-31
SYMBOLS ?= TQQQ
INTERVAL ?= 1d

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

dev:
	$(PIP) install -r requirements.txt -r requirements-dev.txt
	$(PIP) install -e .

test:
	$(PY) -m pytest

run:
	kisbot run --config $(CONFIG)

backtest:
	kisbot backtest --config $(CONFIG) --from $(FROM) --to $(TO) --symbols $(SYMBOLS)

data:
	# Install data dependency if needed
	$(PIP) install -r requirements-data.txt || true
	$(PY) scripts/fetch_data.py --symbols "$(SYMBOLS)" --from "$(FROM)" --to "$(TO)" --interval "$(INTERVAL)" --out data

optimize:
	$(PY) scripts/optimize.py --symbol $(SYMBOLS) --from $(FROM) --to $(TO) --config $(CONFIG)
