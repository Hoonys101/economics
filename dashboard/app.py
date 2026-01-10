import streamlit as st
import pandas as pd
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="The Matrix Cockpit", layout="wide")

st.title("The Matrix: Simulation Cockpit (Phase 20.5)")

st.sidebar.header("God Mode Controls")
st.sidebar.info("Initializing Interface...")

# Placeholder for Connector
st.write("Current Status: Simulation Stopped")

if st.sidebar.button("Run Simulation (Dry Run)"):
    st.write("Initializing Engine...")
    # TODO: Connect to simulation.interface.dashboard_connector
    st.success("Engine Connected (Mock)")
