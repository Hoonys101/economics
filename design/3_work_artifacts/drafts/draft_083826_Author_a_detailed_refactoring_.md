# Refactoring Specification: Household Decomposition and Market Decoupling

- **Author**: Scribe (Gemini)
- **Date**: 2026-02-04
- **Related Tech Debt**: TD-214, TD-215, TD-216, TD-217

---

## 1. Project Overview

### 1.1. Goal
This specification outlines the refactoring plan to address critical architectural debt identified in the "God Class & Abstraction Leak" audit. The primary objectives are:
1.  **Decompose the `Household` God Class** (`TD-214`): To improve maintainability and isolate concerns by breaking the monolithic class into logical, reusable components (mixins).
2.  **Decouple Market Handlers** (`TD-215`): To eliminate tight coupling between market logic and concrete agent implementations by introducing shared interfaces (`Protocols`).
3.  **Clean Up Orchestrator Logic** (`TD-216`): To improve separation of concerns by moving agent-specific logic from the `TickOrchestrator` into dedicated Phases.
4.  **Enforce Encapsulation** (`TD-217`): To remove protected member access violations by services, ensuring components interact via public, stable APIs.

### 1.2. Scope
-   **In Scope**:
    -   Refactoring `simulation/core_agents.py` (`Household` class).
    -   Creating a new `modules/household/mixins` package.
    -   Creating a new `modules/common/interfaces.py` for shared agent protocols.
    -   Refactoring `modules/market/handlers/housing_transaction_handler.py`.
    -   Refactoring `modules/housing/service.py`.
    -   Refactoring `modules/household/services.py` (`HouseholdSnapshotAssembler`).
    -   Refactoring `simulation/orchestration/tick_orchestrator.py` and its associated Phase classes.
-   **Out of Scope**:
    -   Changing the public-facing API (properties and methods) of the `Household` class.
    -   Introducing new features or business logic.

---

## 2. Detailed Design & Implementation Plan

### 2.1. Household God Class Decomposition (TD-214, TD-217)

The `Household` class, exceeding 970 lines, will be decomposed internally using mixins. The public contract of the class will remain unchanged to prevent cascading failures.

#### 2.1.1. Phase 1: Create Household Mixins
A new package `modules/household/mixins/` will be created. The logic from `Household` will be partitioned into the following mixin classes:

1.  **`_properties.py` -> `HouseholdPropertiesMixin`**:
    -   **Responsibility**: Contains all property getters and setters (`@property`, `@x.setter`) for `assets`, `inventory`, `needs`, `is_active`, `age`, `is_homeless`, etc.
    -   **Purpose**: Isolates the facade layer that maintains backward compatibility with the rest of the codebase.

2.  **`_lifecycle.py` -> `HouseholdLifecycleMixin`**:
    -   **Responsibility**: Manages the agent's state changes over time.
    -   **Methods**: `update_needs`, `consume`, `apply_leisure_effect`, `update_perceived_prices`.

3.  **`_financials.py` -> `HouseholdFinancialsMixin`**:
    -   **Responsibility**: Handles direct financial operations.
    -   **Methods**: `adjust_assets`, `modify_inventory`, `_internal_add_assets`, `_internal_sub_assets`, `add_labor_income`, `trigger_emergency_liquidation`.

4.  **`_reproduction.py` -> `HouseholdReproductionMixin`**:
    -   **Responsibility**: Manages cloning and inheritance.
    -   **Methods**: `clone`, `_create_new_decision_engine`, `get_heir`.

5.  **`_state_access.py` -> `HouseholdStateAccessMixin`**:
    -   **Responsibility**: Provides controlled, public access to internal state DTOs, resolving `TD-217`.
    -   **Methods**:
        -   `get_bio_state() -> BioStateDTO`
        -   `get_econ_state() -> EconStateDTO`
        -   `get_social_state() -> SocialStateDTO`
        -   `create_snapshot_dto() -> HouseholdSnapshotDTO`

#### 2.1.2. Phase 2: Refactor `Household` Class
The `Household` class in `simulation/core_agents.py` will be refactored to inherit from these mixins.

```python
# simulation/core_agents.py (Simplified)

from modules.household.mixins import (
    HouseholdPropertiesMixin,
    HouseholdLifecycleMixin,
    HouseholdFinancialsMixin,
    HouseholdReproductionMixin,
    HouseholdStateAccessMixin
)
# ... other imports

class Household(
    BaseAgent,
    ILearningAgent,
    IPortfolioHandler,
    IHeirProvider,
    HouseholdPropertiesMixin,
    HouseholdLifecycleMixin,
    HouseholdFinancialsMixin,
    HouseholdReproductionMixin,
    HouseholdStateAccessMixin
):
    """
    Household Agent (Facade).
    Delegates Bio/Econ/Social logic to specialized stateless components.
    Internal logic is organized into mixins.
    """
    def __init__(self, ...):
        # __init__ remains largely the same, setting up components and state DTOs.
        ...

    # The only methods remaining in the main class body will be those
    # that orchestrate across multiple components/mixins, like make_decision.
    def make_decision(self, ...) -> ...:
        ...

    # ... Other high-level orchestration methods
```

#### 2.1.3. Phase 3: Fix Protected Member Access (TD-217)
The `HouseholdSnapshotAssembler` will be modified to use the new public state accessors.

```python
# modules/household/services.py

class HouseholdSnapshotAssembler:
    @staticmethod
    def assemble(household: "Household") -> HouseholdSnapshotDTO:
        """
        Creates a snapshot DTO using the household's public state accessors.
        """
        # Access internal states via the new public methods
        bio_state_copy = household.get_bio_state().copy()
        econ_state_copy = household.get_econ_state().copy()
        social_state_copy = household.get_social_state().copy()

        return HouseholdSnapshotDTO(
            id=household.id,
            bio_state=bio_state_copy,
            econ_state=econ_state_copy,
            social_state=social_state_copy
        )
```

### 2.2. Market Handler Decoupling (TD-215)

We will introduce abstract protocols to decouple market systems from concrete agent implementations.

#### 2.2.1. Phase 1: Define Agent Protocols
A new file, `modules/common/interfaces.py`, will be created to house `runtime_checkable` protocols.

```python
# modules/common/interfaces.py

from typing import Protocol, List, Optional, Dict
from typing_extensions import runtime_checkable
from modules.system.api import CurrencyCode

@runtime_checkable
class IPropertyOwner(Protocol):
    """Defines an agent that can own real estate."""
    owned_properties: List[int]
    def add_property(self, property_id: int) -> None: ...
    def remove_property(self, property_id: int) -> None: ...

@runtime_checkable
class IResident(Protocol):
    """Defines an agent that can reside in a property."""
    residing_property_id: Optional[int]
    is_homeless: bool

@runtime_checkable
class IMortgageBorrower(Protocol):
    """Defines an agent eligible for a mortgage."""
    id: int
    assets: Dict[CurrencyCode, float]
    current_wage: float
    # Further methods like get_debt_status() can be added if needed by the bank.

# Household class in core_agents.py will implicitly satisfy these protocols.
```

#### 2.2.2. Phase 2: Refactor Market Handlers
The `HousingTransactionHandler` and `HousingService` will be updated to use these protocols instead of `isinstance(agent, Household)`.

```python
# modules/market/handlers/housing_transaction_handler.py

# Remove: from simulation.core_agents import Household
from modules.common.interfaces import IMortgageBorrower, IPropertyOwner

class HousingTransactionHandler(...):
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        # ...
        # is_household = isinstance(buyer, Household)
        use_mortgage = isinstance(buyer, IMortgageBorrower) and context.bank is not None
        # ...

# modules/housing/service.py

# Remove: from simulation.core_agents import Household
from modules.common.interfaces import IPropertyOwner, IResident

class HousingService(...):
    def _handle_housing_registry(self, tx: "Transaction", state: "SimulationState"):
        # ...
        if isinstance(buyer, IPropertyOwner):
            if unit_id not in buyer.owned_properties:
                buyer.owned_properties.append(unit_id)

        if isinstance(buyer, IResident):
            if buyer.residing_property_id is None:
                # ... auto-move-in logic
```

### 2.3. Orchestrator Decoupling (TD-216)

Agent-specific logic will be moved from the orchestrator into the appropriate phase classes to enforce separation of concerns.

1.  **`reset_tick_flow`**:
    -   **Action**: Move the call `state.government.reset_tick_flow()` from `TickOrchestrator.run_tick` into the `execute` method of `Phase0_PreSequence`.
    -   **Rationale**: This is a pre-tick setup action that belongs with other preparatory steps.

2.  **`process_monetary_transactions`**:
    -   **Action**: The call `sim_state.government.process_monetary_transactions(sim_state.transactions)` inside `TickOrchestrator._drain_and_sync_state` will be moved. It will be added to the `execute` method of `Phase3_Transaction`.
    -   **Rationale**: `Phase3_Transaction` is the primary phase for processing and finalizing transactions. While transactions can be generated in other phases, this move centralizes government accounting within the main transaction settlement phase, as recommended by the audit.
    -   **🚨 Risk Mitigation**: The audit notes a timing risk. This change means monetary base adjustments are recognized slightly later than before (but still within the same tick). This is an acceptable trade-off for architectural cleanliness. The impact will be monitored, and if timing issues arise, a dedicated `Phase_GovernmentalAccounting` to be run after each phase could be introduced as a future refinement.

```python
# simulation/orchestration/tick_orchestrator.py
def _drain_and_sync_state(self, sim_state: SimulationState):
    # ...
    # REMOVE THIS BLOCK
    # if sim_state.government and hasattr(sim_state.government, "process_monetary_transactions"):
    #     sim_state.government.process_monetary_transactions(sim_state.transactions)
    # ...

# simulation/orchestration/phases.py
class Phase3_Transaction(IPhaseStrategy):
    def execute(self, state: SimulationState) -> SimulationState:
        # ... existing transaction processing logic ...

        # ADD THIS BLOCK
        # TD-216: Centralize government monetary accounting.
        # This processes all transactions that have been queued so far in the tick.
        if state.government and hasattr(state.government, "process_monetary_transactions"):
            # Note: world_state.transactions contains all tx from previous phases
            # because _drain_and_sync_state moves them from sim_state.transactions.
            all_transactions_so_far = self.world_state.transactions + state.transactions
            state.government.process_monetary_transactions(all_transactions_so_far)

        # ... existing cleanup logic ...
        return state
```

## 3. Risk Assessment & Verification Plan

### 3.1. Architectural Risks
-   **API Drift**: The `Household` class's public API must be preserved. Any change, however small, could cause widespread test failures. All mixin methods must match the original signatures exactly.
-   **Timing Sensitivity**: As noted for `TD-216`, altering the sequence of government accounting could have subtle side effects on monetary aggregates. The first few simulation runs post-refactoring must be closely monitored for money supply anomalies.
-   **Incomplete Protocols**: The new `IPropertyOwner` and `IMortgageBorrower` protocols must be comprehensive. If a market handler requires a property or method not defined in the protocol, it will lead to runtime errors or a reversion to `hasattr` checks, defeating the purpose of the abstraction.

### 3.2. Verification Strategy
1.  **Unit & Integration Tests**: All existing tests must pass. New tests will be added to verify:
    -   The `HousingTransactionHandler` correctly processes transactions for a mock agent that implements `IMortgageBorrower` but is not a `Household`.
    -   `HouseholdSnapshotAssembler` correctly builds a snapshot without runtime errors.
2.  **Golden Run Comparison**: A full simulation run will be executed before and after the refactoring. Key macroeconomic outputs (GDP, inflation, unemployment, Gini coefficient) from the `tracker` will be compared. Any significant deviation (>\`0.1%\`) will be investigated as a potential regression.
3.  **Code Review**: Peer review will focus on ensuring the public API of `Household` remains identical and that no new `isinstance(..., Household)` checks are introduced.

---

## 4. Work Artifacts

### 4.1. New Files to be Created
1.  `modules/common/interfaces.py`: Defines the agent-facing protocols.
2.  `modules/household/mixins/__init__.py`
3.  `modules/household/mixins/_properties.py`
4.  `modules/household/mixins/_lifecycle.py`
5.  `modules/household/mixins/_financials.py`
6.  `modules/household/mixins/_reproduction.py`
7.  `modules/household/mixins/_state_access.py`

### 4.2. Communication & Reporting
-   A new Markdown file will be created in `communications/insights/` upon completion of this refactoring, detailing any challenges encountered, lessons learned, and confirming the resolution of the targeted tech debt items.
-   The `TECH_DEBT_LEDGER.md` will be updated to mark TD-214, TD-215, TD-216, and TD-217 as "Resolved" in the subsequent sprint review.
