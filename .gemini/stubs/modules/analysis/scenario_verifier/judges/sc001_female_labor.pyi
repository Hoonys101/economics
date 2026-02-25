from modules.analysis.scenario_verifier.api import IScenarioJudge as IScenarioJudge, ScenarioReportDTO as ScenarioReportDTO, ScenarioStatus as ScenarioStatus
from typing import Any

class FemaleLaborParticipationJudge:
    SCENARIO_ID: str
    REQUIRED_FIELD: str
    @property
    def required_fields(self) -> list[str]: ...
    def evaluate(self, telemetry_data: dict[str, Any]) -> ScenarioReportDTO: ...
