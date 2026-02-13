from typing import List, Dict, Any, TYPE_CHECKING
from modules.analysis.scenario_verifier.api import IScenarioJudge, ScenarioReportDTO, ScenarioStatus
import logging

if TYPE_CHECKING:
    from modules.system.telemetry import TelemetryCollector

logger = logging.getLogger(__name__)

class ScenarioVerifier:
    """시나리오 검증 총괄 엔진"""
    def __init__(self, judges: List[IScenarioJudge]):
        self._judges = judges
        # Using class name or specific ID if judge exposes it. Assuming class name for now or judge.id if implemented.
        # But IScenarioJudge doesn't mandate ID property yet, but evaluate returns DTO with ID.
        self._active_scenarios: List[str] = [j.__class__.__name__ for j in judges]
        logger.info(f"ScenarioVerifier initialized with {len(judges)} judges: {self._active_scenarios}")

    def initialize(self, telemetry_collector: "TelemetryCollector") -> None:
        """
        각 판정관이 요구하는 데이터를 TelemetryCollector에 구독 신청함.
        """
        for judge in self._judges:
            required = judge.required_fields
            if required:
                # Frequency 1 tick for real-time monitoring
                telemetry_collector.subscribe(required, frequency_interval=1)
                logger.debug(f"Judge {judge.__class__.__name__} subscribed to {required}")

    def verify_tick(self, telemetry_data: Dict[str, Any]) -> List[ScenarioReportDTO]:
        """
        매 틱 호출되어 활성화된 시나리오를 평가함.
        telemetry_data: TelemetryCollector.harvest().data (snapshot.data)
        """
        reports = []
        for judge in self._judges:
            try:
                report = judge.evaluate(telemetry_data)
                reports.append(report)
            except Exception as e:
                logger.error(f"Error evaluating scenario with {judge.__class__.__name__}: {e}", exc_info=True)
                # Fail safe report
                reports.append(ScenarioReportDTO(
                    scenario_id=judge.__class__.__name__,
                    status=ScenarioStatus.FAILED,
                    progress_pct=0.0,
                    current_kpi_value=0.0,
                    target_kpi_value=0.0,
                    message=f"Evaluation Error: {str(e)}",
                    failure_reason="Runtime Exception"
                ))

        return reports
