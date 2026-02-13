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
    command_type: Literal["SET_PARAM", "TRIGGER_EVENT", "INJECT_ASSET", "PAUSE_STATE"] = "SET_PARAM"
    requester_id: str = "WATCHTOWER_UI"
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Backward compatibility helpers (optional, but might be useful if existing code uses them)
    # The spec removed target_agent_id and amount, mapping them to metadata or specific params?
    # Spec says: "INJECT_ASSET" -> new_value might be the amount?
    # Let's check the spec again.
    # Spec example: "INJECT_MONEY" was in the old code. Spec lists "INJECT_ASSET".
    # Spec doesn't detail INJECT_ASSET fields.
    # However, existing code uses target_agent_id and amount.
    # I should likely map INJECT_ASSET to use target_domain="Agent", parameter_key="{agent_id}.balance", new_value={amount}?
    # Or keep strict spec.
    # The spec pseudo-code uses `cmd.target_domain`, `cmd.parameter_key`, `cmd.new_value`.
    # But Phase0_Intercept uses `cmd.amount`.
    # I will add `target_agent_id` and `amount` as optional fields for convenience/compatibility if not strictly forbidden,
    # OR I will rely on `metadata` or `new_value` interpretation.
    # The spec says:
    # "parameter_key: str # e.g., 'tax_rate'"
    # "new_value: Any"
    #
    # Let's follow the spec STRICTLY for the main fields, but for `INJECT_ASSET` (which seems to replace INJECT_MONEY),
    # I might need to store the amount in `new_value` and the agent ID in `parameter_key` or `target_domain`.
    # Let's assume INJECT_ASSET uses:
    # target_domain="Agent"
    # parameter_key="{agent_id}" (or similar)
    # new_value={amount}
    #
    # However, for `INJECT_MONEY` legacy support in Phase0_Intercept (which I am rewriting anyway), I can adapt.
    # But `Phase0_Intercept` in the codebase I read uses `cmd.amount`.
    # Let's add properties to map these for easier access if needed, or just update Phase0 to use the new fields.

    @property
    def amount(self) -> Optional[int]:
        """Helper to get amount from new_value if type is INJECT_ASSET"""
        if self.command_type == "INJECT_ASSET" and isinstance(self.new_value, int):
            return self.new_value
        return None

    @property
    def target_agent_id(self) -> Optional[str]:
         """Helper to get agent ID from parameter_key if type is INJECT_ASSET"""
         if self.command_type == "INJECT_ASSET":
             return self.parameter_key
         return None

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
