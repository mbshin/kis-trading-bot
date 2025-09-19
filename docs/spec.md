# KIS US 3x ETF Trading Bot — Spec (v0.7)

**Owner:** Mobum Shin · **Date:** 2025‑09‑19 (KST)

## Objective
Trade **3× US ETFs** via **KIS API** using **dual-signal strategy** (StochRSI K/D + RSI batch buying) with slice-based position management. Features **PostgreSQL** persistence (SQLAlchemy 2 async), JSON logs to **OpenSearch**, **Slack** alerts, comprehensive **backtesting**, **parameter optimization**, and a **CLI** for live trading and analysis.

## Strategy Rules (Dual-Signal Model)

### Entry Signals
**1. RSI Batch Buying (Primary)**
- **Bankroll Management**: Default 60 slices (configurable via `slices.total`); `slice_value = floor(equity / slices.total)`
- **Slice Allocation Rules**:
  - `RSI < rsi_low_band (20)` → consume `slices.per_entry_lt20` slices
  - `rsi_low_band ≤ RSI < rsi_mid_band (80)` → consume `slices.per_entry_20_80` slices
  - `RSI ≥ rsi_mid_band` → no allocation
- **Batch Trigger**: Position is flat, `RSI < rsi_buy_threshold (50)`, and bearish price move (`last_px < prev_px`)
- **Execution Strategy**:
  - **Kick-off**: Market BUY for immediate first allocation
  - **Follow-ups**: LOC orders at `avg_px × rsi_buy_multiplier (1.1)` for continued accumulation
- **Batch Lifecycle**: Continues until position closes or all allocated slices consumed
- **Batch Reset**: Any complete position exit (sell signals, take-profit, stop-loss) ends batch

**2. K/D Stochastic Buying (Configurable)**
- **Toggle**: Controlled by `strategy.enable_kd_buys` (default: true)
- **Oversold Entry**: `K < oversold (20)` → market BUY using `per_entry_lt20` slices
- **Bullish Crossover**: `20 ≤ K < 80` and `prev_K ≤ prev_D` and `K > D` → market BUY using `per_entry_20_80` slices

### Exit Signals
- **Bearish K/D Cross**: `prev_K > prev_D` and `K ≤ D` and `K > overbought (80)` and `RSI > 80` → sell all
- **Take-Profit**: `last_px ≥ avg_px × (1 + take_profit_pct)` → sell all
- **Stop-Loss**: `last_px ≤ avg_px × (1 − stop_loss_pct)` → sell all (optional)

### Risk Controls
- **Trend Filter**: Optional SMA trend gate (`trend_sma_period`); only buy if `last_px > SMA(period)`
- **Cooldown**: Minimum `add_cooldown_sec` between buy orders per symbol
- **Position Limits**: Slice allocation prevents over-leveraging beyond configured equity

## Backtesting Framework

### Data Sources
- **CSV Mode**: `bars: { type: csv, data_dir, column }`
  - Supports daily and intraday data (1h, 4h, etc.)
  - **Yahoo Finance Format**: `Date`, `Close`/`Adj Close` columns
  - **Generic Format**: `timestamp`/`datetime` + `close` columns
  - UTC-aware datetime parsing with configurable date ranges
- **Synthetic Mode**: Fallback generator for testing (5000 ticks, oscillating price)

### Execution Model
- **Fill Simulation**: Market orders filled at bar close price
- **LOC Orders**: Limit-on-Close treated as market fills in backtest
- **PnL Calculation**:
  - **Realized**: Captured on complete position exit
  - **Unrealized**: `(last_px - avg_px) × qty` at period end
- **Position Tracking**: VWAP-based average cost, slice allocation state

### Reporting & Analysis
- **JSON Output**: Run metadata, per-symbol metrics, aggregate totals
- **CSV Export**: Symbol-level rows + `__TOTAL__` summary for spreadsheet analysis
- **CLI Options**: `--out-json reports/backtest.json --out-csv reports/backtest.csv`
- **Metrics**: Realized/unrealized PnL, final position size, slice utilization

### Data Management Tools
- **Fetch Helper**: `make data SYMBOLS="TQQQ,SOXL" FROM=2024-01-01 INTERVAL=1h`
- **Requirements**: Optional `requirements-data.txt` for yfinance dependency

## Optimization & Parameter Tuning

### Grid Search Framework
- **Script**: `scripts/optimize.py` with configurable parameter grids
- **Search Space**:
  - **Core Strategy**: `take_profit_pct`, `stop_loss_pct`, `trend_sma_period`
  - **Stochastic Bands**: `oversold`, `overbought`
  - **RSI Parameters**: `rsi_buy_threshold`, `rsi_buy_multiplier`
  - **Toggle Controls**: `enable_kd_buys` on/off
  - **Position Sizing**: `per_entry_lt20`, `per_entry_20_80`
- **Grid Presets**:
  - **Small Grid**: Focused parameter sweep for quick optimization
  - **Full Grid**: Comprehensive search space (potentially large)
- **Ranking**: Results sorted by realized PnL, top-N display

### Usage Examples
```bash
# Optimize TQQQ parameters on 2024 data
python3 scripts/optimize.py --symbol TQQQ --from 2024-01-01 --to 2025-01-31 --config config.yaml --top 10

# Use intraday data for leveraged ETFs
make data SYMBOLS=SOXL INTERVAL=1h
python3 scripts/optimize.py --symbol SOXL --from 2024-01-01 --config config.yaml
```

## Command Line Interface

### Live Trading
```bash
kisbot run --config config.yaml
```

### Backtesting
```bash
# Basic backtest
kisbot backtest --config config.yaml --from 2024-01-01 --to 2025-01-31 --symbols TQQQ

# Multi-symbol with exports
kisbot backtest --config config.yaml --from 2024-01-01 --to 2025-01-31 --symbols TQQQ,SOXL \
  --out-json reports/backtest.json --out-csv reports/backtest.csv
```

### Development Workflow
```bash
# Setup development environment
make dev

# Run test suite
make test

# Quick backtest via Makefile
make backtest FROM=2024-01-01 TO=2025-01-31 SYMBOLS=TQQQ

# Fetch data and optimize
make data SYMBOLS="TQQQ,SOXL" INTERVAL=1h
make optimize SYMBOLS=TQQQ FROM=2024-01-01
```

## Architecture & Code Organization

### Core Components (`src/kisbot/core/`)
- **`indicators.py`**: WilderRSI, StochRSI, RollingSMA implementations
- **`slices.py`**: SliceBook for position management and bankroll allocation
- **`signals.py`**: KDTrader with dual-signal strategy logic

### Services Layer (`src/kisbot/services/`)
- **`trader.py`**: Main bot orchestration, symbol configuration merging
- **`executor.py`**: Order execution interface for live trading

### Infrastructure (`src/kisbot/infra/`)
- **`backtest.py`**: Historical simulation engine with CSV data loading
- **`ws_client.py`**: WebSocket client for real-time price feeds
- **`rest_client.py`**: REST API client for KIS broker integration
- **`slack.py`**: Alert notification system
- **`logger.py`**: Structured logging framework

### Data Persistence (`src/kisbot/db/`)
- **`models.py`**: SQLAlchemy 2.0 async models for signals and trades
- **`crud.py`**: Database operations with async session management
- **`base.py`**: Database engine and session factory
- **Migration**: Alembic configuration in `alembic/` directory

## Configuration Management

### Hierarchical Config Structure
- **Global Defaults**: Base strategy, slices, and risk parameters
- **Per-Symbol Overrides**: `symbols.<SYMBOL>` section overrides globals
- **Merge Strategy**: Deep merge with symbol-specific taking precedence

### Key Configuration Sections

#### Strategy Parameters
```yaml
strategy:
  # Technical indicators
  rsi_period: 14
  stoch_period: 14
  k_period: 3
  d_period: 3

  # Trading bands
  overbought: 80
  oversold: 20

  # RSI batch buying
  rsi_buy_threshold: 50      # Entry trigger
  rsi_buy_multiplier: 1.1    # LOC price multiplier
  enable_kd_buys: true       # Toggle K/D entries

  # Risk management
  take_profit_pct: 0.11      # 11% take profit
  stop_loss_pct: 0.10        # 10% stop loss (optional)
  trend_sma_period: 100      # Trend filter (0 = disabled)
  add_cooldown_sec: 60       # Order cooldown
```

#### Position Sizing
```yaml
slices:
  total: 60                  # Total slice count
  per_entry_lt20: 2          # Slices for RSI < 20
  per_entry_20_80: 2         # Slices for 20 ≤ RSI < 80

risk:
  equity: 100000             # Total capital allocation
```

#### Symbol-Specific Overrides
```yaml
symbols:
  TQQQ:
    strategy: { take_profit_pct: 0.11, oversold: 20, overbought: 80 }
    slices: { per_entry_lt20: 2, per_entry_20_80: 2 }
    risk: { equity: 100000 }

  SOXL:
    strategy: { take_profit_pct: 0.14, stop_loss_pct: 0.10, trend_sma_period: 100 }
    slices: { per_entry_lt20: 2, per_entry_20_80: 1 }
    risk: { equity: 40000 }
```

## Testing & Quality Assurance

### Test Coverage
- **Unit Tests**: Core indicators, slice management, signal logic (`tests/`)
- **Test Framework**: pytest with fixtures and parameterized tests
- **Key Test Areas**:
  - StochRSI indicator accuracy and warmup behavior
  - KDTrader entry/exit logic with various market conditions
  - RSI batch buying lifecycle and slice allocation
  - Take-profit and stop-loss trigger conditions

### Quality Tools
- **Linting**: Optional ruff/black integration
- **Type Checking**: Python 3.10+ type hints throughout codebase
- **Development Setup**: `make dev` installs all dependencies

### Testing Commands
```bash
# Run full test suite
make test

# Run specific test module
python3 -m pytest tests/test_signals.py -v

# Run with coverage
python3 -m pytest --cov=src/kisbot tests/
```

## Deployment & Operations

### Environment Setup
- **Python**: 3.10+ required
- **Database**: PostgreSQL with asyncpg driver
- **Dependencies**: Core requirements in `requirements.txt`
- **Optional**: Data fetching tools in `requirements-data.txt`

### Database Migration
```bash
# Initialize database
createdb kisbot
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### Monitoring & Alerts
- **Slack Integration**: Trade notifications and system alerts
- **Structured Logging**: JSON format compatible with OpenSearch
- **Health Checks**: WebSocket connection monitoring
- **Error Handling**: Graceful degradation on API failures
