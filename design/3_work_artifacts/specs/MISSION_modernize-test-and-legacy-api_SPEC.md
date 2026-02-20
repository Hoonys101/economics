simulation/dtos/api.py
```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, TypedDict, TYPE_CHECKING
from modules.simulation.dtos.api import FirmStateDTO, HouseholdConfigDTO, FirmConfigDTO
from simulation.models import Order
from modules.finance.api import IFinancialAgent
from modules.simulation.api import AgentID
from modules.governance.api import SystemCommand
from simulation.dtos.commands import GodCommandDTO

# Alias for standardization
OrderDTO = Order

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.dtos.scenario import StressScenarioConfig
    from modules.household.dtos import HouseholdStateDTO

# ... [Keep previous DTOs like TransactionData, AgentStateData, etc. unchanged] ...

@dataclass
class SimulationState:
    """
    WO-103: Simulation State DTO to reduce coupling.
    Passes all necessary data from the Simulation object to system services.
    
    Refactored for Phase 23 Hygiene:
    - government -> primary_government (Singleton support)
    - added governments (Multi-gov support)
    - god_commands -> god_command_snapshot (Snapshot semantics)
    """
    time: int
    households: List[Household]
    firms: List[Firm]
    agents: Dict[AgentID, Any]
    markets: Dict[str, Any]
    
    # [Refactor] Renamed from 'government' to explicit 'primary_government'
    primary_government: Any  
    
    # [New] List of all governments for WorldState alignment
    governments: List[Any] = field(default_factory=list) 

    bank: Any        # Bank
    central_bank: Any # CentralBank
    escrow_agent: Optional[Any] # EscrowAgent
    stock_market: Optional[Any] # StockMarket
    stock_tracker: Optional[Any] 
    goods_data: Dict[str, Any]
    market_data: Dict[str, Any]
    config_module: Any
    tracker: Any
    logger: Any 
    ai_training_manager: Optional[Any]
    ai_trainer: Optional[Any]
    settlement_system: Optional[Any] = None
    next_agent_id: int = 0 
    real_estate_units: List[Any] = field(default_factory=list) 
    
    transactions: List[Any] = None 
    inter_tick_queue: List[Any] = None 
    effects_queue: List[Dict[str, Any]] = None 
    inactive_agents: Dict[AgentID, Any] = None 
    taxation_system: Optional[Any] = None 
    currency_holders: List[Any] = None 
    stress_scenario_config: Optional[StressScenarioConfig] = None 
    transaction_processor: Optional[Any] = None 
    shareholder_registry: Optional[Any] = None 

    saga_orchestrator: Optional[Any] = None
    monetary_ledger: Optional[Any] = None

    system_commands: List[SystemCommand] = field(default_factory=list)
    
    # [Refactor] Renamed to reflect snapshot nature
    god_command_snapshot: List[GodCommandDTO] = field(default_factory=list) 

    # --- NEW TRANSIENT FIELDS ---
    firm_pre_states: Dict[AgentID, Any] = None
    household_pre_states: Dict[AgentID, Any] = None
    household_time_allocation: Dict[AgentID, float] = None
    planned_consumption: Optional[Dict[AgentID, Dict[str, Any]]] = None 
    household_leisure_effects: Dict[AgentID, float] = None
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
```

simulation/systems/api.py
```python
"""
God Class 리팩토링을 위한 새로운 시스템 및 컴포넌트의 계약을 정의합니다.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Protocol, TypedDict, Deque, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.agents.government import Government
    from simulation.config import SimulationConfig
    from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner
    from simulation.metrics.economic_tracker import EconomicIndicatorTracker
    from simulation.dtos import GovernmentSensoryDTO, LeisureEffectDTO
    from simulation.markets.market import Market
    from simulation.dtos.scenario import StressScenarioConfig
    from simulation.dtos.api import SimulationState
    from simulation.models import Transaction
    from modules.household.dtos import LifecycleDTO
    from modules.finance.api import IFinancialEntity, IShareholderRegistry
    from simulation.systems.settlement_system import SettlementSystem
    from modules.government.taxation.system import TaxationSystem
    from logging import Logger

# ... [Keep Context TypedDicts and other interfaces unchanged] ...

class SystemInterface(Protocol):
    """
    WO-103: Common interface for system services to enforce the sacred sequence.
    """
    def execute(self, state: SimulationState) -> None:
        ...

# ... [Keep ISocialSystem, IEventSystem, ISensorySystem, ICommerceSystem, IAgentLifecycleComponent, IMarketComponent, ILaborMarketAnalyzer, ILearningAgent] ...

class AgentLifecycleManagerInterface(SystemInterface, Protocol):
    """
    Interface for AgentLifecycleManager to ensure contract compliance.
    """
    pass

class IMintingAuthority(Protocol):
    """
    Authority capable of creating or destroying money (Non-Zero-Sum).
    """
    def mint_and_transfer(self, target_agent: Any, amount: float, memo: str) -> bool:
        ...
    def transfer_and_burn(self, source_agent: Any, amount: float, memo: str) -> bool:
        ...

class IAccountingSystem(Protocol):
    def record_transaction(self, transaction: Transaction, buyer: Any, seller: Any, amount: float, tax_amount: float = 0.0) -> None:
        ...

class IRegistry(Protocol):
    def update_ownership(self, transaction: Transaction, buyer: Any, seller: Any, state: SimulationState) -> None:
        ...

class ISpecializedTransactionHandler(Protocol):
    def handle(self, transaction: Transaction, buyer: Any, seller: Any, state: SimulationState) -> bool:
        ...

# [DELETED] ITransactionManager
# Obsolete protocol. Logic has moved to TransactionProcessor (ITransactionProcessor or similar).

@dataclass(frozen=True)
class TransactionContext:
    """
    Provides all necessary simulation state to a transaction handler.
    """
    agents: Dict[int, Any]
    inactive_agents: Dict[int, Any]
    government: 'Government'
    settlement_system: 'SettlementSystem'
    taxation_system: 'TaxationSystem'
    stock_market: Any
    real_estate_units: List[Any]
    market_data: Dict[str, Any]
    config_module: Any
    logger: 'Logger'
    time: int
    bank: Optional[Any] 
    central_bank: Optional[Any] 
    public_manager: Optional[Any] 
    transaction_queue: List['Transaction'] 
    shareholder_registry: Optional['IShareholderRegistry'] = None 

class ITransactionHandler(ABC):
    @abstractmethod
    def handle(self, tx: 'Transaction', buyer: Any, seller: Any, context: 'TransactionContext') -> bool:
        raise NotImplementedError
```

design/3_work_artifacts/specs/phase23_hygiene_execution_spec.md
```markdown
# Spec: Phase 23 Master Hygiene Execution

## 1. Introduction
This specification outlines the execution plan for **Mission Phase 23 Hygiene**, focusing on modernizing the test suite, resolving legacy API drift, and hardening the `SimulationState` DTO. These changes are critical for eliminating technical debt identified in the `TECH_DEBT_LEDGER.md`.

## 2. Scope
- **DTO Hardening**: Update `SimulationState` to align with `WorldState` (multi-government support).
- **Import Resolution**: Eliminate stale imports of `HouseholdFactory`.
- **API Cleanup**: Remove `ITransactionManager` and deprecate `TaxAgency.collect_tax`.
- **Test Modernization**: Refactor tests to use `execute()` and `SettlementSystem` instead of private methods.

## 3. Detailed Changes

### 3.1. DTO & WorldState Alignment
**File**: `simulation/dtos/api.py`
- **Refactor**: `SimulationState`
    - Rename `government` -> `primary_government` (Type: `Any`).
    - Add `governments` (Type: `List[Any]`, Default: `[]`).
    - Rename `god_commands` -> `god_command_snapshot`.
    - **Impact**: All systems accessing `state.government` must be updated to `state.primary_government`.

**File**: `simulation/orchestration/tick_orchestrator.py`
- **Logic Update**:
    - Instantiate `SimulationState` mapping `ws.governments` to `governments`.
    - Map `ws.government` (Singleton) to `primary_government`.
    - Map `ws.god_command_queue` to `god_command_snapshot`.

### 3.2. Legacy Import Resolution
**File**: `simulation/systems/demographic_manager.py` & `simulation/initialization/initializer.py`
- **Change**: `from simulation.factories.agent_factory import HouseholdFactory` -> `from simulation.factories.household_factory import HouseholdFactory`.
- **Cleanup**: Delete `simulation/factories/agent_factory.py` if empty.

### 3.3. API Cleanup
**File**: `simulation/systems/api.py`
- **Delete**: `ITransactionManager` (Protocol). It is superseded by `TransactionProcessor` logic.

**File**: `simulation/systems/tax_agency.py`
- **Deprecate**: `collect_tax` -> `_legacy_collect_tax`.
- **Constraint**: Add `logger.warning` to `_legacy_collect_tax` indicating deprecation.
- **Reference**: Docstrings must point to `SettlementSystem.transfer` for new implementations.

### 3.4. Test Modernization
**Target Files**: `tests/system/test_engine.py`, `scripts/audit_zero_sum.py`, `tests/integration/test_tick_normalization.py`
- **Action**:
    - Replace `sim.lifecycle_manager._handle_agent_liquidation(state)` with `sim.lifecycle_manager.execute(state)`.
    - Replace `state.government` access with `state.primary_government` in mocks and assertions.
    - Rename `system_command_queue` (deque) mocks to `system_commands` (list) in `test_tick_normalization.py` and `test_state_synchronization.py`.

## 4. Verification Plan (Testing)

### 4.1. Static Analysis
- **Imports**: Verify no circular imports introduced by `SimulationState` changes.
- **Typing**: `mypy` check on `SimulationState` field types.

### 4.2. Runtime Verification
- **Test Suite**: Run `pytest tests/` to confirm:
    - 893 tests pass (baseline).
    - `AttributeError: 'SimulationState' object has no attribute 'government'` does NOT occur (verify renaming propagation).
- **Audit Script**: Run `python scripts/audit_zero_sum.py` to verify:
    - Liquidation logic functions correctly via `execute()`.
    - No Zero-Sum violations.

## 5. Risk Assessment
- **Breaking Change**: `government` -> `primary_government` rename is a high-risk breaking change.
- **Mitigation**: Use `grep` to locate all `state.government` usages and update them in a single atomic commit.
- **Fallback**: If too many breakages occur, alias `government = primary_government` property in `SimulationState` temporarily (Phase 23.5), but prefer strict renaming for Phase 23.

## 6. Reporting
- Create `communications/insights/modernize-test-and-legacy-api.md` with execution results and `pytest` logs.
```