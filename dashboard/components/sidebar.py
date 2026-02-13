import streamlit as st
from dashboard.services.socket_manager import SocketManager
from dashboard.components.controls import render_dynamic_controls

def render_sidebar():
    st.sidebar.title("🎮 Global Controls")

    # Connection Status
    socket_mgr = SocketManager()
    status = socket_mgr.connection_status

    color = "green" if status == "Connected" else "red"
    st.sidebar.markdown(f"**Engine Status:** :{color}[{status}]")

    # Intervention Toggle
    # Use key to persist state and share with other components
    god_mode = st.sidebar.toggle("God Mode (Intervention)", value=False, key="god_mode_active")

    st.sidebar.divider()

    if not god_mode:
        st.sidebar.info("Enable God Mode to adjust parameters.")
        # We return here, so sidebar doesn't show controls.
        # But main_cockpit will still render them.
        return

    # Use shared dynamic controls component
    render_dynamic_controls(container=st.sidebar, use_tabs=False)
