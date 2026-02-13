from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from datetime import datetime
from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.watchtower_v2 import WatchtowerV2DTO
from simulation.orchestration.dashboard_service import DashboardService

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

            # 4. Watchtower V2 Broadcast (INT-01)
            if self.world_state.telemetry_exchange:
                # Cache DashboardService instance in WorldState to avoid re-instantiation overhead
                if not self.world_state.dashboard_service:
                    self.world_state.dashboard_service = DashboardService(self.world_state)

                base_snapshot = self.world_state.dashboard_service.get_snapshot()

                # Construct V2 DTO
                v2_dto = WatchtowerV2DTO(
                    tick=state.time,
                    timestamp=datetime.now().timestamp(),
                    status=base_snapshot.status,
                    integrity=base_snapshot.integrity,
                    macro=base_snapshot.macro,
                    finance=base_snapshot.finance,
                    politics=base_snapshot.politics,
                    population=base_snapshot.population,
                    scenario_reports=reports,
                    custom_data=telemetry_snapshot.get("data", {})
                )

                # Update Exchange
                self.world_state.telemetry_exchange.update(v2_dto)

        except Exception as e:
            logger.error(f"Error in Phase_ScenarioAnalysis: {e}", exc_info=True)

        return state
