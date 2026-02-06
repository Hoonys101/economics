# Spec: Domain Purity & Transactional Integrity

- **Version**: 1.0
- **Date**: 2026-02-06
- **Author**: Scribe (Gemini)
- **Objective**: To resolve critical technical debt within the transaction and saga systems (TD-253, TD-254, TD-255, TD-256, TD-258, TD-259) by enforcing stricter domain boundaries, DTO purity, and centralized transaction authority.

---

## 1. Overview & Goals

This specification details the architectural refactoring required to improve the modularity, testability, and integrity of the economic simulation's transactional core. The current implementation suffers from a "God Class" `SettlementSystem`, leaky data transfer objects (DTOs), and inconsistent handling of financial and physical assets.

This refactoring will achieve four primary goals:
1.  **Decompose `SettlementSystem`**: Separate high-level saga orchestration from low-level atomic financial settlement.
2.  **Enforce DTO Purity**: Eliminate the passing of raw agent objects within saga state, making sagas fully serializable and their dependencies explicit.
3.  **Abstract Asset Handling**: Create consistent, authoritative interfaces for managing inventory (real estate) and accessing financial assets, removing redundant and unsafe logic.
4.  **Centralize Monetary Authority**: Ensure all credit creation and destruction events are routed through a single, auditable authority, eliminating manual transaction injections.

## 2. Core Refactoring Initiatives

### 2.1. Saga Orchestration Decoupling (TD-253)

The `SettlementSystem` will be refactored to adhere to the Single Responsibility Principle. All logic related to managing the lifecycle of sagas will be extracted into a new, dedicated `SagaOrchestrator`.

-   **Action**: Move `active_sagas`, `submit_saga`, `process_sagas`, and `find_and_compensate_by_agent` from `SettlementSystem` to a new `SagaOrchestrator` service.
-   **Impact**: `SettlementSystem` is reduced to a pure "Transactional Kernel," responsible only for atomic financial transfers. The `TickOrchestrator` will now interact with the `SagaOrchestrator` instead.

**Pseudo-code: `SagaOrchestrator`**
```python
class SagaOrchestrator:
    def __init__(self, simulation_state):
        self.active_sagas = {}
        self.handler_factory = ... # Factory to get saga-specific handlers

    def submit_saga(self, saga_dto): ...
    def find_and_compensate_by_agent(self, agent_id): ...

    def process_sagas(self):
        handler = self.handler_factory.get_handler("HOUSING") # Inits with sim state
        for saga_id, saga in list(self.active_sagas.items()):
            # ... existing saga processing logic from SettlementSystem ...
            updated_saga = handler.execute_step(saga)
            # ...
```

### 2.2. Housing Saga DTO Purity (TD-255)

The `HousingTransactionSagaStateDTO` will be redesigned to be a pure, serializable data container. It will no longer hold references to live agent objects. All required data will be fetched once at the start of the saga.

-   **Action**:
    1.  Redefine `HousingTransactionSagaStateDTO` to store agent data (e.g., income, debt) directly, instead of agent IDs that require later resolution.
    2.  Modify `HousingTransactionSagaHandler._handle_initiated` to perform a one-time data fetch, populating a new `context` field in the DTO.
    3.  All subsequent saga steps **MUST** only read data from this `context` field.

**DTO Redefinition:**
```python
# In housing_api.py
class HousingSagaAgentContext(TypedDict):
    id: int
    monthly_income: float
    existing_monthly_debt: float
    # Any other required data...

class HousingTransactionSagaStateDTO(TypedDict):
    # ... existing fields ...
    buyer_context: HousingSagaAgentContext
    seller_context: HousingSagaAgentContext
    loan_application: MortgageApplicationDTO # Remains a DTO
    # Raw agent IDs (buyer_id, seller_id) are removed from top level
```

**Logic Modification (`_handle_initiated`):**
```python
# In saga_handler.py
def _handle_initiated(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
    # 1. Resolve agents ONCE
    buyer = self.simulation.agents.get(saga['buyer_id'])
    seller = self.simulation.agents.get(saga['seller_id']) # Or Gov

    # 2. Populate Buyer Context
    saga['buyer_context'] = {
        "id": saga['buyer_id'],
        "monthly_income": calculate_monthly_income(buyer.current_wage, ...),
        "existing_monthly_debt": calculate_total_monthly_debt_payments(...)
    }
    # 3. Populate Seller Context
    saga['seller_context'] = {"id": seller.id, ...}

    # 4. Prepare loan application using data from the context
    app_dto: MortgageApplicationDTO = {
        "applicant_id": saga['buyer_context']['id'],
        "applicant_monthly_income": saga['buyer_context']['monthly_income'],
        # ...
    }
    saga['loan_application'] = app_dto
    # ... rest of the logic
```

### 2.3. Inventory Abstraction (`IInventoryHandler`) (TD-256)

To decouple physical/digital asset management from financial settlement, a new `IInventoryHandler` interface will be created. The existing `HousingService` is the designated implementer for housing-related inventory.

-   **Action**:
    1.  Define an `IInventoryHandler` interface with methods for locking, releasing, and transferring ownership of an asset.
    2.  The `HousingTransactionSagaHandler` will now depend on `IInventoryHandler`, not a concrete `HousingService`.
    3.  Methods in `saga_handler.py` like `set_under_contract`, `release_contract`, and `transfer_ownership` will be calls to this new interface.

**Interface Definition (`modules/inventory/api.py`):**
```python
class IInventoryHandler(Protocol):
    def lock_asset(self, asset_id: Any, lock_owner_id: Any) -> bool: ...
    def release_asset(self, asset_id: Any, lock_owner_id: Any) -> bool: ...
    def transfer_asset(self, asset_id: Any, new_owner_id: Any) -> bool: ...
    def add_lien(self, asset_id: Any, lien_details: Any) -> Optional[UUID]: ...
    def remove_lien(self, asset_id: Any, lien_id: UUID) -> bool: ...
```

### 2.4. Financial Asset Access Unification (`FinanceAssetUtil`) (TD-259)

A utility module will be created to provide a canonical way to access an agent's financial assets, abstracting away the legacy `dict` vs. `float` representation.

-   **Action**: Create a `FinanceAssetUtil` with a `get_asset_balance` function. All parts of the codebase that currently perform `isinstance(agent.assets, dict)` checks (e.g., `AITrainingManager`) must be refactored to use this utility.

**Utility Definition (`modules/finance/util.py`):**
```python
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode

def get_asset_balance(agent: Any, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
    """Safely gets the financial asset balance for a given agent."""
    if hasattr(agent, 'wallet') and agent.wallet is not None:
        return agent.wallet.get_balance(currency)
    
    # Legacy fallbacks
    assets_raw = getattr(agent, 'assets', 0.0)
    if isinstance(assets_raw, dict):
        return assets_raw.get(currency, 0.0)
    try:
        return float(assets_raw) if currency == DEFAULT_CURRENCY else 0.0
    except (TypeError, ValueError):
        return 0.0
```

### 2.5. Centralized Monetary Authority (TD-258)

The manual injection of `Transaction` objects from within the `HousingTransactionSagaHandler` is strictly forbidden. All monetary supply changes must go through the `SettlementSystem` (acting as an agent of the Central Bank).

-   **Action**:
    1.  Remove the manual `Transaction(...)` creation and `world_state.transactions.append(...)` calls from `_handle_escrow_locked` and `_reverse_settlement` in `saga_handler.py`.
    2.  Replace these calls with calls to the appropriate authoritative methods on the `SettlementSystem`.

**Logic Modification (`_handle_escrow_locked`):**
```python
# In saga_handler.py
# BEFORE:
# tx_credit = Transaction(...)
# self.simulation.world_state.transactions.append(tx_credit)

# AFTER:
if principal > 0:
    self.settlement_system.create_and_transfer(
        source_authority=self.simulation.bank, # Or a dedicated CentralBank service
        destination=buyer,
        amount=principal,
        reason=f"mortgage_disbursal_{saga['saga_id']}",
        tick=self.simulation.time
    )
```

## 3. API Definitions (`api.py`)

### `modules/finance/orchestration/api.py`
```python
from typing import Protocol, Any, Dict, UUID

class ISagaHandler(Protocol):
    def execute_step(self, saga: Dict[str, Any]) -> Dict[str, Any]: ...
    def compensate_step(self, saga: Dict[str, Any]) -> Dict[str, Any]: ...

class ISagaOrchestrator(Protocol):
    def submit_saga(self, saga_dto: Dict[str, Any]) -> bool: ...
    def process_sagas(self) -> None: ...
    def find_and_compensate_by_agent(self, agent_id: int) -> None: ...
```

### `modules/inventory/api.py`
```python
from typing import Protocol, Any, Optional
from uuid import UUID

class IInventoryHandler(Protocol):
    """Interface for managing the state of physical or digital assets."""
    def lock_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        """Atomically places a lock on an asset, returns False if already locked."""
        ...

    def release_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        """Releases a lock, returns False if not owned by the lock_owner_id."""
        ...

    def transfer_asset(self, asset_id: Any, new_owner_id: Any) -> bool:
        """Transfers ownership of the asset."""
        ...
    
    def add_lien(self, asset_id: Any, lien_details: Any) -> Optional[UUID]:
        """Adds a lien to a property, returns lien_id on success."""
        ...

    def remove_lien(self, asset_id: Any, lien_id: UUID) -> bool:
        """Removes a lien from a property."""
        ...
```

### `modules/finance/util/api.py`
```python
from typing import Any
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

def get_asset_balance(agent: Any, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
    """
    Safely retrieves an agent's financial asset balance, handling legacy data structures.
    This is the canonical way to check an agent's cash.
    """
    ...
```

## 4. Risk & Impact Audit

-   **Architectural Constraint Adherence**: This plan respects the decomposition of `SettlementSystem` by creating a new `SagaOrchestrator` and `IInventoryHandler`, rather than adding to the existing God Class. It also centralizes transaction authority as mandated.
-   **Critical Risk: Transactional Atomicity**: The extraction of saga logic poses a risk to the atomicity of rollbacks.
    -   **Mitigation**: The verification plan **requires** tick-by-tick comparison of saga state transitions against golden logs generated by `stress_test_validation`. Any divergence in state or final fund balances will fail the test. The compensation logic in `compensate_step` must be rigorously tested for every possible failure point in the state machine.
-   **Critical Risk: Implicit Dependencies**: The refactoring to pure DTOs and `FinanceAssetUtil` will cause breakages where `hasattr` is used.
    -   **Mitigation**: A systematic, three-pronged approach is required:
        1.  **Saga Pre-fetch**: All data needed for a saga's entire lifecycle (e.g., income, debt status, personality traits) **must** be fetched and loaded into the DTO `context` upon initiation.
        2.  **Util Adoption**: A codebase-wide search-and-replace must be performed to substitute direct asset access with `FinanceAssetUtil.get_asset_balance`.
        3.  **Interface Enforcement**: New linter rules or code reviews must flag direct access to agent properties from within transactional or orchestration logic, forcing developers to use DTOs or dedicated provider services.

## 5. Verification Plan

1.  **Unit Tests**:
    -   `SagaOrchestrator`: Test saga submission, processing of terminal states (COMPLETED, FAILED), and removal from the active list.
    -   `FinanceAssetUtil`: Test `get_asset_balance` with agents using both `dict` and `float` asset structures, and agents with `wallet` attributes.
    -   `HousingService` (as `IInventoryHandler`): Test `lock_asset`, `release_asset`, and `transfer_asset` logic, including edge cases like double-locking.
2.  **Integration Tests**:
    -   Create a full integration test for the `HousingTransactionSaga` from initiation to completion, mocking the `SettlementSystem` and `IInventoryHandler`.
    -   Create a separate test for the full compensation path, triggering a failure at each step of the saga (`CREDIT_CHECK`, `APPROVED`, `ESCROW_LOCKED`, `TRANSFER_TITLE`) and verifying that funds are returned and asset locks are released correctly.
3.  **Regression Testing (Mandatory)**:
    -   Run the full simulation with the `stress_test_validation` scenario.
    -   Capture the state of all `HousingTransactionSagaStateDTO` objects at every tick.
    -   Compare this log against a pre-refactor "golden" log. The test passes only if the saga states, transitions, and final financial outcomes are identical.

## 6. Mandatory Reporting Verification

An insight report will be generated upon completion of this refactoring, detailing the resolution of the specified technical debt items (TD-253, TD-254, TD-255, TD-256, TD-258, TD-259). This report will be saved to `communications/insights/domain_purity_refactor.md`.
