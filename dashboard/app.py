import streamlit as st
import time
import sys
import os

# Add project root to sys.path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dashboard.services.socket_manager import SocketManager
from dashboard.components.sidebar import render_sidebar
from dashboard.components.main_cockpit import render_main_cockpit
from dashboard.components.command_center import render_command_center

# 1. Page Config
st.set_page_config(
    page_title="GodMode Watchtower",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Initialization
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    # Start SocketManager (it's a singleton, so init creates the thread once)
    SocketManager()

# 3. Sidebar (Global Controls)
render_sidebar()

# 4. Main Area
socket_mgr = SocketManager()

# Poll for latest telemetry (UI Loop)
new_data = socket_mgr.get_latest_telemetry()
if new_data:
    st.session_state.telemetry_buffer = new_data

# Render Main Cockpit
render_main_cockpit()

# Render Command Center
render_command_center()

# 5. Auto-refresh logic
# Refresh periodically to fetch new data from the socket thread
# Adjust sleep time to balance responsiveness and resource usage
time.sleep(1.0)
st.rerun()
