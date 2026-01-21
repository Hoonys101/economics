# Mission Brief: Domain Logic Refactor (Altman Z-Score)

**TO:** Jules, Systems Implementation Agent
**FROM:** Gemini, Administrative Assistant
**DATE:** 2026-01-21
**SUBJECT:** Refactoring `FinanceDepartment` to delegate solvency calculations.

## 1. Mission Objective

Your mission is to refactor the `FinanceDepartment` class to resolve a Single Responsibility Principle (SRP) violation identified in technical debt item **TD-059**. The `calculate_altman_z_score` method contains complex analytical logic that must be extracted into a dedicated, stateless `AltmanZScoreCalculator`.

This refactoring is critical for improving architectural hygiene, adhering to the Single Source of Truth (SSOT) principle, and reducing coupling, as mandated by the **Pre-flight Audit**.

## 2. Strategic Context & Constraints

This task directly addresses the risks outlined in the `AUTO-AUDIT FINDINGS`. You must adhere to the following architectural constraints:

-   **No God Class Dependency:** The new `AltmanZScoreCalculator` **MUST NOT** import or depend on the `Firm` or `FinanceDepartment` classes. It must be a pure analytical component.
-   **SSOT Enforcement:** `FinanceDepartment` remains the single source of truth for financial data. It will construct and pass a Data Transfer Object (DTO) to the calculator.
-   **Test Integrity:** All existing tests must pass. The test suite must be updated to reflect the new architecture, including isolated tests for the new calculator and updated mock-based tests for `FinanceDepartment`.

## 3. Tactical Implementation Plan

Follow these steps precisely to ensure a successful refactoring.

### Step 1: Define the Data Contract (DTO)

Create a new file at `simulation/dtos/financial_dtos.py` and define the data structure that will be passed between components.

**`simulation/dtos/financial_dtos.py`:**
```python
from dataclasses import dataclass

@dataclass
class FinancialStatementDTO:
    """
    A snapshot of a firm's financial health, used for solvency and valuation analysis.
    This DTO acts as the data contract between financial data providers (like FinanceDepartment)
    and analytical calculators.
    """
    total_assets: float
    working_capital: float
    retained_earnings: float
    average_profit: float
    total_debt: float
```

### Step 2: Create the Dedicated Calculator

Create a new file at `simulation/logic/solvency_calculator.py`. This component will contain the extracted calculation logic.

**`simulation/logic/solvency_calculator.py`:**
```python
from simulation.dtos.financial_dtos import FinancialStatementDTO

class AltmanZScoreCalculator:
    """
    A stateless analytical component for calculating the Altman Z-Score.
    It operates exclusively on a FinancialStatementDTO.
    """
    def calculate(self, statement: FinancialStatementDTO) -> float:
        """
        Calculates the Altman Z-Score based on the provided financial statement.

        The formula used is for non-manufacturing or service companies:
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3

        Where:
            X1 = Working Capital / Total Assets
            X2 = Retained Earnings / Total Assets
            X3 = Average Profit / Total Assets
        """
        if statement.total_assets == 0:
            return 0.0

        x1 = statement.working_capital / statement.total_assets
        x2 = statement.retained_earnings / statement.total_assets
        x3 = statement.average_profit / statement.total_assets

        z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3
        return z_score
```

### Step 3: Refactor `FinanceDepartment`

Modify `simulation/components/finance_department.py` to delegate the calculation.

1.  **Add Imports:**
    ```python
    from simulation.logic.solvency_calculator import AltmanZScoreCalculator
    from simulation.dtos.financial_dtos import FinancialStatementDTO
    ```

2.  **Rewrite `calculate_altman_z_score`:**
    Replace the entire existing method with this new implementation. The logic is now to prepare the DTO and call the external calculator.

    ```python
    def calculate_altman_z_score(self) -> float:
        """
        Calculates the Altman Z-Score by delegating to a dedicated calculator.

        This method acts as a wrapper that prepares the financial data (DTO)
        and uses the stateless AltmanZScoreCalculator for the actual computation,
        adhering to SRP and SSOT principles.
        """
        # 1. Get the raw financial data using the existing snapshot method.
        financial_data = self.get_financial_snapshot()

        # 2. Construct the DTO. This enforces the data contract.
        statement_dto = FinancialStatementDTO(
            total_assets=financial_data["total_assets"],
            working_capital=financial_data["working_capital"],
            retained_earnings=financial_data["retained_earnings"],
            average_profit=financial_data["average_profit"],
            total_debt=financial_data["total_debt"]
        )

        # 3. Instantiate the calculator and compute the score.
        calculator = AltmanZScoreCalculator()
        z_score = calculator.calculate(statement_dto)

        return z_score
    ```

### Step 4: Update Verification Protocols (Tests)

1.  **Create New Unit Tests for the Calculator:**
    Create `tests/logic/test_solvency_calculator.py` to test the new component in isolation.

    **`tests/logic/test_solvency_calculator.py`:**
    ```python
    import pytest
    from simulation.dtos.financial_dtos import FinancialStatementDTO
    from simulation.logic.solvency_calculator import AltmanZScoreCalculator

    def test_altman_z_score_calculation():
        """
        Tests the AltmanZScoreCalculator with a sample FinancialStatementDTO.
        """
        # Arrange: Healthy Company
        statement = FinancialStatementDTO(
            total_assets=1000.0,
            working_capital=300.0,  # X1 = 0.3
            retained_earnings=500.0, # X2 = 0.5
            average_profit=100.0,    # X3 = 0.1
            total_debt=200.0
        )
        calculator = AltmanZScoreCalculator()

        # Act
        z_score = calculator.calculate(statement)

        # Assert (1.2*0.3 + 1.4*0.5 + 3.3*0.1 = 0.36 + 0.7 + 0.33 = 1.39)
        assert z_score == pytest.approx(1.39)

    def test_z_score_with_zero_assets():
        """
        Ensures the calculator handles division by zero gracefully.
        """
        # Arrange
        statement = FinancialStatementDTO(
            total_assets=0.0,
            working_capital=0.0,
            retained_earnings=0.0,
            average_profit=0.0,
            total_debt=100.0
        )
        calculator = AltmanZScoreCalculator()

        # Act
        z_score = calculator.calculate(statement)

        # Assert
        assert z_score == 0.0
    ```

2.  **Update Existing `FinanceDepartment` Tests:**
    In `tests/components/test_finance_department.py`, find the test that validates the Z-score. Modify it to mock the new calculator and verify the interaction.

    **`tests/components/test_finance_department.py` (Example Modification):**
    ```python
    from unittest.mock import patch, MagicMock
    from simulation.dtos.financial_dtos import FinancialStatementDTO

    # ... inside the relevant test class ...

    @patch('simulation.components.finance_department.AltmanZScoreCalculator')
    def test_calculate_altman_z_score_delegation(self, MockCalculator):
        """
        Verify that FinanceDepartment correctly delegates calculation to AltmanZScoreCalculator.
        """
        # Arrange
        mock_instance = MockCalculator.return_value
        mock_instance.calculate.return_value = 1.39  # Expected final score

        # Create a firm and its finance department as usual for the test
        # ... setup firm and finance_dept ...
        finance_dept = self.firm.finance
        finance_dept.retained_earnings = 500
        # ... set other financial attributes on the firm/dept ...

        # Act
        result = finance_dept.calculate_altman_z_score()

        # Assert
        assert result == 1.39
        MockCalculator.assert_called_once()  # Verify the calculator was instantiated
        
        # Verify that the 'calculate' method was called with the correct DTO
        call_args, _ = mock_instance.calculate.call_args
        assert len(call_args) == 1
        dto_arg = call_args[0]
        assert isinstance(dto_arg, FinancialStatementDTO)
        
        # Check if the DTO was populated correctly
        snapshot = finance_dept.get_financial_snapshot()
        assert dto_arg.total_assets == snapshot['total_assets']
        assert dto_arg.retained_earnings == 500
    ```

## 4. Acceptance Criteria

-   The `AltmanZScoreCalculator` is implemented as a stateless class in `simulation/logic/solvency_calculator.py`.
-   `FinanceDepartment.calculate_altman_z_score` is refactored to use the new calculator and `FinancialStatementDTO`.
-   The new test file `tests/logic/test_solvency_calculator.py` passes.
-   All existing test suites, especially `tests/components/test_finance_department.py`, pass after modification.
-   The command `ruff check .` reports no new errors.

Proceed with the implementation. This refactoring is a key step towards a more robust and maintainable architecture.
