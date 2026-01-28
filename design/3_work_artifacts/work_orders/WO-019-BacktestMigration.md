# WO-019: Phase 11 Backtest Engine Migration & Visualization

## 1. Objective
Build the **Backtest Analytics Pipeline** to transform raw SQLite simulation data into actionable economic insights (Charts/Metrics). This empowers the Architect to verify long-term stability and macroeconomic trends.

## 2. Background
- **Source**: `simulation_data.db` (SQLite) is already populated by `SimulationRepository`.
- **Gap**: We have data, but no way to visualize it efficiently. Text logs are insufficient for 1000-tick runs.
- **Goal**: Implement a `Loader` (ETL) and a `Visualizer` (Dashboard).

## 3. Tasks for Jules

### 3.1 Data Generation (Long Run)
- [ ] **Action**: Run `python scripts/iron_test.py --num_ticks 1000`
    - *Note*: This will take time. Ensure it finishes successfully.
    - *Outcome*: A populated `simulation_data.db` file (size should be several MBs).

### 3.2 Analytics Loader (`modules/analytics/loader.py`)
- [ ] **Create Module**: `modules/analytics/` package.
- [ ] **Implement `DataLoader` class**:
    - **Dependency**: `pandas`, `sqlite3`.
    - **Methods**:
        - `load_economic_indicators(run_id=latest) -> pd.DataFrame`
        - `load_agent_states(run_id=latest) -> pd.DataFrame`
        - `load_market_history(run_id=latest, market_id="goods_market") -> pd.DataFrame`
    - **Features**: Convert `time` column to index if useful. Handle data types.

### 3.3 Visualization Script (`scripts/visualize_economy.py`)
- [ ] **Create Script**: `scripts/visualize_economy.py`.
- [ ] **Dependency**: `matplotlib` or `seaborn`.
- [ ] **Charts to Generate** (Save to `reports/figures/`):
    1.  **`macro_overview.png`**:
        - Subplot 1: Total Money Supply (Line)
        - Subplot 2: GDP (Total Production) (Line)
        - Subplot 3: Average Goods Price (Line)
    2.  **`inequality_gini.png`**:
        - Calculate GINI coefficient from `agent_states` (Assets) per tick.
        - Plot GINI over time.
    3.  **`fiscal_status.png`**:
        - Government Assets vs Total Debt (Line).
        - Tax Revenue vs Welfare Spending (Stacked Bar or Multi-line).
- [ ] **Console Report**: Print key stats at the end (e.g., "Final GINI: 0.35").

## 4. Technical Constraints
- **Language**: Python 3.9+
- **Libraries**: `pandas`, `matplotlib`, `sqlite3`.
- **Database**: Use `simulation/db/database.py` to get connection or connect directly if easier for pandas (`pd.read_sql`).

## 5. Verification
- Run `python scripts/visualize_economy.py`
- Check `reports/figures/` for the images.
- Images should show meaningful trends (not empty or flat lines).
