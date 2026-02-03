# Lien and Contract Status Specification

## 1. Introduction

This document specifies the data structures and interfaces required to add a robust lien tracking system to the `RealEstateUnit` model. The design addresses critical architectural risks identified in the pre-flight audit, including DTO duplication, state management redundancy, and backward compatibility.

The core of this proposal is to:
1.  Introduce a `LienDTO` and a `liens` list on `RealEstateUnit` to support multiple encumbrances.
2.  Deprecate the direct `mortgage_id` field in favor of a backward-compatible property.
3.  Eliminate state synchronization risks by making the `is_under_contract` status a derived property, with the `HousingTransactionSaga` as the single source of truth.
4.  Resolve DTO definition conflicts by centralizing financial DTOs.

## 2. Interface Specification (`api.py`)

The following DTOs and interfaces will be defined in `modules/finance/api.py` to centralize financial data structures and contracts.

```python
# file: modules/finance/api.py

from typing import TypedDict, List, Optional, Literal
from abc import ABC, abstractmethod

# --- Lien and Encumbrance DTOs ---

class LienDTO(TypedDict):
    """
    Represents a financial claim (lien) against a real estate property.
    This is the canonical data structure for all property-secured debt.
    """
    loan_id: int
    lienholder_id: int  # The ID of the agent/entity holding the lien (e.g., the bank)
    principal_remaining: float
    lien_type: Literal["MORTGAGE", "TAX_LIEN", "JUDGEMENT_LIEN"]


# --- Interfaces for Data Access ---

class IRealEstateRegistry(ABC):
    """
    An interface for querying the state of real estate assets,
    decoupling models from business logic.
    """
    @abstractmethod
    def is_under_contract(self, property_id: int) -> bool:
        """
        Checks if a property is currently involved in an active purchase Saga.
        This is the single source of truth for the "under contract" status.

        Implementation Note: This method should query the Saga persistence layer
        for any non-terminal Saga state associated with the property_id.
        """
        ...

class ISagaRepository(ABC):
    """
    Interface for querying the state of active Sagas.
    """
    @abstractmethod
    def find_active_saga_for_property(self, property_id: int) -> Optional[dict]:
        """
        Finds an active (non-completed, non-failed) housing transaction saga
        for a given property ID. Returns the saga state DTO if found, else None.
        """
        ...
```

## 3. Data Model & Logic (`simulation/models.py`)

The `RealEstateUnit` dataclass in `simulation/models.py` will be modified as follows. Direct mutation of the `liens` list should be avoided; changes should be handled by a dedicated manager or service.

```python
# file: simulation/models.py (Proposed Changes)

from dataclasses import dataclass, field
from typing import Optional, List

# Assumes IRealEstateRegistry is available via dependency injection
# from modules.finance.api import LienDTO, IRealEstateRegistry

# ... other imports

@dataclass
class RealEstateUnit:
    """부동산 자산 단위 (Phase 17-3A, Updated for Lien System)"""
    id: int
    owner_id: Optional[int] = None
    occupant_id: Optional[int] = None
    condition: float = 1.0
    estimated_value: float = 10000.0
    rent_price: float = 100.0

    # New field for tracking all liens against the property
    liens: List[LienDTO] = field(default_factory=list)

    # --- DEPRECATED/DERIVED FIELDS ---
    # The 'mortgage_id' is now a read-only property for backward compatibility.
    # It should not be set directly. New code should inspect the 'liens' list.
    # The registry_dependency would be injected at runtime.
    _registry_dependency: "IRealEstateRegistry" = field(repr=False, compare=False, hash=False)


    @property
    def mortgage_id(self) -> Optional[int]:
        """
        Backward compatibility for existing logic. Returns the loan_id of the
        first mortgage found in the liens list. Returns None if no mortgage exists.
        New logic should iterate over the `liens` list directly.
        """
        for lien in self.liens:
            if lien['lien_type'] == 'MORTGAGE':
                return lien['loan_id']
        return None

    @property
    def is_under_contract(self) -> bool:
        """
        Derived property to check if the unit is in a pending transaction.
        Delegates the check to the Real Estate Registry, which queries the
        Saga state, ensuring a single source of truth.
        """
        return self._registry_dependency.is_under_contract(self.id)

```

## 4. DTO Unification Plan

To resolve the conflict identified in the audit, the following actions will be taken:

1.  **Centralize**: All financial DTOs, including `MortgageApplicationDTO` and the new `LienDTO`, will be consolidated into `modules/finance/api.py`.
2.  **Canonical Source**: The more detailed definition of `MortgageApplicationDTO` from `modules/market/housing_planner_api.py` will be used as the canonical version.
3.  **Deprecate**: The conflicting definition in `modules/housing/dtos.py` will be removed.
4.  **Refactor**: All imports will be updated to point to `modules.finance.api`.

## 5. Verification Plan

### Test Cases
1.  **`mortgage_id` Compatibility**:
    -   Given a `RealEstateUnit` with a `liens` list containing one mortgage, assert that `unit.mortgage_id` returns the correct `loan_id`.
    -   Given a `RealEstateUnit` with an empty `liens` list, assert that `unit.mortgage_id` is `None`.
    -   Given a `RealEstateUnit` with multiple liens, assert that `unit.mortgage_id` returns the ID of the *first* mortgage encountered.
2.  **`is_under_contract` Logic**:
    -   Given a `property_id`, configure the mock `IRealEstateRegistry` to return `True`. Assert that the corresponding `RealEstateUnit.is_under_contract` property returns `True`.
    -   Given a `property_id`, configure the mock `IRealEstateRegistry` to return `False`. Assert that the `RealEstateUnit.is_under_contract` property returns `False`.
3.  **Lien Management**:
    -   Write a test for a service that correctly adds a `LienDTO` to the `liens` list of a `RealEstateUnit` upon mortgage creation.
    -   Write a test for a service that removes a `LienDTO` from the `liens` list when a loan is fully paid off.

### Mocking Guide
-   The `IRealEstateRegistry` interface is designed for easy mocking. In tests, provide a mock implementation that can be configured to return `True` or `False` for the `is_under_contract` method.
-   **DO NOT** use `MagicMock` to create `RealEstateUnit` instances. Use existing fixtures or factory functions that properly initialize the object and its dependencies (`_registry_dependency`).

### 🚨 Schema Change Notice
The introduction of the `liens` list and removal of the `mortgage_id` attribute from the `RealEstateUnit` dataclass is a breaking schema change.
-   **Action Required**: All `golden_...` fixtures in `tests/conftest.py` and data snapshots in `design/_archive/snapshots/` that contain `RealEstateUnit` objects must be updated.
-   **Harvesting**: The `scripts/fixture_harvester.py` script must be run to regenerate these fixtures from a simulation state that includes the new `liens` field.

## 6. 🚨 Risk & Impact Audit (Post-Design)

This design directly addresses the risks identified in the pre-flight audit.

-   **Circular Reference Risk**: **Mitigated**. Centralizing financial DTOs in `modules/finance/api.py` establishes a clear, unidirectional dependency flow where other modules (`housing`, `market`) depend on `finance`, preventing import loops.
-   **Test Impact**: **Acknowledged**. Tests that directly assigned a value to `unit.mortgage_id` will fail. This is intentional. These tests must be refactored to use a dedicated service/manager that manipulates the `liens` list, reflecting a more robust and controlled state management approach.
-   **State Synchronization Risk**: **Resolved**. By defining `is_under_contract` as a derived property that queries Saga state via a dedicated registry, the design eliminates the possibility of data duplication and synchronization bugs. The Saga remains the single source of truth for transactional state.
-   **Backward Compatibility**: **Addressed**. The read-only `mortgage_id` property provides a non-disruptive transition path for legacy code, preventing immediate, widespread breakage. A deprecation warning should be added to guide future development.
