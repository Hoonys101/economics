# Mission Brief: Domain Logic Refactor (Solvency Calculation)

**TO:** Jules
**FROM:** Antigravity (via Gemini Scribe)
**SUBJECT:** Refactor `FinanceDepartment` to Delegate Solvency Logic
**TRACKING ID:** `WO-084` (Work Order)
**RELATED DEBT:** `TD-059`, `TD-058`

## ⚠️ CRITICAL: Architecture Preservation
**DO NOT REGRESS** the TD-067 refactoring:
- CorporateManager MUST continue calling `firm.finance.invest_in_*()` methods
- DO NOT change CorporateManager to use `firm.assets -= amount` directly
- DO NOT add wrapper properties to `Firm` class
- DO NOT move component methods back to `Firm`

Your task is ONLY to extract Altman Z-Score calculation logic, not to restructure how Firm/CorporateManager interact.

---

## 1. Objective

Refactor the `FinanceDepartment` component to eliminate its internal `calculate_altman_z_score` method. All solvency calculations must be delegated to a dedicated, pure `AltmanZScoreCalculator` component, adhering to our established DTO-based communication protocol. This action will resolve technical debt `TD-059` and enforce the Single Source of Truth (SSOT) principle for financial analytics.

## 2. Context & Architectural Mandate

The recent pre-flight audit confirmed that `FinanceDepartment` violates the Single Responsibility Principle (SRP) by containing complex solvency calculation logic. This is a direct contravention of our architectural goals, as documented in `TD-059`.

Furthermore, architectural mandate `TD-058` requires that communication between major components must be done via Data Transfer Objects (DTOs), not by passing entire agent objects. This refactor must strictly adhere to this principle.

**Reference:** `[AUTO-AUDIT FINDINGS] Pre-flight Audit: Domain Logic Refactor`

## 3. Execution Plan

### Step 1: Define the Data Contract (`FinancialStatementDTO`)

In a suitable DTOs file (e.g., `simulation/dtos/financial_dtos.py`), define a new `TypedDict` or `Dataclass` named `FinancialStatementDTO`.

This DTO will serve as the standardized data contract for passing financial state. Its structure should be based on the return value of the existing `get_financial_snapshot` method in `FinanceDepartment`.

```python
# simulation/dtos/financial_dtos.py (Example)
from typing import TypedDict

class FinancialStatementDTO(TypedDict):
    total_assets: float
    working_capital: float
    retained_earnings: float
    average_profit: float
    total_debt: float
```

### Step 2: Implement the Pure Calculator (`AltmanZScoreCalculator`)

Create or modify the `simulation/ai/altman_z_score.py` file to contain the `AltmanZScoreCalculator`. This class must be "pure" — it should have no knowledge of the `Firm` or `FinanceDepartment` objects.

Its sole public method, `calculate`, will accept the `FinancialStatementDTO` as input and return the Z-score as a float. The logic currently inside `FinanceDepartment.calculate_altman_z_score` should be moved here and adapted to read from the DTO.

```python
# simulation/ai/altman_z_score.py (Example)
from simulation.dtos.financial_dtos import FinancialStatementDTO

class AltmanZScoreCalculator:
    """Calculates the Altman Z-Score based on a standardized financial snapshot."""

    def calculate(self, statement: FinancialStatementDTO) -> float:
        """
        Calculates the Z-Score using a modified formula for service companies.
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3
        """
        if statement["total_assets"] == 0:
            return 0.0

        # X1: Working Capital / Total Assets
        x1 = statement["working_capital"] / statement["total_assets"]

        # X2: Retained Earnings / Total Assets
        x2 = statement["retained_earnings"] / statement["total_assets"]

        # X3: Average Profit / Total Assets
        x3 = statement["average_profit"] / statement["total_assets"]

        z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3
        return z_score
```

### Step 3: Refactor `FinanceDepartment`

1.  **Remove Legacy Logic:** Delete the entire `calculate_altman_z_score` method from `simulation/components/finance_department.py`.
2.  **Implement Delegator Method:** Create a new public method that orchestrates the calculation. This method will construct and pass the DTO to the new calculator.

```python
# In simulation/components/finance_department.py

from simulation.ai.altman_z_score import AltmanZScoreCalculator
from simulation.dtos.financial_dtos import FinancialStatementDTO

class FinanceDepartment:
    # ... existing methods ...

    def __init__(self, firm: Firm, config_module: Any):
        # ...
        self.solvency_calculator = AltmanZScoreCalculator() # Instantiate the calculator

    # DELETE THE ENTIRE `calculate_altman_z_score` METHOD

    def get_altman_z_score(self) -> float:
        """
        Calculates the firm's solvency by assembling a financial snapshot
        and delegating the calculation to the dedicated solvency calculator.
        """
        # 1. Get the raw financial data.
        snapshot_data = self.get_financial_snapshot()

        # 2. Assemble the DTO.
        financial_statement = FinancialStatementDTO(
            total_assets=snapshot_data["total_assets"],
            working_capital=snapshot_data["working_capital"],
            retained_earnings=snapshot_data["retained_earnings"],
            average_profit=snapshot_data["average_profit"],
            total_debt=snapshot_data["total_debt"]
        )

        # 3. Delegate calculation and return the result.
        return self.solvency_calculator.calculate(financial_statement)

    # ... other methods ...
```

### Step 4: Update Call Sites

Search the codebase for any direct calls to `finance_department.calculate_altman_z_score()` and update them to call the new `finance_department.get_altman_z_score()` method.

### Step 5: Refactor Tests

1.  **Test `AltmanZScoreCalculator`:** Create a new test file, `tests/ai/test_altman_z_score.py`. Write focused unit tests that provide various `FinancialStatementDTO` inputs to the calculator and assert that the returned Z-score is correct.
2.  **Test `FinanceDepartment`:** Modify existing tests for `FinanceDepartment`. Instead of testing the calculation itself, mock the `AltmanZScoreCalculator` and verify that the `get_altman_z_score` method correctly assembles the `FinancialStatementDTO` from the `Firm`'s state and passes it to the mocked calculator.

## 4. Verification (Definition of Done)

- The `calculate_altman_z_score` method has been completely removed from `FinanceDepartment`.
- The `AltmanZScoreCalculator` class exists, is pure, and performs the Z-score calculation using a `FinancialStatementDTO`.
- `FinanceDepartment` now uses an instance of `AltmanZScoreCalculator` to perform the solvency check.
- All pre-existing and new unit tests pass successfully.
- Technical debt `TD-059` is resolved and can be marked as such in `design/TECH_DEBT_LEDGER.md`.
