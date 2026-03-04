from dataclasses import dataclass, field
from modules.system.api import OriginType
from typing import Any, Literal
from uuid import UUID, uuid4

@dataclass(frozen=True)
class GodCommandDTO:
    """
    God-Mode 조작 명령을 위한 최상위 데이터 계약.
    """
    target_domain: str
    parameter_key: str
    new_value: Any
    command_id: UUID = field(default_factory=uuid4)
    command_type: Literal['SET_PARAM', 'TRIGGER_EVENT', 'INJECT_ASSET', 'PAUSE_STATE', 'UPDATE_TELEMETRY', 'INJECT_MONEY'] = ...
    requester_id: str = ...
    metadata: dict[str, Any] = field(default_factory=dict)
    target_agent_id: str | None = ...
    amount: int | None = ...
    @property
    def origin(self) -> OriginType: ...

@dataclass(frozen=True)
class GodResponseDTO:
    """
    명령 실행 결과 및 감사(Audit) 리포트.
    """
    command_id: UUID
    success: bool
    execution_tick: int
    error_code: str | None = ...
    failure_reason: str | None = ...
    audit_report: dict[str, Any] = field(default_factory=dict)
    rollback_performed: bool = ...
