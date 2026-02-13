import streamlit as st
import pandas as pd
from typing import Dict, Any
from dashboard.components.controls import render_dynamic_controls

def render_main_cockpit():
    st.title("👁️ Watchtower Cockpit")

    # Access telemetry from session state (updated by app.py via SocketManager)
    telemetry = st.session_state.get("telemetry_buffer")

    if not telemetry:
        st.warning("No telemetry data received yet. Waiting for engine...")
        return

    # Telemetry is expected to be a Dict matching WatchtowerV2DTO structure
    data = telemetry

    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tick", data.get("tick", 0))
    with col2:
        macro = data.get("macro", {})
        gdp = macro.get("gdp", 0)
        st.metric("GDP", f"${gdp:,.2f}")
    with col3:
        macro = data.get("macro", {})
        cpi = macro.get("cpi", 0)
        st.metric("Inflation (CPI)", f"{cpi:.2f}")
    with col4:
        pop = data.get("population", {})
        active = pop.get("active_count", 0)
        st.metric("Population", f"{active:,}")

    # Integrity Check
    integrity = data.get("integrity", {})
    leak = integrity.get("m2_leak", 0.0)
    fps = integrity.get("fps", 0.0)

    if abs(leak) > 1.0:
        st.error(f"⚠️ M2 Leak Detected: {leak:.4f}")
    else:
        st.success(f"✅ System Integrity Normal (Leak: {leak:.4f}) - FPS: {fps:.1f}")

    # Controls Section
    st.divider()
    render_dynamic_controls(use_tabs=True)

    # Wealth Distribution Heatmap (Placeholder)
    st.subheader("Wealth Distribution")
    pop_dist = data.get("population", {}).get("distribution", {})
    if pop_dist:
        # q1..q5
        df = pd.DataFrame([pop_dist])
        st.bar_chart(df.T)

    # Finance Overview
    st.subheader("Financial Overview")
    fin = data.get("finance", {})
    supply = fin.get("supply", {})
    rates = fin.get("rates", {})

    c1, c2 = st.columns(2)
    with c1:
        st.write("**Money Supply**")
        st.json(supply)
    with c2:
        st.write("**Interest Rates**")
        st.json(rates)
