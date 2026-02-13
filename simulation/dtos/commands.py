from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Literal
from uuid import UUID, uuid4
from modules.system.api import OriginType

@dataclass(frozen=True)
class GodCommandDTO:
    """
    God-Mode 조작 명령을 위한 최상위 데이터 계약.
    """
    target_domain: str        # e.g., "Economy", "Government", "Finance"
    parameter_key: str        # e.g., "tax_rate", "harvest_multiplier"
    new_value: Any
    command_id: UUID = field(default_factory=uuid4)
    command_type: Literal["SET_PARAM", "TRIGGER_EVENT", "INJECT_ASSET", "PAUSE_STATE", "UPDATE_TELEMETRY", "INJECT_MONEY"] = "SET_PARAM"
    requester_id: str = "WATCHTOWER_UI"
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Backward compatibility fields
    target_agent_id: Optional[str] = None
    amount: Optional[int] = None

    @property
    def origin(self) -> OriginType:
        return OriginType.GOD_MODE

@dataclass(frozen=True)
class GodResponseDTO:
    """
    명령 실행 결과 및 감사(Audit) 리포트.
    """
    command_id: UUID
    success: bool
    execution_tick: int
    error_code: Optional[str] = None
    failure_reason: Optional[str] = None
    audit_report: Dict[str, Any] = field(default_factory=dict) # SettlementSystem 결과 포함
    rollback_performed: bool = False
