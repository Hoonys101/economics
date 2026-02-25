from _typeshed import Incomplete
from modules.analysis.scenario_verifier.api import IScenarioJudge as IScenarioJudge, ScenarioReportDTO as ScenarioReportDTO, ScenarioStatus as ScenarioStatus
from modules.system.telemetry import TelemetryCollector as TelemetryCollector
from typing import Any

logger: Incomplete

class ScenarioVerifier:
    """시나리오 검증 총괄 엔진"""
    def __init__(self, judges: list[IScenarioJudge]) -> None: ...
    def initialize(self, telemetry_collector: TelemetryCollector) -> None:
        """
        각 판정관이 요구하는 데이터를 TelemetryCollector에 구독 신청함.
        """
    def verify_tick(self, telemetry_data: dict[str, Any]) -> list[ScenarioReportDTO]:
        """
        매 틱 호출되어 활성화된 시나리오를 평가함.
        telemetry_data: TelemetryCollector.harvest().data (snapshot.data)
        """
