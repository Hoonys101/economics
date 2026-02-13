from typing import List, Dict, Any, TYPE_CHECKING
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.analysis.scenario_verifier.api import ScenarioReportDTO, ScenarioStatus

class BaseVisualizer:
    """모든 차트 컴포넌트의 기본 클래스"""
    @property
    def required_mask(self) -> List[str]:
        """이 차트가 필요로 하는 데이터 필드 목록"""
        return []

    def render(self, data: Dict[str, Any]):
        """데이터를 받아 Streamlit에 렌더링"""
        raise NotImplementedError

class ScenarioCardVisualizer(BaseVisualizer):
    def render(self, report: ScenarioReportDTO):
        # Determine color based on status
        status_color = "gray"
        if report.status == ScenarioStatus.SUCCESS:
            status_color = "green"
        elif report.status == ScenarioStatus.FAILED:
            status_color = "red"
        elif report.status == ScenarioStatus.RUNNING:
            status_color = "blue"

        with st.container(border=True):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric(
                    label="Progress",
                    value=f"{report.progress_pct:.1f}%",
                    delta=f"{report.current_kpi_value - report.target_kpi_value:.2f}"
                )
                st.progress(max(0.0, min(1.0, report.progress_pct / 100.0)))

            with col2:
                st.subheader(f"Scenario: {report.scenario_id}")
                st.caption(f"Status: :{status_color}[{report.status.value}]")
                if report.failure_reason:
                    st.error(f"Failure Reason: {report.failure_reason}")
                st.write(report.message)

class AgentHeatmapVisualizer(BaseVisualizer):
    @property
    def required_mask(self) -> List[str]:
        # Required paths for heatmap
        return ["population.distribution", "household_detailed_stats"]

    def render(self, data: Dict[str, Any]):
        # Expecting data to contain keys from required_mask (mapped from custom_data or main payload)
        # Note: The data passed here should be the full WatchtowerV2DTO-like dict or a subset.
        # Let's assume 'data' is the 'custom_data' or we extract from it.

        # Check if we have the data
        dist_data = data.get("population.distribution")
        detailed_stats = data.get("household_detailed_stats")

        if not detailed_stats:
            st.info("Waiting for agent detailed stats...")
            return

        # Convert to DataFrame
        # Assuming detailed_stats is a list of dicts: [{age, wealth, id, ...}]
        try:
            df = pd.DataFrame(detailed_stats)
            if df.empty:
                 st.warning("No agent data available.")
                 return

            # Plotly Heatmap or Scatter
            # Using Scatter for now as it's more versatile for "Heatmap" style visualization of agents
            # X: Age, Y: Wealth, Color: Satisfaction/Occupation
            st.subheader("Agent Micro-Distribution")

            fig = px.scatter(
                df,
                x="age",
                y="wealth",
                color="satisfaction" if "satisfaction" in df.columns else None,
                size="wealth",
                hover_data=["id", "occupation"] if "occupation" in df.columns else ["id"],
                title="Agent Wealth vs Age Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Failed to render heatmap: {e}")
