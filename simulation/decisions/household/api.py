from __future__ import annotations
from typing import List, Dict, Any, Optional, Protocol, TYPE_CHECKING
from dataclasses import dataclass

from simulation.models import Order, StockOrder
from simulation.dtos import MacroFinancialContext, MarketSnapshotDTO

if TYPE_CHECKING:
    from modules.household.dtos import HouseholdStateDTO
    from simulation.dtos import HouseholdConfigDTO

@dataclass
class ConsumptionContext:
    household: HouseholdStateDTO
    config: HouseholdConfigDTO
    market_data: Dict[str, Any]
    action_vector: Any # HouseholdActionVector
    savings_roi: float
    debt_penalty: float
    stress_config: Any = None
    logger: Optional[Any] = None

@dataclass
class LaborContext:
    household: HouseholdStateDTO
    config: HouseholdConfigDTO
    market_data: Dict[str, Any]
    action_vector: Any
    current_time: int
    logger: Optional[Any] = None

@dataclass
class AssetManagementContext:
    household: HouseholdStateDTO
    config: HouseholdConfigDTO
    market_data: Dict[str, Any]
    market_snapshot: Optional[MarketSnapshotDTO]
    macro_context: Optional[MacroFinancialContext]
    action_vector: Any
    current_time: int
    stress_config: Any = None
    logger: Optional[Any] = None

@dataclass
class HousingContext:
    household: HouseholdStateDTO
    config: HouseholdConfigDTO
    market_data: Dict[str, Any]
    market_snapshot: Optional[MarketSnapshotDTO]
    current_time: int
    stress_config: Any = None
    logger: Optional[Any] = None

class ConsumptionManagerProtocol(Protocol):
    def decide_consumption(self, context: ConsumptionContext) -> List[Order]: ...

class LaborManagerProtocol(Protocol):
    def decide_labor(self, context: LaborContext) -> List[Order]: ...

class AssetManagerProtocol(Protocol):
    def decide_investments(self, context: AssetManagementContext) -> List[Order]: ...
    def get_savings_roi(self, household: HouseholdStateDTO, market_data: Dict[str, Any]) -> float: ...
    def get_debt_penalty(self, household: HouseholdStateDTO, market_data: Dict[str, Any], config: HouseholdConfigDTO) -> float: ...

class HousingManagerProtocol(Protocol):
    def decide_housing(self, context: HousingContext) -> List[Order]: ...
