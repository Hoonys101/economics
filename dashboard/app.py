# 1. Imports
import streamlit as st
import pandas as pd
from modules.analytics.loader import DataLoader
# CRITICAL: No other imports from `simulation`, `modules.finance`, etc. are allowed.

# 2. Initialization
st.set_page_config(layout="wide")
st.title("WO-037: Simulation Cockpit")
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
    if (
        "gdp_real" in economic_indicators_df.columns
        and "gdp_nominal" in economic_indicators_df.columns
    ):
        st.line_chart(economic_indicators_df[["gdp_real", "gdp_nominal"]])
    else:
        st.warning("GDP data not available.")

    # Chart 2: Inflation (CPI)
    st.subheader("Inflation (CPI)")
    if "cpi" in economic_indicators_df.columns:
        st.line_chart(economic_indicators_df["cpi"])
    else:
        st.warning("CPI data not available.")

    # Chart 3: Population
    st.subheader("Population")
    if "population" in economic_indicators_df.columns:
        st.line_chart(economic_indicators_df["population"])
    else:
        st.warning("Population data not available.")

    # Chart 4: Gini Coefficient
    st.subheader("Gini Coefficient")
    if "gini_coefficient" in economic_indicators_df.columns:
        st.line_chart(economic_indicators_df["gini_coefficient"])
    else:
        st.warning("Gini Coefficient data not available.")

    # Raw Data Viewer
    with st.expander("View Raw Economic Indicators Data"):
        st.dataframe(economic_indicators_df)
