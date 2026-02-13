from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from simulation.orchestration.api import IPhaseStrategy

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_ScenarioAnalysis(IPhaseStrategy):
    """
    Phase 8: Scenario Analysis
    - Harvests telemetry data.
    - Runs Scenario Verifier to check success criteria.
    - Terminal node: does not modify state.
    """
    def __init__(self, world_state: "WorldState"):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # Check if components are available
        telemetry_collector = getattr(self.world_state, "telemetry_collector", None)
        scenario_verifier = getattr(self.world_state, "scenario_verifier", None)

        if not telemetry_collector or not scenario_verifier:
            logger.debug("ScenarioAnalysis skipped: components not initialized.")
            return state

        try:
            # 1. Harvest Data
            telemetry_snapshot = telemetry_collector.harvest(state.time)

            # 2. Verify Scenarios
            # harvest returns a dict with "data" key
            reports = scenario_verifier.verify_tick(telemetry_snapshot["data"])

            # 3. Log/Report Results
            # For now, we log to info/debug.
            # In future, this could push to a Dashboard Service or Watchtower.
            if reports:
                for report in reports:
                    # Log interesting updates
                    log_level = logging.INFO
                    if report.status.name == "RUNNING" and state.time % 10 != 0:
                         # Downsample logs for running state
                         log_level = logging.DEBUG

                    logger.log(
                        log_level,
                        f"SCENARIO_REPORT | {report.scenario_id} [{report.status.name}] "
                        f"Progress: {report.progress_pct:.1f}% | KPI: {report.current_kpi_value:.2f}/{report.target_kpi_value} | {report.message}",
                        extra={
                            "scenario_id": report.scenario_id,
                            "status": report.status.name,
                            "progress": report.progress_pct,
                            "kpi": report.current_kpi_value,
                            "tick": state.time
                        }
                    )

        except Exception as e:
            logger.error(f"Error in Phase_ScenarioAnalysis: {e}", exc_info=True)

        return state
