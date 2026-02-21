"""
modules/system/api.py
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable, TypedDict
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Core Identifiers & Enums
# -----------------------------------------------------------------------------

# Strict Integer Typing for Agent IDs
AgentID = int

class SystemAgentID(IntEnum):
    """
    Reserved Agent IDs for System-Level Singletons.
    Range 0-99 is reserved for system use.
    """
    CENTRAL_BANK = 0
    GOVERNMENT = 1
    PUBLIC_MANAGER = 2
    SYSTEM_SINK = 99  # For burned assets/void

# Standard Currency Code
CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode = "USD"

# -----------------------------------------------------------------------------
# DTOs & Snapshots
# -----------------------------------------------------------------------------

@dataclass
class MarketContextDTO:
    """
    Context object passed to agents for making decisions.
    Contains strictly external market data (prices, rates, signals).
    """
    market_data: Dict[str, Any]
    market_signals: Dict[str, int]
    tick: int
    exchange_rates: Optional[Dict[str, float]] = None

@dataclass(frozen=True)
class MarketSignalDTO:
    market_id: str
    item_id: str
    best_bid: Optional[int]
    best_ask: Optional[int]
    last_traded_price: Optional[int]
    last_trade_tick: int
    price_history_7d: List[int]
    volatility_7d: float
    order_book_depth_buy: int
    order_book_depth_sell: int
    total_bid_quantity: float
    total_ask_quantity: float
    is_frozen: bool

@dataclass(frozen=True)
class HousingMarketUnitDTO:
    unit_id: str
    price: int
    quality: float
    rent_price: Optional[int] = None

@dataclass(frozen=True)
class HousingMarketSnapshotDTO:
    for_sale_units: List[HousingMarketUnitDTO]
    units_for_rent: List[HousingMarketUnitDTO]
    avg_rent_price: float
    avg_sale_price: float

@dataclass(frozen=True)
class LoanMarketSnapshotDTO:
    interest_rate: float

@dataclass(frozen=True)
class LaborMarketSnapshotDTO:
    avg_wage: float

@dataclass(frozen=True)
class MarketSnapshotDTO:
    """
    A pure-data snapshot of the state of all markets at a point in time.
    """
    tick: int
    market_signals: Dict[str, MarketSignalDTO]
    market_data: Dict[str, Any]
    housing: Optional[HousingMarketSnapshotDTO] = None
    loan: Optional[LoanMarketSnapshotDTO] = None
    labor: Optional[LaborMarketSnapshotDTO] = None

class AgentBankruptcyEventDTO(TypedDict):
    agent_id: int
    tick: int
    inventory: Dict[str, float]

@dataclass(frozen=True)
class PublicManagerReportDTO:
    tick: int
    newly_recovered_assets: Dict[str, float]
    liquidation_revenue: Dict[str, int]
    managed_inventory_count: float
    system_treasury_balance: Dict[str, int]

# -----------------------------------------------------------------------------
# Configuration Registry Types
# -----------------------------------------------------------------------------

class OriginType(IntEnum):
    """
    Priority Level for Parameter Updates.
    Higher value = Higher Priority.
    """
    SYSTEM = 0          # Internal logic (Hardcoded defaults)
    CONFIG = 10         # Loaded from file (User Configuration)
    USER = 50           # Dashboard/UI manual override
    GOD_MODE = 100      # Absolute override (Scenario Injection)

class RegistryValueDTO(BaseModel):
    """
    Data Transfer Object for Registry Values.
    Replaces the legacy RegistryEntry dataclass.
    """
    key: str
    value: Any
    domain: str = "global"
    origin: OriginType
    is_locked: bool = False
    last_updated_tick: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

RegistryEntry = RegistryValueDTO

class RegistryObserver(Protocol):
    def on_registry_update(self, key: str, value: Any, origin: OriginType) -> None:
        ...

@runtime_checkable
class IConfigurationRegistry(Protocol):
    """
    Interface for the Global Registry acting as the Single Source of Truth (SSoT).
    """
    def get(self, key: str, default: Any = None) -> Any:
        ...

    def set(self, key: str, value: Any, origin: OriginType = OriginType.USER) -> None:
        ...

    def snapshot(self) -> Dict[str, Any]:
        ...

    def reset_to_defaults(self) -> None:
        ...

@runtime_checkable
class IGlobalRegistry(Protocol):
    """
    Interface for the Global Parameter Registry.
    FOUND-01: Centralized Configuration Management.
    """
    def get(self, key: str, default: Any = None) -> Any:
        ...

    def set(self, key: str, value: Any, origin: OriginType = OriginType.CONFIG) -> bool:
        ...

    def lock(self, key: str) -> None:
        ...

    def unlock(self, key: str) -> None:
        ...

    def subscribe(self, observer: RegistryObserver, keys: Optional[List[str]] = None) -> None:
        ...

    def snapshot(self) -> Dict[str, RegistryValueDTO]:
        ...

    def get_metadata(self, key: str) -> Any:
        ...

    def get_entry(self, key: str) -> Optional[RegistryValueDTO]:
        ...

@runtime_checkable
class IRestorableRegistry(IGlobalRegistry, Protocol):
    """
    Extended interface for Registries that support state restoration/undo operations.
    """
    def delete_entry(self, key: str) -> bool:
        ...

    def restore_entry(self, key: str, entry: RegistryValueDTO) -> bool:
        ...

@runtime_checkable
class IProtocolEnforcer(Protocol):
    def assert_implements_protocol(self, instance: Any, protocol: Any) -> None:
        ...

# -----------------------------------------------------------------------------
# System Interfaces
# -----------------------------------------------------------------------------

class IAgentRegistry(Protocol):
    def get_agent(self, agent_id: AgentID) -> Any:
        ...

    def get_all_financial_agents(self) -> List[Any]:
        ...

    def set_state(self, state: Any) -> None:
        ...

@runtime_checkable
class ICurrencyHolder(Protocol):
    """
    Protocol for agents/systems that hold currency.
    Used for M2 Money Supply calculation.
    """
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        ...

    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        ...

@runtime_checkable
class IAssetRecoverySystem(Protocol):
    """
    Interface for the Public Manager acting as a receiver of assets.
    """
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        ...

    def receive_liquidated_assets(self, inventory: Dict[str, float]) -> None:
        ...

    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> List[Any]:
        ...
```

```markdown
# Specification: Fix System Agent Registration & ID Standardization

## 1. Introduction

- **Mission Key**: `spec-fix-sys-registry`
- **Objective**: Resolve critical initialization defects where System Agents (Central Bank, Public Manager) are excluded from the main `sim.agents` registry, leading to runtime failures in settlement and liquidation. This spec also standardizes System Agent IDs to a reserved integer block (0-99).
- **Scope**:
    - `modules/system/constants.py`
    - `modules/system/api.py`
    - `modules/system/registry.py`
    - `simulation/initialization/initializer.py`
- **Status**: DRAFT (Pending Review)

## 2. Problem Statement

### 2.1. Registration Gaps (TD-CRIT-SYS0-MISSING, TD-CRIT-PM-MISSING)
Current logic in `SimulationInitializer` instantiates `CentralBank` and `PublicManager` but fails to insert them into the `sim.agents` dictionary. This causes `AgentRegistry.get_agent(id)` to return `None` for these agents, leading to crashes in:
- `SettlementSystem.transfer()`: "Source account does not exist: 0"
- `EscheatmentHandler`: Cannot lookup Public Manager to transfer liquidated assets.

### 2.2. Registry Hack
`AgentRegistry` currently employs a "stringly-typed" fallback (`if agent_id == "government"`) to find the government agent. This is brittle and violates the Single Source of Truth (SSoT) principle.

### 2.3. ID Type Confusion
The system mixes `int` IDs (Agents/Firms) and `str` IDs ("government"). `AgentID` is defined as `int` in API docs but violated in implementation.

## 3. Detailed Solution

### 3.1. Constant Standardization (`modules/system/constants.py`)
Define a strict integer block for system agents.

```python
# System Agent IDs (Reserved 0-99)
ID_CENTRAL_BANK = 0
ID_GOVERNMENT = 1
ID_PUBLIC_MANAGER = 2
ID_SYSTEM_SINK = 99

# Reserved Block Range
ID_RESERVED_BLOCK_START = 0
ID_RESERVED_BLOCK_END = 99
```

### 3.2. Initializer Logic Update (`simulation/initialization/initializer.py`)
Refactor `build_simulation` to explicitly register system agents and enforce ID reservation.

**Pseudo-Code Logic:**

```python
def build_simulation(self) -> Simulation:
    # ... (Locking & Registry Init) ...

    # 1. Initialize System Agents with Fixed IDs
    sim.central_bank = CentralBank(id=ID_CENTRAL_BANK, ...)
    sim.government = Government(id=ID_GOVERNMENT, ...)
    sim.public_manager = PublicManager(id=ID_PUBLIC_MANAGER, ...)
    
    # 2. Initialize Commercial Bank (Next available or Fixed?)
    # Commercial Bank is technically an agent, but foundational. 
    # Let's give it dynamic allocation OR a reserved slot if it's a singleton.
    # Current: sim.bank.id = sim.next_agent_id
    
    # 3. Explicit Registry Insertion (THE FIX)
    sim.agents = {}
    sim.agents[ID_CENTRAL_BANK] = sim.central_bank
    sim.agents[ID_GOVERNMENT] = sim.government
    sim.agents[ID_PUBLIC_MANAGER] = sim.public_manager
    
    # 4. Initialize Households & Firms (Dynamic Allocation)
    # Start dynamic allocation AFTER the reserved block
    sim.next_agent_id = 100 
    
    # Re-map households/firms if they came in with pre-assigned IDs < 100?
    # Assumption: Newly created agents will use sim.next_agent_id. 
    # Existing households passed in __init__ might need re-indexing if they conflict, 
    # but usually they are 0-indexed. 
    # CRITICAL: If households are passed in with IDs 0, 1, 2... they will COLLIDE.
    # STRATEGY: Re-assign IDs for initial population if they collide with reserved block.
    
    current_dynamic_id = 100
    
    # Register Households
    for h in self.households:
        h.id = current_dynamic_id
        sim.agents[h.id] = h
        current_dynamic_id += 1
        
    # Register Firms
    for f in self.firms:
        f.id = current_dynamic_id
        sim.agents[f.id] = f
        current_dynamic_id += 1
        
    sim.next_agent_id = current_dynamic_id
    
    # ... (Bank initialization logic using current_dynamic_id) ...
    # sim.bank = Bank(id=current_dynamic_id, ...)
    # sim.agents[sim.bank.id] = sim.bank
    # sim.next_agent_id += 1

    # ... (Rest of initialization) ...
```

### 3.3. Registry Clean-up (`modules/system/registry.py`)
Remove the fallback logic. `AgentRegistry` becomes a pure look-up proxy.

```python
def get_agent(self, agent_id: AgentID) -> Optional[Agent]:
    if self._state is None:
        return None
    return self._state.agents.get(agent_id) # Pure dictionary lookup
```

## 4. Impact Analysis & Risk

### 4.1. Risks
- **ID Collision**: Existing serialized runs (DB) might have households with IDs 0, 1, 2. Loading these runs might conflict with CentralBank(0).
    - *Mitigation*: This change primarily affects *new* simulation runs (`build_simulation`). Loading legacy runs is handled by `PersistenceManager`, which might need a migration strategy later. For now, this spec focuses on clean genesis.
- **String ID Regressions**: Any code performing `if agent.id == "government"` will break.
    - *Mitigation*: Grep codebase for `"government"` literal usage and replace with `ID_GOVERNMENT` constant or `SystemAgentID.GOVERNMENT` enum.

### 4.2. Dependencies
- **SettlementSystem**: Relies on `AgentRegistry`. Fixing the registry fixes `TD-CRIT-SYS0-MISSING`.
- **EscheatmentHandler**: Relies on Public Manager lookup. Fixing registration fixes `TD-CRIT-PM-MISSING`.

## 5. Verification Plan

### 5.1. New Test Cases (`tests/test_initialization_fix.py`)
1.  **System Agent Lookup**:
    - `sim = initializer.build_simulation()`
    - `assert sim.agent_registry.get_agent(0) is sim.central_bank`
    - `assert sim.agent_registry.get_agent(1) is sim.government`
    - `assert sim.agent_registry.get_agent(2) is sim.public_manager`
2.  **ID Safety**:
    - Verify no household or firm has ID < 100.
    - Verify `sim.next_agent_id` >= 100.
3.  **Settlement Integration**:
    - Perform a transfer from Central Bank (0) to a Household. Ensure it passes without "Source account not found".

### 5.2. Legacy Test Impact
- Existing tests mocking `Government` with string ID might fail.
- **Action**: Update `tests/conftest.py` or relevant test fixtures to use integer IDs for system agents.

## 6. Mandatory Reporting

> **[INSIGHT]**: This task requires creating `communications/insights/spec-fix-sys-registry.md`.
> Record:
> 1. Locations of "government" string replacement.
> 2. Confirmation that `AgentRegistry` hack was removed.
> 3. Full pytest output demonstrating stability.