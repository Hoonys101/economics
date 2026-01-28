# Phase 11: Backtest Engine Migration & Visualization Plan

## 1. Goal
Migrate the project's analysis capability from text-based log scraping to a robust **Database-Driven Backtesting Engine**. We will verify the economy's stability over a long run (1000 ticks) and visualize key macroeconomic indicators.

## 2. Rationale
Currently, we rely on `iron_test.py` logs and `PHASE1_FINAL_REPORT.md` for snapshots. As the simulation grows (1000+ ticks), text logs become unmanageable. We need to leverage the existing SQLite storage (`simulation_data.db`) to enable:
- Quantitative Analysis (Pandas/Backtrader)
- Time-Series Visualization (Matplotlib)
- Deep Dive into inequality (Gini) and structural issues.

## 3. Implementation Steps

### 3.1 Data Generation (Long Run)
- **Script**: `scripts/iron_test.py`
- **Action**: Run for **1000 ticks**.
- **Output**: Populated `simulation_data.db` with `run_id` for this session.

### 3.2 Analytics Module (Migration Layer)
- **New Module**: `modules/analytics/loader.py`
- **Responsibilities**:
    - Connect to `simulation_data.db`.
    - `load_indicators(run_id) -> pd.DataFrame`: Load GDP, Inflation, etc.
    - `load_agent_states(run_id) -> pd.DataFrame`: Load Gini constituents.
    - `load_market_history(run_id) -> pd.DataFrame`: Load price/volume data.

### 3.3 Visualization Engine
- **New Script**: `scripts/visualize_economy.py`
- **Charts to Generate**:
    1.  **Macro Overview**: GDP, Total Money Supply, Inflation Rate (multi-plot).
    2.  **Inequality**: Gini Coefficient over time (calculated from Agent States).
    3.  **Fiscal Health**: Government Debt vs Approval Rating.
    4.  **Market Dynamics**: Price/Volume trends for "basic_food" and "luxury_food".
- **Output**: Save PNGs to `reports/figures/`.

## 4. Verification Plan
1.  **DB Check**: Run `scripts/iron_test.py` (100 ticks trial for quick verify, then 1000). Check DB file size increases.
2.  **Loader Test**: Create `tests/test_analytics_loader.py` to verify DataFrame shapes and column types.
3.  **Vis Test**: Run `scripts/visualize_economy.py` and inspect generated PNG files in `reports/figures/`.

## 5. User Review Required
- **Libraries**: Need `pandas` and `matplotlib`. Confirmation needed if these are installed (standard data stack).
- **Execution Time**: 1000 ticks may take ~15-20 minutes.
