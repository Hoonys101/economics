modules/simulation/api.py
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable, TypedDict
from dataclasses import dataclass, field
from enum import Enum, auto

# ==============================================================================
# Domain Types
# ==============================================================================
AgentID = Union[int, str]  # Transitioning to int, legacy str support
CurrencyCode = str

# ==============================================================================
# Lifecycle Protocols (Module C)
# ==============================================================================

class LifecycleState(Enum):
    """
    Strict lifecycle states for Agents to prevent Zombie/Ghost entities.
    """
    PENDING = auto()    # Reserved ID, Instance created, but not Simulation-ready
    ACTIVE = auto()     # Fully registered, funded, and ticking
    SUSPENDED = auto()  # Temporarily disabled (e.g., during Saga execution)
    BANKRUPT = auto()   # Insolvency process started
    LIQUIDATED = auto() # Removed from Simulation, kept for history
    ZOMBIE = auto()     # Error state (Registry mismatch)

@dataclass
class AgentRegistrationDTO:
    """
    DTO for atomic agent registration.
    """
    agent_id: AgentID
    agent_type: str
    initial_state: LifecycleState
    config: Dict[str, Any]
    parent_id: Optional[AgentID] = None

@runtime_checkable
class ILifecycleAware(Protocol):
    """
    Protocol for agents that react to lifecycle events.
    """
    @property
    def lifecycle_state(self) -> LifecycleState:
        ...

    def on_spawn(self, context: Any) -> None:
        """Called immediately after instantiation (PENDING state)."""
        ...

    def on_activate(self) -> None:
        """Called after successful registration and funding (ACTIVE state)."""
        ...

    def on_destroy(self, reason: str) -> None:
        """Called before removal (LIQUIDATED state)."""
        ...

@runtime_checkable
class ILifecycleRegistry(Protocol):
    """
    Protocol for the Central Registry handling Atomic Onboarding.
    """
    def reserve_id(self, agent_type: str) -> AgentID:
        """Generates and reserves a unique ID."""
        ...

    def register_agent(self, agent: Any, state: LifecycleState = LifecycleState.PENDING) -> bool:
        """Adds agent to the registry in PENDING state."""
        ...

    def activate_agent(self, agent_id: AgentID) -> bool:
        """Transitions agent to ACTIVE state, enabling ticks."""
        ...

    def purge_agent(self, agent_id: AgentID) -> None:
        """Hard removal for rollback scenarios (Ghost busting)."""
        ...

# ==============================================================================
# Financial Protocols (Strict Typing)
# ==============================================================================

@runtime_checkable
class IFinancialEntity(Protocol):
    """
    Strict protocol for entities participating in financial transactions.
    Replaces loose `hasattr` checks in Bank/Settlement.
    """
    @property
    def id(self) -> AgentID:
        ...
    
    @property
    def assets(self) -> Dict[CurrencyCode, int]:
        # Enforcing Penny Standard (int)
        ...

    def get_balance(self, currency: CurrencyCode = "USD") -> int:
        ...

    def deposit(self, amount: int, currency: CurrencyCode = "USD") -> None:
        ...

    def withdraw(self, amount: int, currency: CurrencyCode = "USD") -> bool:
        ...

    # Transactional Safety
    def prepare_transaction(self, tx_id: str, amount: int) -> bool:
        """Locks funds/assets for a pending transaction."""
        ...

    def commit_transaction(self, tx_id: str) -> None:
        """Finalizes the transaction."""
        ...

    def rollback_transaction(self, tx_id: str) -> None:
        """Releases locks on failure."""
        ...

# ==============================================================================
# Saga Protocols & DTOs
# ==============================================================================

@dataclass
class SagaParticipantDTO:
    """
    Normalized DTO for Saga participants.
    Resolves TD-FIN-SAGA-ORPHAN.
    """
    agent_id: AgentID
    role: str  # "BUYER", "SELLER", "BROKER"
    financial_interface: Optional[IFinancialEntity] = None # For direct access if allowed
    context: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        return self.agent_id is not None

@dataclass
class HousingTransactionSagaStateDTO:
    """
    Standardized State for Housing Sagas.
    """
    saga_id: str
    step: int
    buyer: SagaParticipantDTO
    seller: SagaParticipantDTO
    property_id: str
    price: int # Pennies
    status: str # "INIT", "RESERVED", "PAID", "TRANSFERRED", "FAILED", "COMPLETED"
    logs: List[str] = field(default_factory=list)
    rollback_stack: List[str] = field(default_factory=list)

# ==============================================================================
# Simulation Core API
# ==============================================================================

@dataclass
class EconomicIndicatorsDTO:
    """Snapshot of economic health."""
    run_id: int
    time: int
    unemployment_rate: float
    avg_wage: float
    total_production: float
    total_consumption: int
    inflation_rate: Optional[float] = None
    gini_index: Optional[float] = None

@dataclass
class AgentCoreConfigDTO:
    id: AgentID
    name: str
    value_orientation: str
    initial_needs: Dict[str, float]
    logger: Any
    memory_interface: Any

class IAgent(ABC):
    """Base Abstract Class for all Agents."""
    
    @property
    @abstractmethod
    def id(self) -> AgentID:
        ...

    @property
    @abstractmethod
    def is_active(self) -> bool:
        ...
```

design/3_work_artifacts/specs/mod_lifecycle_spec.md
```markdown
# Module C Spec: Lifecycle & Saga Reliability

## 1. Introduction
- **Module**: Lifecycle Management (Module C)
- **Objective**: Resolve critical race conditions in Agent spawning (`TD-ARCH-STARTUP-RACE`) and fragile type handling in Sagas (`TD-FIN-SAGA-ORPHAN`).
- **Key Deliverables**: 
  1. Atomic Onboarding Protocol (Registration before Funding).
  2. Strict `IFinancialEntity` Protocol (Removing `hasattr`).
  3. `SagaParticipantDTO` Normalization.

## 2. Architectural Changes

### 2.1. Atomic Onboarding Protocol (Fixing TD-ARCH-STARTUP-RACE)
Currently, `FirmSystem` instantiates a firm and attempts to transfer capital *before* the firm is fully registered in the `Simulation` and `Bank`. This causes `SettlementSystem` failures.

**New Workflow:**
1.  **Reserve**: `LifecycleRegistry` generates a guaranteed unique `AgentID`.
2.  **Instantiate**: Create `Firm` instance in `LifecycleState.PENDING`.
3.  **Register (Soft)**: Add to `simulation.agents` and `bank.accounts` (marked PENDING/INACTIVE).
    - *Crucial*: Bank account must be open to receive funds.
4.  **Fund**: Execute `SettlementSystem.transfer(founder, new_firm)`.
5.  **Commit/Rollback**:
    - *Success*: Update state to `LifecycleState.ACTIVE`.
    - *Failure*: Call `purge_agent(id)` to remove from all registries and close bank account.

### 2.2. Strict Financial Protocol (Fixing TD-INT-BANK-ROLLBACK)
Deprecate `hasattr(agent, 'rollback')`. All agents participating in finance must implement `IFinancialEntity`.

**Protocol Requirement:**
- `prepare_transaction(tx_id, amount)`: Locks funds.
- `commit_transaction(tx_id)`: Consumes locked funds.
- `rollback_transaction(tx_id)`: Releases locks.

### 2.3. Saga Normalization (Fixing TD-FIN-SAGA-ORPHAN)
The `SagaOrchestrator` currently guesses agent IDs from dictionaries. This must be replaced with `SagaParticipantDTO`.

**Constraint:**
- `SagaOrchestrator` inputs must be converted to `HousingTransactionSagaStateDTO` *at the entry gate*.
- No logic within the Saga should access raw dictionaries for `buyer_id` or `seller_id`.

## 3. Implementation Plan

### 3.1. API & DTO Updates (`modules/simulation/api.py`)
- Define `LifecycleState` Enum.
- Define `ILifecycleRegistry` Protocol.
- Define `IFinancialEntity` Protocol.
- Define `SagaParticipantDTO`.

### 3.2. Refactoring `FirmSystem.spawn_firm`
- **Logic**:
  ```python
  def spawn_firm(self, simulation, founder):
      # 1. Reserve
      firm_id = simulation.registry.reserve_id("FIRM")
      
      # 2. Instantiate (Pending)
      firm = Firm(id=firm_id, state=LifecycleState.PENDING, ...)
      
      # 3. Atomic Registration Context
      try:
          simulation.register_agent(firm) # Adds to agents dict
          simulation.bank.open_account(firm) # Explicit Account Opening
          
          # 4. Fund
          success = settlement.transfer(founder, firm, amount)
          
          if success:
              firm.on_activate()
              simulation.registry.activate_agent(firm.id)
              return firm
          else:
              raise FundingError("Transfer failed")
              
      except Exception:
          # 5. Rollback
          simulation.registry.purge_agent(firm.id)
          simulation.bank.close_account(firm.id)
          return None
  ```

### 3.3. Refactoring `Bank` and `TransactionProcessor`
- Replace `hasattr` checks with `isinstance(agent, IFinancialEntity)`.
- Ensure `Household` and `Firm` classes implement the `IFinancialEntity` methods (even if stubs for now).

## 4. Verification & Testing

### 4.1. New Test Cases
- **`test_firm_startup_rollback`**:
    - Mock `settlement.transfer` to return `False`.
    - Assert `firm.id` is NOT present in `simulation.agents` after call.
    - Assert `bank.accounts` does not contain `firm.id`.
- **`test_saga_participant_validation`**:
    - Pass invalid DTO (missing ID) to Saga.
    - Assert immediate `ValueError` or `SAGA_REJECT`.

### 4.2. Impact on Existing Tests
- **`test_firm_management.py`**: Will fail because mocks expect "fire and forget" creation. Mocks must be updated to simulate the "Open Account" step.
- **`test_transaction_engine.py`**: Any mock agents used here must be updated to use `spec=IFinancialEntity` or implement `prepare/commit/rollback`.

## 5. Technical Debt Analysis
- **Resolved**: `TD-ARCH-STARTUP-RACE`, `TD-FIN-SAGA-ORPHAN`, `TD-INT-BANK-ROLLBACK`.
- **Introduced Risk**: Strict typing might expose latent bugs in `Government` or `System` agents if they don't conform to `IFinancialEntity` (e.g., `PublicManager`).
- **Mitigation**: Ensure `PublicManager` implements `IFinancialEntity`.

## 6. Audit & Reporting
- All changes must be logged to `communications/insights/mod-lifecycle-spec.md`.
- Run full regression suite: `pytest tests/`.
```