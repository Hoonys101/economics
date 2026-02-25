from dataclasses import dataclass
from modules.household.dtos import HouseholdStateDTO as HouseholdStateDTO
from simulation.dtos import HouseholdConfigDTO as HouseholdConfigDTO, MacroFinancialContext as MacroFinancialContext, MarketSnapshotDTO as MarketSnapshotDTO
from simulation.models import Order as Order
from typing import Any, Protocol

@dataclass
class ConsumptionContext:
    household: HouseholdStateDTO
    config: HouseholdConfigDTO
    market_data: dict[str, Any]
    action_vector: Any
    savings_roi: float
    debt_penalty: float
    stress_config: Any = ...
    logger: Any | None = ...

@dataclass
class LaborContext:
    household: HouseholdStateDTO
    config: HouseholdConfigDTO
    market_data: dict[str, Any]
    action_vector: Any
    current_time: int
    logger: Any | None = ...

@dataclass
class AssetManagementContext:
    household: HouseholdStateDTO
    config: HouseholdConfigDTO
    market_data: dict[str, Any]
    market_snapshot: MarketSnapshotDTO | None
    macro_context: MacroFinancialContext | None
    action_vector: Any
    current_time: int
    stress_config: Any = ...
    logger: Any | None = ...

@dataclass
class HousingContext:
    household: HouseholdStateDTO
    config: HouseholdConfigDTO
    market_data: dict[str, Any]
    market_snapshot: MarketSnapshotDTO | None
    current_time: int
    stress_config: Any = ...
    logger: Any | None = ...

class ConsumptionManagerProtocol(Protocol):
    def decide_consumption(self, context: ConsumptionContext) -> list[Order]: ...

class LaborManagerProtocol(Protocol):
    def decide_labor(self, context: LaborContext) -> list[Order]: ...

class AssetManagerProtocol(Protocol):
    def decide_investments(self, context: AssetManagementContext) -> list[Order]: ...
    def get_savings_roi(self, household: HouseholdStateDTO, market_data: dict[str, Any]) -> float: ...
    def get_debt_penalty(self, household: HouseholdStateDTO, market_data: dict[str, Any], config: HouseholdConfigDTO) -> float: ...

class HousingManagerProtocol(Protocol):
    def decide_housing(self, context: HousingContext) -> list[Order]: ...
