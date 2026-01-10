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

# Agent Selector
st.sidebar.markdown("---")
st.sidebar.subheader("Inspector Controls")
selected_agent_id = st.sidebar.number_input(
    "Agent ID",
    min_value=0,
    value=st.session_state.get('selected_agent_id', 0),
    step=1
)
st.session_state['selected_agent_id'] = selected_agent_id


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

# --- Agent Mind Inspector ---
with st.expander("🧠 Agent Mind Inspector", expanded=True):
    if 'selected_agent_id' in st.session_state:
        agent_details = dashboard_connector.get_agent_details(simulation, st.session_state['selected_agent_id'])

        if "error" in agent_details:
            st.error(agent_details["error"])
        else:
            # Display Key Stats in Columns
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("ID", agent_details['id'])
            c2.metric("Assets", f"{agent_details['assets']:.2f}")
            c3.metric("Age/Gender", f"{agent_details['age']:.1f} / {agent_details['gender']}")
            c4.metric("Children", agent_details['children_count'])

            st.markdown("#### System 2 Projections")
            c5, c6, c7 = st.columns(3)
            c5.metric("NPV Wealth", f"{agent_details['npv_wealth']:.2f}")
            c6.metric("Bankruptcy Tick", str(agent_details['bankruptcy_tick']))
            c7.metric("Last Leisure", agent_details['last_leisure_type'])

            # Show raw data for debugging
            if st.checkbox("Show Raw Agent Data"):
                st.json(agent_details)

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
