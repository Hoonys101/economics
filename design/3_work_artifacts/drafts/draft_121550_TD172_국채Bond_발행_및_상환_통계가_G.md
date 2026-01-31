# TD-172 Refactoring Spec: Government Debt Single Source of Truth (SSOT)

## 1. Project Overview

- **Goal**: Refactor the government debt tracking mechanism to establish `FinanceSystem` as the Single Source of Truth (SSOT), removing redundant and coupled state from the `Government` agent.
- **Scope**:
    - Modify the `Government` agent.
    - Define a clear API in `modules/finance/api.py` for debt management.
    - Update data logging and history tracking.
- **Key Problem**: `Government.total_debt` is calculated by directly accessing `FinanceSystem.outstanding_bonds`, violating SRP and SSOT principles. The definition of "debt" is also ambiguous.

## 2. Detailed Design & Refactoring Steps

### 2.1. Debt Definition Clarification

"Government Debt" will be strictly defined as **the total face value of all outstanding government-issued bonds**. The fallback logic of using `abs(government.assets)` will be removed, as a negative asset balance is an accounting state, not necessarily bonded debt.

### 2.2. `Government` Agent Modifications (`simulation/agents/government.py`)

1.  **Attribute Removal**: The class attribute `total_debt` will be **deleted**.

    ```python
    class Government:
        # ...
        # self.total_debt: float = 0.0  <- REMOVE THIS LINE
        # ...
    ```

2.  **New Public Accessor Method**: A new method `get_total_debt()` will be added to serve as the sole public interface for querying the government's debt. This method delegates the call to the `FinanceSystem`.

    ```python
    # In Government class
    def get_total_debt(self) -> float:
        """
        Retrieves the total outstanding debt from the FinanceSystem.
        This is the single public accessor for government debt.
        """
        if not self.finance_system:
            logger.warning("Finance system not available to query total debt.")
            return 0.0
        # The finance_system is expected to have the new API method
        return self.finance_system.get_total_outstanding_debt(owner_id=self.id)
    ```

3.  **Update `finalize_tick`**: The logic for snapshotting data for `welfare_history` will be updated to use the new accessor method.

    ```python
    # In Government.finalize_tick()
    def finalize_tick(self, current_tick: int):
        """ ... """
        # WO-057 Deficit Spending: The old logic is replaced with a single call to the new accessor.
        total_debt_snapshot = self.get_total_debt()

        # The rest of the old logic for debt calculation is removed.
        # if self.finance_system:
        #      self.total_debt = sum(b.face_value for b in self.finance_system.outstanding_bonds)
        # elif self.assets < 0:
        #      self.total_debt = abs(self.assets)
        # else:
        #      self.total_debt = 0.0
        #  <- ALL OF THIS IS REMOVED

        welfare_snapshot = {
            "tick": current_tick,
            "welfare": self.current_tick_stats["welfare_spending"],
            "stimulus": self.current_tick_stats["stimulus_spending"],
            "education": self.current_tick_stats.get("education_spending", 0.0),
            "debt": total_debt_snapshot, # Use the value from the new accessor
            "assets": self.assets
        }
        self.welfare_history.append(welfare_snapshot)
        if len(self.welfare_history) > self.history_window_size:
            self.welfare_history.pop(0)

        # ... rest of the function
    ```

### 2.3. `FinanceSystem` API Definition (`modules/finance/api.py`)

A clear interface for the `FinanceSystem` will be defined to establish its role as the SSOT for debt. This spec proposes the following API contract.

```python
# In modules/finance/api.py
from __future__ import annotations
from typing import Protocol, Any, List, Tuple, Optional, TypedDict

# Forward-declare DTOs to avoid circular imports if they are in a separate file
if False:
    from .dtos import BailoutLoanDTO
    from simulation.models import Transaction

class InsufficientFundsError(Exception):
    """Custom exception for financial operations."""
    pass

class TaxCollectionResult(TypedDict):
    success: bool
    amount_collected: float
    tax_type: str
    payer_id: Any
    payee_id: Any
    error_message: Optional[str]

class DebtReportDTO(TypedDict):
    """
    A data transfer object for reporting debt statistics.
    """
    owner_id: Any
    total_outstanding_principal: float
    outstanding_bond_count: int
    interest_due_next_tick: float

class IFinanceSystem(Protocol):
    """
    Defines the public interface for the financial system. This establishes the
    FinanceSystem as the Single Source of Truth for government debt.
    """

    # --- NEW SSOT-Compliant Methods for TD-172 ---

    def get_total_outstanding_debt(self, owner_id: Any) -> float:
        """
        Calculates and returns the total principal of all outstanding bonds for a given owner.
        This is the core SSOT method for querying debt.

        Args:
            owner_id: The unique identifier of the entity (e.g., government.id) whose debt is being queried.

        Returns:
            The total outstanding principal as a float.
        """
        ...

    def get_debt_report(self, owner_id: Any) -> DebtReportDTO:
        """
        Returns a structured report of the debt portfolio for a given owner.

        Args:
            owner_id: The unique identifier of the entity whose debt report is requested.

        Returns:
            A DebtReportDTO containing detailed debt statistics.
        """
        ...
```

## 3. 예외 처리 (Error Handling)

- If `get_total_debt()` is called on a `Government` agent without a linked `finance_system`, it will log a warning and return `0.0`. This ensures graceful failure and prevents crashes in downstream consumers.

## 4. 검증 계획 (Verification Plan)

1.  **Existing Test Modification**:
    - All tests that directly read or assert on `government.total_debt` must be updated to use `government.get_total_debt()`.
    - Tests that verify the `debt` field in `government.welfare_history` must be reviewed to ensure they are compatible with the new data source.

2.  **New Unit Tests**:
    - `tests/finance/test_finance_system.py`:
        - `test_get_total_outstanding_debt_no_bonds`: Should return 0.0 for an owner with no bonds.
        - `test_get_total_outstanding_debt_single_bond`: Should return the correct principal for one bond.
        - `test_get_total_outstanding_debt_multiple_bonds`: Should return the sum of principals for multiple bonds.
        - `test_get_total_outstanding_debt_after_maturity`: Should not include matured/paid-off bonds in the total.

3.  **New Integration Tests**:
    - `tests/simulation/test_government_finance_integration.py`:
        - `test_bond_issuance_updates_total_debt`:
            1.  Start simulation.
            2.  Force government to issue a bond of value `X` via `finance_system`.
            3.  Assert `government.get_total_debt()` returns `X`.
            4.  Run simulation until the bond matures.
            5.  Assert `government.get_total_debt()` returns `0.0`.

## 5. Mocking 가이드 (Mocking Guide)

- When testing components that depend on `government.get_total_debt()`, it's now safer and cleaner to mock the accessor method.

- **Example**:
  ```python
  from unittest.mock import patch

  def test_some_reporting_feature(government_agent):
      with patch.object(government_agent, 'get_total_debt', return_value=1_000_000.0) as mock_get_debt:
          report = generate_economic_report(government_agent)
          assert report['debt'] == 1_000_000.0
          mock_get_debt.assert_called_once()
  ```

## 6. Risk & Impact Audit (기술적 위험 분석)

-   **Breaking Change**: The removal of the `government.total_debt` attribute is a **major breaking change**. All consumers, including data analysis scripts, dashboards, and tests, must be migrated to the new `government.get_total_debt()` accessor method.
-   **Circular Dependency**: The proposed design successfully **avoids circular dependencies**. `Government` calls `FinanceSystem`, but `FinanceSystem`'s new debt methods only require a primitive `owner_id`, not the full `Government` object, maintaining a clean dependency graph (`Government` -> `FinanceSystem`).
-   **Performance**: The `get_total_outstanding_debt` method will iterate over the list of outstanding bonds. For simulations with a very large number of concurrent bonds, this could introduce a minor performance overhead if called frequently. However, since it's primarily used once per tick in `finalize_tick`, the impact is expected to be negligible. The `FinanceSystem` can internally cache the result if this becomes a bottleneck.
-   **선행 작업 권고**: This refactoring is self-contained. No other technical debt items are blockers, but this change must be communicated clearly to all team members working on data analysis or features that rely on government state.
