import streamlit as st
import pandas as pd
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.interface import dashboard_connector

st.set_page_config(page_title="The Matrix Cockpit", layout="wide")

st.title("The Matrix: Simulation Cockpit (Phase 20.5)")

# --- Sidebar: Control Panel ---
st.sidebar.header("God Mode Controls")

# --- Session State Management ---
if 'simulation' not in st.session_state:
    st.sidebar.info("Initializing Interface...")
    try:
        st.session_state['simulation'] = dashboard_connector.get_engine_instance()
        st.session_state['tick'] = 0
        st.sidebar.success("Engine Connected")
    except Exception as e:
        st.sidebar.error(f"Failed to initialize engine: {e}")
        st.stop()

simulation = st.session_state['simulation']

# Get current config values
current_tech_level = getattr(simulation.config_module, 'FORMULA_TECH_LEVEL', 0.0)
current_wealth_tax = getattr(simulation.config_module, 'ANNUAL_WEALTH_TAX_RATE', 0.0)

# Sliders
new_tech_level = st.sidebar.slider(
    "Formula Tech Level",
    min_value=0.0,
    max_value=1.0,
    value=float(current_tech_level),
    step=0.1
)

new_wealth_tax = st.sidebar.slider(
    "Annual Wealth Tax Rate",
    min_value=0.0,
    max_value=0.1,
    value=float(current_wealth_tax),
    step=0.005,
    format="%.3f"
)

if st.sidebar.button("Apply Parameters"):
    params = {
        "FORMULA_TECH_LEVEL": new_tech_level,
        "ANNUAL_WEALTH_TAX_RATE": new_wealth_tax
    }
    dashboard_connector.update_params(simulation, params)
    st.sidebar.success("Parameters Updated!")

# --- Session State Management (Continued) ---
st.sidebar.success(f"Engine Connected (Tick {st.session_state['tick']})")

# --- Main Area: Metrics ---
st.subheader("Live Monitor")

# Fetch Metrics
metrics = dashboard_connector.get_metrics(simulation)

# Display Metrics using Columns
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Tick", metrics['tick'])
col2.metric("Population", metrics['total_population'])
col3.metric("GDP", f"{metrics['gdp']:.2f}")
col4.metric("Avg Assets", f"{metrics['average_assets']:.2f}")
col5.metric("Unemployment", f"{metrics['unemployment_rate']:.1f}%")

# --- Control Area ---
st.markdown("---")
if st.button("Run 1 Tick"):
    with st.spinner("Running Tick..."):
        new_tick = dashboard_connector.run_tick(simulation)
        st.session_state['tick'] = new_tick
        st.rerun()

# --- Debug Info ---
if st.checkbox("Show Raw Metrics"):
    st.json(metrics)
