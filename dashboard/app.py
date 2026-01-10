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

        # Initialize history with Tick 0 metrics
        initial_metrics = dashboard_connector.get_metrics(st.session_state['simulation'])
        st.session_state['history'] = [initial_metrics]

        st.sidebar.success("Engine Connected")
    except Exception as e:
        st.sidebar.error(f"Failed to initialize engine: {e}")
        st.stop()

simulation = st.session_state['simulation']

# Ensure history exists if simulation was already loaded (safety check)
if 'history' not in st.session_state:
    st.session_state['history'] = [dashboard_connector.get_metrics(simulation)]

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

# --- Bulk Execution Controls ---
st.sidebar.markdown("---")
st.sidebar.subheader("Bulk Execution")
n_ticks = st.sidebar.number_input("Ticks to Run", min_value=1, max_value=100, value=10)
if st.sidebar.button(f"Run {n_ticks} Ticks"):
    progress_bar = st.sidebar.progress(0)
    for i in range(n_ticks):
        new_tick = dashboard_connector.run_tick(simulation)
        st.session_state['tick'] = new_tick

        # Append history
        metrics = dashboard_connector.get_metrics(simulation)
        st.session_state['history'].append(metrics)

        progress_bar.progress((i + 1) / n_ticks)
    st.sidebar.success(f"Ran {n_ticks} ticks!")
    st.rerun()

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

        # Append history
        metrics = dashboard_connector.get_metrics(simulation)
        st.session_state['history'].append(metrics)

        st.rerun()

# --- Visual Analytics ---
st.subheader("Visual Analytics (Pulse)")

if len(st.session_state['history']) > 0:
    # Convert history to DataFrame
    df_history = pd.DataFrame(st.session_state['history'])
    df_history.set_index('tick', inplace=True)

    # Chart 1: Demographics
    st.markdown("### Demographics")
    st.line_chart(df_history['total_population'])

    # Chart 2: Economic Health
    st.markdown("### Economic Health")
    col_eco1, col_eco2 = st.columns(2)
    with col_eco1:
        st.markdown("**GDP Growth**")
        st.line_chart(df_history['gdp'])
    with col_eco2:
        st.markdown("**Average Assets**")
        st.line_chart(df_history['average_assets'])

# --- Debug Info ---
if st.checkbox("Show Raw Metrics"):
    st.json(metrics)
