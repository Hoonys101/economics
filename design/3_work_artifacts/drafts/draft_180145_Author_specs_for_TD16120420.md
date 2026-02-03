```markdown
# Spec: SRP Refactoring for Registry & Transaction Phases (TD-161, TD-204, TD-205)

## 1. Executive Summary

This specification outlines a major refactoring effort to resolve critical Single Responsibility Principle (SRP) violations in the simulation engine, as identified in technical debt tickets TD-161, TD-204, and TD-205. The primary goals are to:

1.  **Decompose the `Registry` "God Class"**: Extract all housing-related logic into a new, dedicated `HousingService`.
2.  **Decompose the `Phase3_Transaction` "God Phase"**: Break down the monolithic transaction generation phase into a sequence of smaller, cohesive, and domain-specific phases.
3.  **Enforce Data Object Purity**: Ensure `RealEstateUnit` and other models are pure data containers with no business logic.

This refactoring will improve modularity, testability, and maintainability, while strictly adhering to the project's core architectural constraints, especially regarding financial integrity.

## 2. Part 1: `Registry` Decomposition & `HousingService` Introduction (TD-161, TD-204)

The `simulation.systems.registry.Registry` class currently manages state for disparate domains like labor, goods, stocks, and real estate. This creates high coupling and makes the system brittle. We will extract all logic related to real estate and housing into a new `HousingService`.

### 2.1. New Module: `modules.housing`

A new module will be created at `modules/housing/` to encapsulate all housing-related logic.

-   `modules/housing/api.py`: Public interface (`IHousingService`).
-   `modules/housing/service.py`: Concrete implementation (`HousingService`).
-   `modules/housing/dtos.py`: (If necessary) DTOs specific to the housing domain.

### 2.2. API Specification: `IHousingService`

The `IHousingService` will be responsible for all state changes related to real estate assets.

**File**: `modules/housing/api.py`

```python
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from modules.finance.api import LienDTO
from simulation.dtos.api import SimulationState
from simulation.models import Transaction

class IHousingService(ABC):
    """
    Manages the lifecycle and state of all real estate and housing units.
    This service is the single source of truth for ownership, liens,
    and contractual status of properties.
    """

    @abstractmethod
    def process_transaction(self, tx: Transaction, state: SimulationState) -> None:
        """
        Primary entry point to process a housing-related transaction and update
        the state of real estate units, owners, and occupants.
        This replaces the logic previously in Registry._handle_housing_registry.
        """
        ...

    @abstractmethod
    def is_under_contract(self, property_id: int) -> bool:
        """Checks if a property is currently locked by a purchase saga."""
        ...

    @abstractmethod
    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Locks a property for a purchase saga."""
        ...

    @abstractmethod
    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Releases a property lock from a purchase saga."""
        ...

    @abstractmethod
    def add_lien(self, property_id: int, loan_id: str, lienholder_id: int, principal: float) -> Optional[str]:
        """Adds a lien (e.g., a mortgage) to a property."""
        ...

    @abstractmethod
    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        """Removes a lien from a property."""
        ...

    @abstractmethod
    def transfer_ownership(self, property_id: int, new_owner_id: int) -> bool:
        """Transfers ownership of a property."""
        ...
```

### 2.3. Refactoring `Registry`

The `Registry` class will be simplified, delegating housing-related logic to the new `HousingService`.

**File**: `simulation/systems/registry.py`

```python
# BEFORE (Simplified)
class Registry(IRegistry):
    def update_ownership(self, transaction: Transaction, ...):
        # ...
        elif tx_type == "housing":
            self._handle_housing_registry(...) # <-- Complex logic lives here
        # ...

    def _handle_housing_registry(...):
        # ... 30+ lines of logic ...

    def add_lien(...): # ...
    def remove_lien(...): # ...
    def set_under_contract(...): # ...
```

```python
# AFTER (Simplified)
# Imports: from modules.housing.api import IHousingService

class Registry(IRegistry):
    # Dependency injection of the new service
    def __init__(self, housing_service: IHousingService, ...):
        self.housing_service = housing_service
        # ... other initializations

    def update_ownership(self, transaction: Transaction, buyer: Any, seller: Any, state: SimulationState) -> None:
        tx_type = transaction.transaction_type

        if tx_type in ["labor", "research_labor"]:
            self._handle_labor_registry(...)
        elif tx_type == "goods":
            self._handle_goods_registry(...)
        elif tx_type == "stock":
            self._handle_stock_registry(...)
        # All housing-related logic is now delegated
        elif tx_type.startswith("real_estate_") or tx_type == "housing":
             # The new service handles the entire transaction context
             self.housing_service.process_transaction(transaction, state)
        # ... other transaction types

    # REMOVED: _handle_housing_registry
    # REMOVED: _handle_real_estate_registry
    # REMOVED: add_lien, remove_lien, transfer_ownership
    # REMOVED: is_under_contract, set_under_contract, release_contract
    # REMOVED: contract_locks, real_estate_units attributes
```

### 2.4. Data Object Purity: `RealEstateUnit`

The `RealEstateUnit` model will be refactored into a pure data object. Any methods containing business logic (e.g., calling the registry to check its own status) will be removed.

**File**: `simulation/housing.py` (or wherever `RealEstateUnit` is defined)

```python
# BEFORE
class RealEstateUnit:
    # ... attributes
    def is_under_contract(self, registry: IRegistry) -> bool:
        # VIOLATION: Data object calls a service to check its own state
        return registry.is_under_contract(self.id)

# AFTER
class RealEstateUnit:
    # ... attributes ONLY
    # NO METHODS with business logic. It is a pure data container.
```

## 3. Part 2: `Phase3_Transaction` Decomposition (TD-205)

`Phase3_Transaction` aggregates too many unrelated transaction-generation processes. It will be broken into smaller, more focused phases executed sequentially by the `TickOrchestrator`.

### 3.1. New Phase Strategies

The logic from `Phase3_Transaction` will be split into the following new phases:

1.  **`Phase_BankAndDebt`**: Handles bank interest/fees and agent debt servicing.
    -   `state.bank.run_tick(...)`
    -   `finance_system.service_debt(...)`
2.  **`Phase_FirmProductionAndSalaries`**: Handles core firm operations.
    -   `firm.generate_transactions(...)` (e.g., paying salaries)
3.  **`Phase_GovernmentPrograms`**: Handles all government spending programs.
    -   `government.run_welfare_check(...)`
    -   `government.invest_infrastructure(...)`
    -   `government.run_public_education(...)`
4.  **`Phase_TaxationIntents`**: Handles the generation of corporate tax obligations.
    -   `taxation_system.generate_corporate_tax_intents(...)`

### 3.2. `TickOrchestrator` Update

The orchestrator's tick sequence will be updated to call these new phases in order, replacing the single call to `Phase3_Transaction`.

```python
# In TickOrchestrator.run_tick()

# ... after Phase2_Matching ...

# --- START REFACTORED SEQUENCE ---
self._execute_phase(Phase_HousingSaga(self.world_state), sim_state)
self._execute_phase(Phase_BankAndDebt(self.world_state), sim_state)
self._execute_phase(Phase_FirmProductionAndSalaries(self.world_state), sim_state)
self._execute_phase(Phase_GovernmentPrograms(self.world_state), sim_state)
self._execute_phase(Phase_TaxationIntents(self.world_state), sim_state)
# --- END REFACTORED SEQUENCE ---

# The original transaction processing logic from the end of Phase3
# remains in place to process the aggregated transactions.
if self.world_state.transaction_processor:
    combined_txs = list(self.world_state.transactions) + list(sim_state.transactions)
    results = self.world_state.transaction_processor.execute(sim_state, transactions=combined_txs)
    # ...
```

## 4. 🚨 Risk & Impact Audit

### 4.1. CRITICAL: State Synchronization Integrity (TD-177/TD-192)

-   **Constraint**: The `TickOrchestrator`'s state draining process (`_drain_and_sync_state`) contains a direct, mid-cycle call to `sim_state.government.process_monetary_transactions(...)`.
-   **Reason**: This is a **NON-NEGOTIABLE ARCHITECTURAL CONSTRAINT** required for the M2 money supply integrity check (TD-177). It ensures the government's monetary delta is calculated incrementally, which is fundamental to end-of-tick financial audits.
-   **Mandate**: **DO NOT REFACTOR OR REMOVE THIS CALL.** Any attempt to "purify" the state sync process by deferring this logic will break financial validation and re-introduce money leak bugs. This specific, intentional protocol violation must be preserved.

### 4.2. Dependency & Integration

-   The `WorldState` or equivalent top-level container must be updated to instantiate and hold a reference to the new `HousingService`.
-   The `Registry`'s constructor must be updated to accept the `IHousingService` via dependency injection.
-   The `TickOrchestrator`'s phase list must be updated to reflect the new phase sequence.

### 4.3. Testing Impact

-   **`Registry` Tests**: Unit tests for `Registry` that cover housing, real estate, and liens must be moved and adapted to become unit tests for the new `HousingService`.
-   **`Phase3_Transaction` Tests**: Integration tests that relied on the behavior of `Phase3_Transaction` must be broken down to test the new, smaller phases individually and sequentially.
-   **New Tests**: New unit tests must be written for each of the new phases (`Phase_BankAndDebt`, `Phase_GovernmentPrograms`, etc.) to ensure they correctly generate their respective transactions.
-   **`RealEstateUnit` Tests**: Any tests that asserted behavior on `RealEstateUnit` methods must be removed or refactored to test the `HousingService`'s manipulation of the `RealEstateUnit` data object.
```
