# Spec: DTO Refactoring (TD-194, TD-206)

## 1. Overview

This specification details the necessary refactoring of `HouseholdStateDTO` and `MortgageApplicationDTO` to resolve technical debts TD-194 and TD-206.

The primary goals are:
1.  **Unify Household Data (TD-194)**: Create a single, comprehensive, and **read-only** DTO, `HouseholdSnapshotDTO`, to serve as the canonical data source for all decision-making engines. This eliminates data fragmentation and prepares the system for Phase 33's complex behavioral models.
2.  **Enforce Financial Precision (TD-206)**: Standardize the definition of household debt obligations within the new snapshot DTO. This resolves critical ambiguity in Debt-to-Income (DTI) calculations used in the mortgage application process.

This refactoring addresses the risks identified in the pre-flight audit, including potential SRP violations, downstream consumer breakage, and inconsistent financial logic.

---

## 2. `HouseholdSnapshotDTO` Consolidation (TD-194)

### 2.1. Problem
The existing `HouseholdStateDTO` is a fragmented representation of an agent's state, missing critical fields from underlying components like `EconStateDTO` and `SocialStateDTO`. This forces downstream consumers (e.g., `HousingPlanner`) to work with incomplete data or make multiple costly calls, increasing complexity and the risk of errors.

### 2.2. Solution
We will introduce a new, comprehensive `HouseholdSnapshotDTO` in `modules/household/api.py`. This DTO will act as a **read-only snapshot** of a household's complete state at a specific tick. It is designed for decision-making and will replace the outdated `HouseholdStateDTO` in all high-level logic.

This approach addresses the "God DTO" risk by creating a clear separation: internal components use mutable state DTOs (`EconStateDTO`, etc.), while external decision engines consume this immutable, unified snapshot.

### 2.3. Proposed `modules/household/api.py`

```python
from __future__ import annotations
from typing import TypedDict, List, Dict, Optional
from abc import ABC, abstractmethod

# =================================================================
# 1. UNIFIED DATA CONTRACT (TD-194)
# =================================================================

class HouseholdSnapshotDTO(TypedDict):
    """
    A comprehensive, READ-ONLY snapshot of a household's state at a point in time.
    Designed for use by decision-making engines and external modules.
    This DTO consolidates critical fields from Bio, Econ, and Social components.
    """
    # Core Identity & Bio
    id: int
    age: float
    is_active: bool

    # Economic State
    assets: float
    is_employed: bool
    current_wage: float
    labor_income_this_tick: float
    capital_income_this_tick: float
    inventory: Dict[str, float]

    # Liabilities & Financial Health (TD-206 Solution)
    portfolio_value: float
    total_monthly_debt_payments: float # UNAMBIGUOUS: Sum of all recurring debt payments

    # Housing
    is_homeless: bool
    owned_properties: List[int]
    residing_property_id: Optional[int]

    # Social & Psychological State
    social_status: float
    discontent: float
    optimism: float
    ambition: float

# =================================================================
# 2. HOUSEHOLD INTERFACE
# =================================================================

class IHousehold(ABC):
    """
    Defines the public interface for a Household agent.
    """

    @abstractmethod
    def get_snapshot(self) -> HouseholdSnapshotDTO:
        """
        Assembles and returns a comprehensive, read-only snapshot of the
        household's current state.
        """
        ...

```

---

## 3. `MortgageApplicationDTO` Precision (TD-206)

### 3.1. Problem
The existing mortgage application process suffers from an ambiguous definition of an applicant's financial obligations. The `HousingDecisionRequestDTO` required a pre-calculated `outstanding_debt_payments` field, creating a high risk of inconsistent DTI calculations between the `HousingPlanner` and the `LoanMarket`.

### 3.2. Solution
We will refactor the DTOs involved in the housing and mortgage process to use the new `HouseholdSnapshotDTO` as the single source of truth for an applicant's financial state.

1.  **Standardize Debt Metric**: The `total_monthly_debt_payments` field in `HouseholdSnapshotDTO` becomes the canonical metric for all DTI calculations.
2.  **Enrich `MortgageApplicationDTO`**: The application sent to the `LoanMarket` will now include the applicant's full `HouseholdSnapshotDTO`, providing complete context for the loan decision.
3.  **Simplify `HousingDecisionRequestDTO`**: This DTO no longer needs the ambiguous `outstanding_debt_payments` field, as that data is now part of the snapshot.

This resolves the "Debt vs Payment mismatch" (TD-206) and aligns the process with the transactional saga pattern.

### 3.3. Proposed `modules/housing/api.py`

```python
from __future__ import annotations
from typing import TypedDict, Union, Literal
from abc import ABC, abstractmethod

# Using the new canonical snapshot DTO
from modules.household.api import HouseholdSnapshotDTO
from modules.system.api import HousingMarketSnapshotDTO

# =================================================================
# 1. REFINED DECISION & APPLICATION DTOS (TD-194, TD-206)
# =================================================================

class HousingDecisionRequestDTO(TypedDict):
    """
    (REFINED) Input for the HousingPlanner.
    The ambiguous `outstanding_debt_payments` is removed in favor of the
    canonical data within the household_snapshot.
    """
    household_snapshot: HouseholdSnapshotDTO
    housing_market_snapshot: HousingMarketSnapshotDTO

class MortgageApplicationDTO(TypedDict):
    """
    (REFINED) Data sent to the LoanMarket to apply for a mortgage.
    Includes the full household snapshot to provide a complete, unambiguous
    financial picture for DTI calculation.
    """
    applicant_id: int
    household_snapshot: HouseholdSnapshotDTO # Provides SSOT for financial state
    target_property_id: int
    offer_price: float
    down_payment_amount: float

# --- Unchanged Decision Outcome DTOs for planner output ---

class HousingPurchaseDecisionDTO(TypedDict):
    decision_type: Literal["INITIATE_PURCHASE"]
    target_property_id: int
    offer_price: float
    down_payment_amount: float

class HousingRentalDecisionDTO(TypedDict):
    decision_type: Literal["MAKE_RENTAL_OFFER"]
    target_property_id: int

class HousingStayDecisionDTO(TypedDict):
    decision_type: Literal["STAY"]

HousingDecisionDTO = Union[HousingPurchaseDecisionDTO, HousingRentalDecisionDTO, HousingStayDecisionDTO]


# =================================================================
# 2. REFINED HOUSING-RELATED INTERFACES
# =================================================================

class IHousingPlanner(ABC):
    """
    Defines the public interface for the housing decision logic.
    """
    @abstractmethod
    def make_decision(self, request: HousingDecisionRequestDTO) -> HousingDecisionDTO:
        """
        Analyzes the household and market state to make a housing decision.
        """
        ...
```

---

## 4. Architectural Impact & Refactoring Plan

This is a **significant breaking change** that impacts the core data contracts of the simulation. It requires a coordinated, multi-stage refactoring effort.

1.  **Phase 1: API & DTO Implementation**:
    - Create `modules/household/api.py` and `modules/housing/api.py` with the DTOs and interfaces defined above.

2.  **Phase 2: Household Module Refactoring**:
    - Implement the `get_snapshot()` method in the `Household` agent class. This method will be responsible for querying its internal `EconComponent`, `SocialComponent`, etc., to assemble the `HouseholdSnapshotDTO`.
    - The logic for `total_monthly_debt_payments` must be implemented here, summing payments from all outstanding loans.

3.  **Phase 3: Consumer Module Refactoring**:
    - **`HousingPlanner`**: Update its `make_decision` method to accept the new `HousingDecisionRequestDTO` and use the `household_snapshot` for its logic.
    - **`HousingTransactionSaga`**: Update the "LOAN_APPLICATION_PENDING" step to construct and dispatch the new `MortgageApplicationDTO`.
    - **`LoanMarket`**: Update its mortgage approval logic to extract all required financial data from the `household_snapshot` within the `MortgageApplicationDTO`.

4.  **Phase 4: Test Suite Migration**:
    - Update all unit and integration tests that are broken by these DTO changes. This will primarily affect tests for `HousingPlanner`, `LoanMarket`, and the `HousingTransactionSaga`.

## 5. Verification Plan
- **Unit Tests**:
    - A new test for `Household.get_snapshot()` must verify that all fields are populated correctly.
    - A specific test case must ensure `total_monthly_debt_payments` is calculated accurately for a household with multiple existing loans.
- **Integration Tests**:
    - The end-to-end test for a housing purchase (`test_housing_transaction_saga`) must be updated and pass successfully.
    - A new integration test will verify that a household with a high DTI (based on the new snapshot field) is correctly rejected for a loan by the `LoanMarket`.
- **Golden Data Schema Change**:
    - The introduction of `HouseholdSnapshotDTO` constitutes a schema change for any serialized agent data.
    - **Action**: After implementation, `scripts/fixture_harvester.py` must be reviewed. If any golden fixtures store the old `HouseholdStateDTO`, they must be regenerated to reflect the new `HouseholdSnapshotDTO` structure.

## 6. Mocking Guide
The project's "No Mock-Magic" policy remains in effect. Test setup should continue to rely on concrete fixtures.

- **Use `golden_households`**: The `conftest.py` fixture remains the primary source for test agents.
- **Accessing New DTO**: To test a component that consumes the snapshot, obtain it from the fixture instance:
  ```python
  def test_my_planner_logic(golden_households):
      # Arrange
      test_household = golden_households[0]
      snapshot = test_household.get_snapshot() # Use the new interface method

      # Act & Assert
      assert snapshot['total_monthly_debt_payments'] >= 0
      ...
  ```

## 7. Risk & Impact Audit (Resolution)
This specification directly addresses the risks identified by the pre-flight audit:
- **SRP Violation**: Mitigated by creating a dedicated, read-only `HouseholdSnapshotDTO` for decision-making, separating it from internal mutable state.
- **Breaking Downstream Consumers**: Acknowledged. The refactoring plan provides a clear, staged path for migrating all consumer modules.
- **State Immutability**: Enforced by the read-only nature of the `TypedDict` snapshot and the `get_snapshot()` interface, preventing zero-sum violations.
- **Inconsistent Financial Logic**: Resolved by establishing `total_monthly_debt_payments` in the snapshot as the Single Source of Truth for DTI calculations across all modules.
- **Saga Compatibility**: Ensured. The new `MortgageApplicationDTO` provides a richer, self-contained data packet that enhances the autonomy of the saga's loan application step.

## 8. [Routine] Mandatory Reporting
An insight report will be generated at `communications/insights/TD-194_TD-206_DTO_Refactor.md` detailing the rationale, implementation details, and downstream impact of this DTO consolidation upon completion.
