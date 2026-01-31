# Work Order Specification: Simulation Cockpit

**Phase:** 20.5
**Priority:** HIGH
**Prerequisite:** None

---

## 1. Overview & Core Principles

### 1.1. Objective
To create a read-only Streamlit dashboard (`dashboard/app.py`) for visualizing key macroeconomic indicators from simulation runs. This tool will serve as a passive "Simulation Cockpit" for observability.

### 1.2. Core Architectural Principles
- **Strict Read-Only (Observer Pattern):** The dashboard MUST NOT have any capability to write or modify the simulation's state. It is a pure data consumer.
- **Data Access Layer Enforcement:** All data MUST be fetched exclusively through the `modules.analytics.loader.DataLoader` class. Direct database connections or imports from the core simulation engine are strictly forbidden.
- **Separation of Concerns (SoC):** The dashboard's responsibility is limited to data presentation. Data loading and processing logic are delegated to the `analytics` module.

---

## 2. Interface & API (The Contract)

### 2.1. UI Layout (`dashboard/app.py`)
The application will have a simple layout:
1. **Main Title:** "Simulation Cockpit"
2. **Run Selector:** A Streamlit text input `st.text_input` allowing the user to specify a `run_id`. It should default to `"latest"`.
3. **Data Display:** A series of charts visualizing the metrics for the selected run.

### 2.2. Data Access Contract
The application MUST use the following pre-approved method from the `DataLoader` class:
- `DataLoader.load_economic_indicators(run_id: Optional[int] = None) -> pd.DataFrame`

---

## 3. Logic & Algorithm (Pseudo-code)

This pseudo-code outlines the implementation for `dashboard/app.py`.

```python
# 1. Imports
import streamlit as st
import pandas as pd
from modules.analytics.loader import DataLoader
# CRITICAL: No other imports from `simulation`, `modules.finance`, etc. are allowed.

# 2. Initialization
st.set_page_config(layout="wide")
st.title("Simulation Cockpit")
st.markdown("A read-only dashboard for observing simulation outcomes.")

data_loader = DataLoader(db_path="simulation_data.db")

# 3. User Input for Run ID
run_id_input = st.text_input("Enter Simulation Run ID", value="latest")

# 4. Data Loading
try:
 # Use the validated run_id for loading. The loader handles the 'latest' keyword.
 economic_indicators_df = data_loader.load_economic_indicators(run_id=run_id_input)
except Exception as e:
 st.error(f"Failed to load data for run '{run_id_input}'. Error: {e}")
 st.stop()


# 5. Data Validation and Display
if economic_indicators_df is None or economic_indicators_df.empty:
 st.warning(f"No economic indicator data found for Run ID: '{run_id_input}'.")
else:
 st.success(f"Displaying data for Run ID: '{run_id_input}'")

 # 6. Visualization
 st.header("Key Economic Indicators")

 # Chart 1: GDP
 st.subheader("GDP (Real vs. Nominal)")
 if 'gdp_real' in economic_indicators_df.columns and 'gdp_nominal' in economic_indicators_df.columns:
 st.line_chart(economic_indicators_df[['gdp_real', 'gdp_nominal']])
 else:
 st.warning("GDP data not available.")

 # Chart 2: Inflation (CPI)
 st.subheader("Inflation (CPI)")
 if 'cpi' in economic_indicators_df.columns:
 st.line_chart(economic_indicators_df['cpi'])
 else:
 st.warning("CPI data not available.")

 # Chart 3: Population
 st.subheader("Population")
 if 'population' in economic_indicators_df.columns:
 st.line_chart(economic_indicators_df['population'])
 else:
 st.warning("Population data not available.")

 # Chart 4: Gini Coefficient
 st.subheader("Gini Coefficient")
 if 'gini_coefficient' in economic_indicators_df.columns:
 st.line_chart(economic_indicators_df['gini_coefficient'])
 else:
 st.warning("Gini Coefficient data not available.")

 # Raw Data Viewer
 with st.expander("View Raw Economic Indicators Data"):
 st.dataframe(economic_indicators_df)

```

---

## 4. Architectural Constraints & Prohibitions

This section is critical and non-negotiable.

### 4.1. Forbidden Imports
To enforce the read-only boundary, `dashboard/app.py` is **PROHIBITED** from importing any of the following:
- `simulation.*`
- `modules.finance.*`
- `modules.core.*`
- `main`
- `config` (to prevent state modification)
- Any other module that is part of the core simulation logic.

The **ONLY** permitted local module import for data access is `from modules.analytics.loader import DataLoader`.

### 4.2. Out-of-Scope Data Sources
Based on the pre-flight audit, the following data sources are explicitly out of scope for this Work Order to avoid schema instability risks:
- **`market_history` table:** Do not implement features that rely on `DataLoader.load_market_history`.
- **`fiscal_history.json` file:** Do not implement features that rely on `DataLoader.load_fiscal_history`.

---

## 5. Verification Plan

### 5.1. Execution
The dashboard can be run locally using the following command:
```bash
streamlit run dashboard/app.py
```

### 5.2. Success Criteria
1. **No Errors on Launch:** The application starts without any import errors or runtime exceptions.
2. **UI Renders Correctly:** The title, description, and run ID input box are visible.
3. **Default Load:** On initial load, the dashboard correctly fetches and displays charts for the "latest" run.
4. **Specific Run Load:** Entering a valid, existing `run_id` into the text box and pressing Enter updates the charts with the data for that specific run.
5. **Graceful Failure:** Entering an invalid or non-existent `run_id` displays the "No data found" warning message without crashing the application.
6. **Chart Verification:** The four specified charts (GDP, CPI, Population, Gini) are rendered correctly. If a column is missing from the data, a warning is shown for that chart.

---

## 6. [ROUTINE] Mandatory Reporting

As part of the implementation of this work order, the assigned developer (Jules) is required to document any findings.

1. **Technical Insights & Suggestions:** If any potential improvements, bugs, or notable discoveries are made regarding the `DataLoader` or the data schema during implementation, report them in the `communications/insights/` directory.
2. **Technical Debt:** If any shortcuts or temporary solutions are implemented, log them as a new entry in `design/TECH_DEBT_LEDGER.md`.
