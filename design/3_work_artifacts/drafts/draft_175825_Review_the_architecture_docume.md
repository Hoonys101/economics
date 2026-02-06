# Combined Spec: TD-255 & TD-256 Saga and Inventory Purity

## 1. Objective
To enforce domain purity and data integrity across the platform by (1) isolating long-running Sagas from mid-transaction state changes through immutable DTO snapshots, and (2) abstracting all inventory management behind a strict transactional protocol. This combined initiative addresses the critical architectural risks of state bleeding in sagas and illegal item mutations in agent inventories, strengthening the "Sacred Sequence" and "Purity over Convenience" principles.

## 2. Proposed Architecture

### 2.1 API & Contract Definitions
The following contracts shall be defined in `modules/simulation/api.py` to serve as the single source of truth for these purity patterns.

```python
# In: modules/simulation/api.py

from typing import Protocol, runtime_checkable, Optional
from dataclasses import dataclass

# From TD-256: Inventory Purity
@runtime_checkable
class IInventoryHandler(Protocol):
    """
    A strict protocol for all agent inventory modifications.
    This ensures all inventory changes are atomic and potentially logged
    within a transactional context, preventing illegal state mutations.
    """
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool:
        """Atomically adds items to storage with optional logging."""
        ...

    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool:
        """Atomically removes items if available; returns False if insufficient."""
        ...

    def get_quantity(self, item_id: str) -> float:
        """Returns current quantity of a specific item."""
        ...

# From TD-255: Saga Purity
@dataclass(frozen=True)
class HouseholdSnapshotDTO:
    """
    An immutable snapshot of a household's financial state at a specific moment.
    Used by Sagas to make decisions based on a consistent view of the data,
    preventing state bleeding from external changes.
    
    AUDIT NOTE: This DTO must be comprehensive for underwriting. See Risk Audit section.
    """
    household_id: str
    cash: float
    income: float
    credit_score: float
    existing_debt: float
    assets_value: float

@dataclass
class HousingSagaContext:
    """
    The execution context for a housing saga, ensuring it operates on
    isolated and immutable data snapshots.
    """
    applicant_snapshot: HouseholdSnapshotDTO
    property_id: str
    status: str # e.g., "PENDING_APPROVAL", "APPROVED", "FUNDS_DRAWN"
    saga_id: str
```

### 2.2 Architectural Logic (Pseudo-code)

#### Saga Purity (TD-255)
```python
# In HousingManager or SagaOrchestrator
def begin_housing_saga(household: Household, property_id: str):
    # 1. Create an IMMUTABLE snapshot.
    snapshot = HouseholdSnapshotDTO(
        household_id=household.id,
        cash=household.cash,
        income=household.income,
        # ... and all other relevant fields
    )

    # 2. Create the isolated context. DO NOT pass the 'household' object itself.
    saga_context = HousingSagaContext(
        applicant_snapshot=snapshot,
        property_id=property_id,
        status="PENDING_APPROVAL",
        # ...
    )

    # 3. All subsequent saga steps operate ONLY on saga_context.
    approve_mortgage(saga_context)
```

#### Inventory Purity (TD-256)
```python
# In SettlementSystem
def settle_trade(buyer: IInventoryHandler, seller: IInventoryHandler, good: str, quantity: float, price: float, tx_id: str):
    # 1. Verify buyer and seller conform to the protocol.
    # This check prevents dependency on concrete agent classes.
    if not isinstance(buyer, IInventoryHandler) or not isinstance(seller, IInventoryHandler):
        raise TypeError("Participants in settlement must implement IInventoryHandler.")

    # 2. Perform atomic operations via the protocol.
    # Direct access like `buyer.inventory.append(...)` is now impossible and will fail.
    if buyer.remove_item("cash", price * quantity, transaction_id=tx_id):
        seller.add_item("cash", price * quantity, transaction_id=tx_id)
        seller.remove_item(good, quantity, transaction_id=tx_id)
        buyer.add_item(good, quantity, transaction_id=tx_id)
    else:
        # Handle insufficient funds
        ...
```

## 3. Implementation Steps (Jules Mission)

### Phase 1: API & Contract Definition
1.  [ ] **Define Contracts**: Add `IInventoryHandler`, `HouseholdSnapshotDTO`, and `HousingSagaContext` to `modules/simulation/api.py` as specified above.

### Phase 2: Inventory Protocol Implementation (TD-256)
2.  [ ] **Audit Access Patterns**: Perform a full-codebase search for all instances of `.inventory` access. This includes `modules/`, `tests/`, `scripts/`, and `analysis/`. Document all call sites that require refactoring.
3.  [ ] **Refactor Agents**: Modify `Firm` and `Household` classes.
    - Rename `self.inventory` to `self._inventory` to signal it is a protected member.
    - Implement all methods of the `IInventoryHandler` protocol (`add_item`, `remove_item`, `get_quantity`).
4.  [ ] **Update Call Sites**: Refactor all identified call sites from the audit to use the new protocol methods.
5.  [ ] **Harden `SettlementSystem`**: Update the settlement logic to use `isinstance(agent, IInventoryHandler)` checks before attempting any goods or cash transfers, as shown in the pseudo-code.

### Phase 3: Saga Purity Implementation (TD-255)
6.  [ ] **Refactor Saga Initiation**: Update `HousingManager` (or the relevant Saga orchestrator) to create and populate the `HousingSagaContext` with a `HouseholdSnapshotDTO` at the start of any housing transaction.
7.  [ ] **Update Saga Handlers**: Modify all saga step handlers (e.g., `approve_mortgage`, `drawdown_loan`) to operate exclusively on the `HousingSagaContext` and its snapshot DTO. Remove any direct references to live agent objects.
8.  [ ] **Implement Sanity Checks**: At critical saga boundaries (e.g., before final fund drawdown), implement checks that compare the snapshot state against the agent's current state to detect external interference and fail the saga gracefully if necessary.

## 4. Verification Plan
-   [ ] **New Unit Tests (TD-256)**: Create `tests/unit/test_inventory_handler.py`. These tests must verify the atomicity of the protocol methods and explicitly test that direct access to `_inventory` from outside the agent class is not possible or raises an error.
-   [ ] **New Integration Test (TD-255)**: Create `tests/integration/test_housing_saga_purity.py`. This test must simulate a state change mid-saga (e.g., another system drains the household's cash) and verify that the housing saga fails gracefully due to the snapshot mismatch.
-   [ ] **Automated Access Audit**: Create a script `scripts/audit_inventory_access.py` that scans the codebase for patterns like `._inventory` or `.inventory.` to confirm no direct access remains post-refactoring. The build should fail if this audit detects violations.
-   [ ] **Full Regression**: Execute the entire project test suite (`pytest`) to identify and fix any breakages resulting from the widespread inventory refactoring.

## 5. Mocking Guide
-   **Golden Fixtures**: All tests for these components MUST utilize the existing golden data fixtures (`golden_households`, `golden_firms` in `conftest.py`). These fixtures provide type-safe, realistic agent instances.
-   **Prohibited**: Do not use `MagicMock()` to create mock agents. This practice obscures type errors and leads to brittle tests.
-   **Schema Changes**: If the `HouseholdSnapshotDTO` schema changes, the corresponding golden data samples (`design/_archive/snapshots/`) MUST be updated via the `scripts/fixture_harvester.py` script. This is a mandatory step.

## 6. 🚨 Risk & Impact Audit (Mandatory)
The following constraints and risks identified by the pre-flight audit must be strictly adhered to. Failure to do so will result in a violation of core architectural principles.

1.  **Architectural Constraint: Strict Protocol-Based Dependency (TD-256)**
    - **Rule**: Logic-heavy modules like `modules/simulation` **MUST NOT** import concrete agent classes (`Firm`, `Household`) from `modules/agents`.
    - **Rationale**: To prevent circular dependencies, business logic must depend only on the abstract `IInventoryHandler` protocol defined in `modules/simulation/api.py`. This is non-negotiable and upholds the project's loose-coupling principle.

2.  **Architectural Constraint: Immutable Saga Context (TD-255)**
    - **Rule**: The `SagaOrchestrator` and its handlers **MUST** operate exclusively on the `HouseholdSnapshotDTO`. Live agent objects must not be passed into or referenced from within a saga's execution context.
    - **Rationale**: This enforces the "Purity over Convenience" principle. The DTO is the pure, isolated data contract for the transaction.

3.  **Risk: Widespread Breaking Changes (TD-256)**
    - **Impact**: Encapsulating `agent.inventory` is an intentionally breaking change. All parts of the codebase that perform direct list manipulation will fail.
    - **Mitigation**: The full-codebase audit for `.inventory` access (Implementation Step #2) is the most critical step. No implementation work should proceed until the scope of this impact is fully mapped.

4.  **Risk: Incomplete Data Contracts (TD-255)**
    - **Impact**: If `HouseholdSnapshotDTO` omits a field critical for underwriting (e.g., credit status, existing liabilities), the saga will operate on incomplete data, creating a silent failure mode and negating the benefits of this entire initiative.
    - **Mitigation**: The `HouseholdSnapshotDTO` design MUST be audited by the domain expert (Team Lead) to ensure it contains a complete, self-sufficient representation of an applicant's financial state *before* implementation begins.

## 7. 🚨 Mandatory Reporting Verification
- **Requirement**: During the implementation of these specifications, the assigned developer (Jules) is required to document any unforeseen challenges, new technical debt, or architectural insights discovered.
- **Procedure**: This information must be recorded in a new, separate markdown file within the `communications/insights/` directory (e.g., `communications/insights/insight_td255_td256_purity.md`).
- **Confirmation**: [ ] I acknowledge that a separate insight report will be created and that failing to do so constitutes a mission failure.
