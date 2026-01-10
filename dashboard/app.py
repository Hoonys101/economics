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
else:
    st.sidebar.success(f"Engine Connected (Tick {st.session_state['tick']})")

simulation = st.session_state['simulation']

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
