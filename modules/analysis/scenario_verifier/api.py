from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Protocol, runtime_checkable

class ScenarioStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

@dataclass(frozen=True)
class ScenarioReportDTO:
    """시나리오 판정 결과 및 상태를 담는 DTO"""
    scenario_id: str
    status: ScenarioStatus
    progress_pct: float
    current_kpi_value: float
    target_kpi_value: float
    message: str
    failure_reason: Optional[str] = None

@runtime_checkable
class IScenarioJudge(Protocol):
    """개별 시나리오 카드 판정 인터페이스"""

    @property
    def required_fields(self) -> List[str]:
        """TelemetryCollector에서 수집해야 할 필드 목록"""
        ...

    def evaluate(self, telemetry_data: Dict[str, Any]) -> ScenarioReportDTO:
        """수집된 데이터를 바탕으로 시나리오 성공 여부를 판정"""
        ...
