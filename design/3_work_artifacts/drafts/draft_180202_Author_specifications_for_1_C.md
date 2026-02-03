I will prepare two specification documents to address `TD-194` and `TD-206`.

### Specification for TD-194: Consolidating HouseholdStateDTO

```markdown
# Spec: TD-194 Household DTO Consolidation

- **ID**: `spec_td194_household_dto_consolidation`
- **Related Debt**: `TD-194: HouseholdStateDTO Fragmentation`
- **Author**: Scribe (Gemini)

## 1. Executive Summary

This document proposes a refactoring of the `HouseholdStateDTO` to resolve its fragmentation and growing complexity. The current flat structure violates the Single Responsibility Principle and has a wide blast radius for any change. We will replace it with a structured, composite DTO, `HouseholdSnapshotDTO`, which encapsulates state from the agent's underlying components (`Bio`, `Econ`, `Social`). This maintains the crucial decoupling layer for the `DecisionEngine` while improving modularity, maintainability, and testability.

---

## 2. Problem Analysis

The `HouseholdStateDTO` has become a "God DTO" by aggregating a partial, flat list of attributes from distinct components. This has several negative consequences identified in the pre-flight audit:
1.  **High Maintenance Burden**: Adding any new state required by a decision-maker forces a modification of this central, widely-used DTO.
2.  **Systemic Impact**: Changes to `HouseholdStateDTO` affect numerous modules, including the `DecisionEngine` and `HousingPlanner`, leading to high-risk, widespread refactoring efforts.
3.  **Difficult Testing**: Mocking the DTO is cumbersome, contributing to test suite bloat (Ref: `TD-180`).

## 3. Proposed Architecture

### 3.1. New DTO Definition

We will introduce a new composite DTO in `modules/household/dtos.py` and export it via `modules/household/api.py`.

```python
# In: modules/household/dtos.py

from dataclasses import dataclass

# Existing DTOs (BioStateDTO, EconStateDTO, SocialStateDTO) remain as-is.

@dataclass
class HouseholdSnapshotDTO:
    """
    A structured, read-only snapshot of a Household agent's complete state,
    composed of the states of its underlying components.
    Serves as the primary data contract for decision-making systems.
    """
    id: int  # Keep ID at the top level for easy access
    bio_state: BioStateDTO
    econ_state: EconStateDTO
    social_state: SocialStateDTO
    
    # The original HouseholdStateDTO will be deprecated and removed.
```

### 3.2. Assembler Logic (Pseudo-code)

A new service, `HouseholdSnapshotAssembler`, will be responsible for creating the snapshot. This enforces the decoupling of the `Household` agent's internal structure from the data contract.

```python
# In: modules/household/services.py (new file or existing service layer)

class HouseholdSnapshotAssembler:
    def assemble(self, household: "Household") -> HouseholdSnapshotDTO:
        """Creates a snapshot DTO from a household agent instance."""

        # Assumes household agent has internal state components
        # that provide copies of their state DTOs.
        bio_state_copy = household.bio.get_state_copy()
        econ_state_copy = household.econ.get_state_copy()
        social_state_copy = household.social.get_state_copy()

        return HouseholdSnapshotDTO(
            id=household.id,
            bio_state=bio_state_copy,
            econ_state=econ_state_copy,
            social_state=social_state_copy
        )
```

---

## 4. Verification Plan

1.  **Refactor Consumers**: All systems currently using `HouseholdStateDTO` must be refactored to use `HouseholdSnapshotDTO`.
    -   **`DecisionEngine`**: Access will change from `state.assets` to `state.econ_state.assets`.
    -   **`HousingPlanner`**: The `HousingDecisionRequestDTO`'s `household_state` field will now expect a `HouseholdSnapshotDTO`.
2.  **Static Analysis**: Utilize tooling to find all usages of the old `HouseholdStateDTO` to ensure a complete migration.
3.  **Unit Testing**:
    -   Create dedicated unit tests for the `HouseholdSnapshotAssembler` to verify correct state copying and assembly.
    -   Update and refactor tests for `DecisionEngine`, `HousingPlanner`, and other consumers to use the new DTO structure. Mocking should become simpler, as individual component states (`EconStateDTO`, etc.) can be instantiated and passed into the `HouseholdSnapshotDTO` constructor.
4.  **Deprecation**: Once all consumers are migrated, the original `HouseholdStateDTO` will be removed.

---

## 5. Risk & Impact Audit

-   **Decoupling Layer**: **(Mitigated)** This design preserves the essential architectural pattern of using a DTO to decouple decision logic from the agent model.
-   **God Object / SRP Violation**: **(Resolved)** The composite structure resolves the God Object anti-pattern. Responsibility is now clearly partitioned into the respective `Bio`, `Econ`, and `Social` state DTOs.
-   **Widespread Impact**: **(High - Action Required)** This is an intentionally high-impact refactoring. A dedicated branch and careful coordination are required to update all affected modules simultaneously.
-   **Test Brittleness**: **(Mitigated)** While requiring a one-time update to tests, the new structure will improve long-term testability. Mocking a specific scenario (e.g., a household with high assets) becomes a matter of creating a specific `EconStateDTO`, which is more modular and less brittle.

---

### **[Routine] Mandatory Reporting**
Any insights or new technical debt discovered during the implementation of this refactoring must be documented in `communications/insights/TD-194_Refactor.md`.

```

### Specification for TD-206: Enforcing Financial Precision in MortgageApplicationDTO

```markdown
# Spec: TD-206 Mortgage DTO Precision

- **ID**: `spec_td206_mortgage_dto_precision`
- **Related Debt**: `TD-206: MortgageApplicationDTO Precision`
- **Author**: Scribe (Gemini)

## 1. Executive Summary

This specification addresses the critical risk of financial miscalculation within the housing market saga, as identified in `TD-206`. The ambiguity between "total debt" (a stock value) and "debt payments" (a flow value) in the mortgage application process can lead to incorrect Debt-to-Income (DTI) calculations, jeopardizing the stability of the loan and housing markets. We will resolve this by introducing a new, unambiguous DTO, `MortgageApplicationRequestDTO`, which explicitly requires the applicant's `existing_monthly_debt_payments`.

---

## 2. Problem Analysis

The pre-flight audit identified a high-risk ambiguity:
-   **The "Debt vs. Payment" Mismatch**: Lenders calculate DTI using an applicant's gross income and their recurring monthly debt payments. Using the total outstanding debt principal instead would produce a wildly incorrect DTI ratio, causing improper loan approvals or rejections.
-   **API Contract Weakness**: The existing contract (assumed to be implicit or ill-defined in `modules.market.housing_planner_api`) lacks the precision to prevent this error.
-   **Stale Test Suite**: `TD-203` warns that existing tests for the `SettlementSystem` are outdated, meaning this critical financial logic is likely untested.

## 3. Proposed Architecture

### 3.1. New DTO Definition

We will introduce a new, explicit DTO to serve as the request from the `HousingTransactionSaga` to the `LoanMarket`. This will be defined in a new `modules/market/loan_api.py` (or similar) to create a clear API boundary.

```python
# In: modules/market/loan_api.py (or other suitable API file)
from typing import TypedDict

class MortgageApplicationRequestDTO(TypedDict):
    """
    A precise data contract for applying for a mortgage.
    Sent by a saga or agent to the LoanMarket.
    """
    applicant_id: int
    requested_principal: float
    property_value: float # For Loan-to-Value (LTV) calculation
    applicant_monthly_income: float

    # This field resolves the ambiguity of TD-206.
    # It is the SUM of all pre-existing monthly payments for other loans.
    existing_monthly_debt_payments: float

# The existing MortgageApprovalDTO in housing/dtos.py remains the response.
```

### 3.2. Saga Logic Integration (Pseudo-code)

The `HousingTransactionSaga` will be responsible for populating this new DTO.

```python
# In: modules/housing/purchase_saga.py (or equivalent)

class HousingTransactionSaga:
    # ... saga state and methods

    def _prepare_loan_application(self):
        # 1. Get household's financial state
        household_snapshot = self.household_repo.get_snapshot(self.state.buyer_id)
        
        # 2. Get pre-existing debt payments
        # This logic MUST be implemented. Assume a service exists.
        existing_payments = self.debt_service.calculate_monthly_payments(self.state.buyer_id)
        
        # 3. Assemble the precise request DTO
        application_request = MortgageApplicationRequestDTO(
            applicant_id=self.state.buyer_id,
            requested_principal=self.state.loan_application["principal"],
            property_value=self.state.offer_price,
            applicant_monthly_income=household_snapshot.econ_state.current_wage / 12, # Example
            existing_monthly_debt_payments=existing_payments
        )
        
        # 4. Submit to loan market
        self.loan_market.submit_application(application_request)

```

---

## 4. Verification Plan

1.  **Implement `DebtService`**: A reliable mechanism to calculate a household's total `existing_monthly_debt_payments` must be implemented. This is a prerequisite.
2.  **Refactor `HousingTransactionSaga`**: Update the saga to use the new `MortgageApplicationRequestDTO`.
3.  **Refactor `LoanMarket`**: The loan market must be updated to expect the new DTO and use the `existing_monthly_debt_payments` field correctly in its DTI calculations.
4.  **Mandatory Unit Tests**: New unit tests for the `LoanMarket`'s approval logic are required. This directly addresses the risk from `TD-203`.
    -   **Test Case 1 (Approval)**: Applicant with high income and low `existing_monthly_debt_payments` is approved.
    -   **Test Case 2 (Rejection)**: Applicant with the same income but high `existing_monthly_debt_payments` is rejected due to exceeding DTI threshold.
    -   **Test Case 3 (Zero Debt)**: Applicant with zero `existing_monthly_debt_payments` is evaluated correctly.

---

## 5. Risk & Impact Audit

-   **Saga Integrity**: **(Strengthened)** This change introduces a clear, unambiguous contract between the Housing Saga and the Loan Market, reducing the risk of transactional failure due to bad data.
-   **Critical Financial Miscalculation**: **(Resolved)** The explicit field `existing_monthly_debt_payments` directly eliminates the ambiguity that could cause incorrect DTI calculations. The primary remaining risk is the *implementation* of the logic that populates this field.
-   **API Contract Violation**: **(High - Breaking Change)** This is a necessary breaking change for the Loan Market's interface. It clarifies the contract for all future development.
-   **Stale Test Suite (TD-203)**: **(Mitigated)** The verification plan explicitly mandates the creation of new, targeted tests to cover the DTI logic, directly addressing the gap identified in `TD-203`.

---

### **[Routine] Mandatory Reporting**
All findings, implementation details, and newly identified debt related to this task must be logged in `communications/insights/TD-206_Precision.md`.
```
