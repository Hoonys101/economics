import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from dashboard.components.visuals import ScenarioCardVisualizer, AgentHeatmapVisualizer
from dashboard.components.controls import render_dynamic_controls
from simulation.dtos.commands import GodCommandDTO
from modules.analysis.scenario_verifier.api import ScenarioReportDTO, ScenarioStatus
from dashboard.services.socket_manager import SocketManager

def _get_or_create_visualizers():
    if "visualizers" not in st.session_state:
        st.session_state.visualizers = {
            "scenario": ScenarioCardVisualizer(),
            "heatmap": AgentHeatmapVisualizer()
        }
    return st.session_state.visualizers

def _update_telemetry_mask(visualizers: Dict[str, Any]):
    """
    Collects masks from active visualizers and sends update command if changed.
    """
    required_mask = set()

    # Always include basic telemetry (handled by default in backend? No, backend sends full WatchtowerV2DTO usually)
    # But if we use On-Demand, maybe we need to specify even basic fields?
    # Assuming WatchtowerV2DTO basic structure is always sent, and 'custom_data' is what we mask.

    # Check which visualizers are "active".
    # For now, let's assume all are active if they are in the dict.
    # In a real app, we might check if a tab is selected.

    # Example: If Drill-down is expanded
    if st.session_state.get("show_heatmap", False):
        required_mask.update(visualizers["heatmap"].required_mask)

    current_mask = st.session_state.get("current_telemetry_mask", set())

    # Convert to list for comparison and sending
    new_mask_list = sorted(list(required_mask))
    current_mask_list = sorted(list(current_mask))

    if new_mask_list != current_mask_list:
        st.session_state.current_telemetry_mask = required_mask

        # Send Command
        cmd = GodCommandDTO(
            command_type="UPDATE_TELEMETRY",
            target_domain="System",
            parameter_key="telemetry_mask",
            new_value=new_mask_list
        )
        # Use the singleton SocketManager instance (or get from session if stored)
        # Assuming app.py initializes it globally or in session
        socket_mgr = SocketManager()
        socket_mgr.send_command(cmd)
        # st.toast(f"Updated Telemetry Mask: {new_mask_list}")

def render_main_cockpit():
    st.title("👁️ Watchtower Cockpit")

    # Initialize Visualizers
    visualizers = _get_or_create_visualizers()

    # Toggle for Heatmap (Drill-down)
    st.toggle("Show Agent Micro-Distribution", key="show_heatmap")

    # Update Mask based on UI state
    _update_telemetry_mask(visualizers)

    # Access telemetry from session state (updated by app.py via SocketManager)
    telemetry = st.session_state.get("telemetry_buffer")

    if not telemetry:
        st.warning("No telemetry data received yet. Waiting for engine...")
        return

    # Telemetry is expected to be a Dict matching WatchtowerV2DTO structure
    data = telemetry

    # --- Top Metrics ---
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

    # --- Integrity Check ---
    integrity = data.get("integrity", {})
    leak = integrity.get("m2_leak", 0.0)
    fps = integrity.get("fps", 0.0)

    if abs(leak) > 1.0:
        st.error(f"⚠️ M2 Leak Detected: {leak:.4f}")
    else:
        st.success(f"✅ System Integrity Normal (Leak: {leak:.4f}) - FPS: {fps:.1f}")

    # --- Controls Section (UI-02) ---
    st.divider()
    render_dynamic_controls(use_tabs=True)

    # --- Scenario Progress (SCENARIO COCKPIT) ---
    st.divider()
    st.subheader("📊 Scenario Progress")

    scenario_reports_data = data.get("scenario_reports", [])
    if not scenario_reports_data:
        st.info("No active scenarios reported.")
    else:
        # Convert dicts back to DTOs for visualizer
        reports = []
        for report_data in scenario_reports_data:
            try:
                # Handle potential enum conversion if needed, but assuming simple dict structure for now
                # If report_data is already an object (unlikely via JSON), use it.
                if isinstance(report_data, dict):
                    # Manual reconstruction to ensure types
                    status_str = report_data.get("status", "PENDING")
                    # Map string to Enum
                    status_enum = ScenarioStatus.PENDING
                    if status_str == "SUCCESS": status_enum = ScenarioStatus.SUCCESS
                    elif status_str == "FAILED": status_enum = ScenarioStatus.FAILED
                    elif status_str == "RUNNING": status_enum = ScenarioStatus.RUNNING

                    report = ScenarioReportDTO(
                        scenario_id=report_data.get("scenario_id", "Unknown"),
                        status=status_enum,
                        progress_pct=report_data.get("progress_pct", 0.0),
                        current_kpi_value=report_data.get("current_kpi_value", 0.0),
                        target_kpi_value=report_data.get("target_kpi_value", 0.0),
                        message=report_data.get("message", ""),
                        failure_reason=report_data.get("failure_reason")
                    )
                    reports.append(report)
            except Exception as e:
                st.error(f"Error parsing scenario report: {e}")

        cols = st.columns(2)
        for i, report in enumerate(reports):
            with cols[i % 2]:
                visualizers["scenario"].render(report)

    # --- Micro-Insight Drill-down (HEATMAP) ---
    if st.session_state.get("show_heatmap", False):
        st.divider()
        # Pass custom_data or the whole telemetry dict
        custom_data = data.get("custom_data", {})
        # Merge with main data if needed, but visuals expects specific keys
        # The visualizer will look for 'population.distribution' etc.
        # Check if they are in 'custom_data' or root 'data'
        # TelemetryCollector puts masked data in 'custom_data' field of WatchtowerV2DTO ideally?
        # Wait, WatchtowerV2DTO has 'custom_data' field. TelemetryCollector returns 'data' dict.
        # We need to map where TelemetryCollector output goes.
        # Assuming the backend puts the dynamic keys into 'custom_data'.

        visualizers["heatmap"].render(custom_data)

    # --- Finance Overview (Legacy) ---
    st.divider()
    with st.expander("Financial Overview (Details)"):
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
