# simulation/dtos/api.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union, TypedDict
from modules.simulation.dtos.api import FirmStateDTO, HouseholdConfigDTO, FirmConfigDTO
from simulation.models import Order
from simulation.dtos.decision_dtos import DecisionOutputDTO
from modules.finance.api import IFinancialAgent
from modules.simulation.api import AgentID
from modules.governance.api import SystemCommand
from simulation.dtos.commands import GodCommandDTO

# Phase 1: MarketSnapshotDTO moved to modules.system.api
from modules.system.api import (
    CurrencyCode,
    MarketSnapshotDTO,
    HousingMarketSnapshotDTO,
    LoanMarketSnapshotDTO,
    LaborMarketSnapshotDTO,
    HousingMarketUnitDTO,
    MarketContextDTO
)
# Phase 1: EconomicIndicatorsDTO from modules.simulation.api
from modules.simulation.api import EconomicIndicatorsDTO

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.dtos.scenario import StressScenarioConfig
    from modules.household.dtos import HouseholdStateDTO

# Alias for standardization
OrderDTO = Order

# ... (Previous DTOs: TransactionData, AgentStateData, etc. remain unchanged) ...

@dataclass
class TransactionData:
    run_id: int
    time: int
    buyer_id: AgentID
    seller_id: AgentID
    item_id: str
    quantity: float
    price: float
    total_pennies: int
    currency: CurrencyCode
    market_id: str
    transaction_type: str

@dataclass
class AgentStateData:
    run_id: int
    time: int
    agent_id: AgentID
    agent_type: str
    assets: Dict[CurrencyCode, int]
    is_active: bool
    is_employed: Optional[bool] = None
    employer_id: Optional[AgentID] = None
    needs_survival: Optional[float] = None
    needs_labor: Optional[float] = None
    inventory_food: Optional[float] = None
    current_production: Optional[float] = None
    num_employees: Optional[int] = None
    education_xp: Optional[float] = None
    generation: Optional[int] = 0
    time_worked: Optional[float] = None
    time_leisure: Optional[float] = None

@dataclass
class EconomicIndicatorData:
    run_id: int
    time: int
    unemployment_rate: Optional[float] = None
    avg_wage: Optional[float] = None
    food_avg_price: Optional[float] = None
    food_trade_volume: Optional[float] = None
    avg_goods_price: Optional[float] = None
    total_production: Optional[float] = None
    total_consumption: Optional[int] = None
    total_household_assets: Optional[int] = None
    total_firm_assets: Optional[int] = None
    total_food_consumption: Optional[int] = None
    total_inventory: Optional[float] = None
    avg_survival_need: Optional[float] = None
    total_labor_income: Optional[int] = None
    total_capital_income: Optional[int] = None
    avg_education_level: Optional[float] = None
    education_spending: Optional[float] = None
    education_coverage: Optional[float] = None
    brain_waste_count: Optional[int] = None

@dataclass
class MarketHistoryData:
    time: int
    market_id: str
    item_id: Optional[str] = None
    avg_price: Optional[float] = None
    trade_volume: Optional[float] = None
    best_ask: Optional[float] = None
    best_bid: Optional[float] = None
    avg_ask: Optional[float] = None
    avg_bid: Optional[float] = None
    worst_ask: Optional[float] = None
    worst_bid: Optional[float] = None

@dataclass
class AIDecisionData:
    run_id: int
    tick: int
    agent_id: AgentID
    decision_type: str
    decision_details: Optional[Dict[str, Any]] = None
    predicted_reward: Optional[float] = None
    actual_reward: Optional[float] = None

class GoodsDTO(TypedDict, total=False):
    id: str
    name: str
    category: str
    is_durable: bool
    is_essential: bool
    initial_price: int
    base_need_satisfaction: float
    quality_modifier: float
    type: str
    satiety: float
    decay_rate: float

class MarketHistoryDTO(TypedDict, total=False):
    avg_price: float
    trade_volume: float
    best_ask: int
    best_bid: int
    avg_ask: float
    avg_bid: float
    worst_ask: int
    worst_bid: int

@dataclass
class GovernmentPolicyDTO:
    income_tax_rate: float
    sales_tax_rate: float
    corporate_tax_rate: float
    base_interest_rate: float

@dataclass
class FiscalContext:
    government: IFinancialAgent

@dataclass
class MacroFinancialContext:
    inflation_rate: float
    gdp_growth_rate: float
    market_volatility: float
    interest_rate_trend: float

@dataclass
class DecisionInputDTO:
    market_snapshot: MarketSnapshotDTO
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    fiscal_context: Optional[FiscalContext] = None
    macro_context: Optional[MacroFinancialContext] = None
    stress_scenario_config: Optional[Any] = None
    government_policy: Optional[GovernmentPolicyDTO] = None
    agent_registry: Optional[Dict[str, int]] = None
    housing_system: Optional[Any] = None
    market_context: Optional[MarketContextDTO] = None

@dataclass
class DecisionContext:
    goods_data: List[GoodsDTO]
    market_data: Dict[str, MarketHistoryDTO]
    current_time: int
    state: Union[HouseholdStateDTO, FirmStateDTO]
    config: Union[HouseholdConfigDTO, FirmConfigDTO]
    market_snapshot: Optional[MarketSnapshotDTO] = None
    government_policy: Optional[GovernmentPolicyDTO] = None
    stress_scenario_config: Optional[StressScenarioConfig] = None
    agent_registry: Dict[str, AgentID] = field(default_factory=dict)
    market_context: Optional[MarketContextDTO] = None

@dataclass
class SimulationState:
    """
    WO-103: Simulation State DTO to reduce coupling.
    Passes all necessary data from the Simulation object to system services.
    
    Aligned with MISSION_PHASE23_HYGIENE_SPEC.md:
    - Renamed 'government' to 'primary_government' to imply singleton proxy.
    - Added 'governments' list for WorldState parity.
    - Renamed 'god_commands' to 'god_command_snapshot' to reflect frozen state.
    """
    time: int
    households: List[Household]
    firms: List[Firm]
    agents: Dict[AgentID, Any]
    markets: Dict[str, Any]
    
    # --- Renamed/Added Fields for Hygiene ---
    primary_government: Any  # Was 'government'. The active/primary government agent.
    governments: List[Any]   # Added. List of all government entities.
    # ----------------------------------------
    
    bank: Any        # Bank
    central_bank: Any # CentralBank
    escrow_agent: Optional[Any] # EscrowAgent
    stock_market: Optional[Any] # StockMarket
    stock_tracker: Optional[Any] # Added for WO-133 Fix
    goods_data: Dict[str, Any]
    market_data: Dict[str, Any] # Added for WO-103
    config_module: Any
    tracker: Any
    logger: Any # logging.Logger
    ai_training_manager: Optional[Any]
    ai_trainer: Optional[Any] # Added for WO-103
    settlement_system: Optional[Any] = None # WO-112: Settlement System
    next_agent_id: int = 0 # Added for WO-103
    real_estate_units: List[Any] = field(default_factory=list) # Added for WO-103
    
    # Mutable state for the tick
    transactions: List[Any] = None # List[Transaction]
    inter_tick_queue: List[Any] = None # List[Transaction]
    effects_queue: List[Dict[str, Any]] = None # WO-109: Queue for side-effects
    inactive_agents: Dict[AgentID, Any] = None # WO-109: Store inactive agents
    taxation_system: Optional[Any] = None # WO-116: Taxation System
    currency_holders: List[Any] = None # Added for M2 tracking (Phase 33/5)
    stress_scenario_config: Optional[StressScenarioConfig] = None # Phase 28
    transaction_processor: Optional[Any] = None # Added for system delegation compatibility
    shareholder_registry: Optional[Any] = None # TD-275 Shareholder Registry

    # Phase 4.1: Saga Orchestration & Monetary Ledger (TD-253)
    saga_orchestrator: Optional[Any] = None
    monetary_ledger: Optional[Any] = None

    # TD-255: System Command Pipeline
    system_commands: List[SystemCommand] = field(default_factory=list)
    
    # --- Renamed Field for Hygiene ---
    god_command_snapshot: List[GodCommandDTO] = field(default_factory=list) # Was 'god_commands'. Frozen for tick.
    # ---------------------------------

    # --- NEW TRANSIENT FIELDS ---
    firm_pre_states: Dict[AgentID, Any] = None
    household_pre_states: Dict[AgentID, Any] = None
    household_time_allocation: Dict[AgentID, float] = None
    planned_consumption: Optional[Dict[AgentID, Dict[str, Any]]] = None
    household_leisure_effects: Dict[AgentID, float] = None

    # Injection
    injectable_sensory_dto: Optional[Any] = None 
    currency_registry_handler: Optional[Any] = None 

    def register_currency_holder(self, holder: Any) -> None:
        if self.currency_registry_handler:
            self.currency_registry_handler.register_currency_holder(holder)
        elif self.currency_holders is not None:
             self.currency_holders.append(holder)

    def unregister_currency_holder(self, holder: Any) -> None:
        if self.currency_registry_handler:
            self.currency_registry_handler.unregister_currency_holder(holder)
        elif self.currency_holders is not None:
             if holder in self.currency_holders:
                 self.currency_holders.remove(holder)

    def __post_init__(self):
        if self.transactions is None:
            self.transactions = []
        if self.system_commands is None:
            self.system_commands = []
        if self.god_command_snapshot is None:
            self.god_command_snapshot = []
        if self.inter_tick_queue is None:
            self.inter_tick_queue = []
        if self.effects_queue is None:
            self.effects_queue = []
        if self.inactive_agents is None:
            self.inactive_agents = {}
        if self.currency_holders is None:
            self.currency_holders = []
        if self.firm_pre_states is None:
            self.firm_pre_states = {}
        if self.household_pre_states is None:
            self.household_pre_states = {}
        if self.household_time_allocation is None:
            self.household_time_allocation = {}
        if self.planned_consumption is None:
            self.planned_consumption = {}
        if self.household_leisure_effects is None:
            self.household_leisure_effects = {}
        if self.governments is None:
            self.governments = []

# ... (Remaining DTOs: StockMarketHistoryData, etc. remain unchanged) ...
```

```markdown
# Design Document: Phase 23 Hygiene - DTO & WorldState Alignment

## 1. Introduction
- **Purpose**: To align `SimulationState` DTO naming conventions with `WorldState` to prevent singleton/list mismatches and clarify data mutability (Snapshot vs Queue).
- **Scope**: `simulation/dtos/api.py`, `simulation/orchestration/tick_orchestrator.py`, and dependent modules.
- **Goals**: 
    - Resolve **TD-ARCH-GOV-MISMATCH** (Singleton vs List).
    - Hardening of `GodCommand` handling by explicit snapshot naming.
    - Strict adherence to `MISSION_PHASE23_HYGIENE_SPEC.md`.

## 2. Detailed Design

### 2.1. Component: SimulationState DTO (`simulation/dtos/api.py`)
- **Modification**:
    - Rename `government` -> `primary_government` (Explicit Singleton Proxy).
    - Add `governments: List[Any]` (Full Registry access).
    - Rename `god_commands` -> `god_command_snapshot` (Immutable View of Queue).
- **Rationale**:
    - `WorldState` maintains `governments` as a list, but exposes `government` as a property. `SimulationState` blindly mapping `government` hid the underlying list structure.
    - `god_commands` in `SimulationState` is a `List` populated from a `Deque`. Calling it `snapshot` enforces the mental model that it is frozen for the tick.

### 2.2. Component: TickOrchestrator (`simulation/orchestration/tick_orchestrator.py`)
- **Modification**:
    - Update `_create_simulation_state_dto`:
        ```python
        return SimulationState(
            # ...
            primary_government=state.government, # Map property to new field
            governments=state.governments,       # Map list to new field
            god_command_snapshot=god_commands_for_tick, # Map drained list to new field
            # ...
        )
        ```

## 3. Impact Analysis & Risk Assessment (Ripple Effects)

### 3.1. Breaking Changes
- **High Risk**: Renaming `.government` will break any logic accessing `state.government`.
    - **Impacted Modules**:
        - `modules/finance/system.py`: Likely uses `state.government` for fiscal checks.
        - `modules/government/`: Tax collection logic.
        - `simulation/orchestration/phases/`: `Phase_GovernmentPrograms`, `Phase_TaxationIntents`.
- **Mitigation**:
    - Systematic `grep` and replace is required immediately after DTO update.
    - Search Pattern: `state.government` -> `state.primary_government`.

### 3.2. Test Impact
- **Test Failures Expected**:
    - `tests/unit/systems/test_finance.py`
    - `tests/unit/agents/test_government.py`
    - `tests/orchestration/test_tick_orchestrator.py`
- **Action**: Tests mocking `SimulationState` must be updated to use the new field names.

## 4. Verification Plan

### 4.1. Static Analysis
- Run `grep -r "state.government" .` to ensure zero occurrences in `modules/` (except where aliased intentionally).
- Run `grep -r "state.god_commands" .` to ensure zero occurrences.

### 4.2. Runtime Verification
- Execute `pytest tests/unit/systems/test_finance.py` (or equivalent) to verify `primary_government` access works.
- Execute a full tick loop in `diagnose_runtime.py` to ensure `TickOrchestrator` correctly populates the DTO.

## 5. Mandatory Reporting
**[REQUIRED ACTION]**:
Upon completion of the code changes, create a new file: `communications/insights/fix-dto-naming-alignment.md` containing:
1.  Confirmation of the rename operations.
2.  Output of the test run verifying the fix.
3.  Any other "Hygiene" issues discovered during the refactor (e.g., other `state` fields that are ambiguous).

## 6. Debt Ledger Update
- **TD-ARCH-GOV-MISMATCH**: Mark as **Resolved**.