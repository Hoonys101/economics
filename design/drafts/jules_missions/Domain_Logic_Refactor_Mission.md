# Work Order: WO-088 - Refactor Solvency Calculation

**Phase:** 30
**Priority:** HIGH
**Prerequisite:** None
**Related Tech Debt:** TD-059 (Legacy Logic in FinanceDepartment), TD-073 (State Ownership)

---

## 1. Problem Statement

The `FinanceDepartment` class currently violates the Single Responsibility Principle (SRP) by containing the complex business logic for calculating the Altman Z-Score. This logic is tightly coupled to the `Firm` model, accessing its internal state directly. This makes the `FinanceDepartment` difficult to test in isolation and increases the risk of architectural decay.

This work order addresses the deferred technical debt `TD-059` by extracting the calculation logic into a dedicated, stateless component.

## 2. Objective

Delegate the Altman Z-Score calculation from `FinanceDepartment` to a new, stateless `AltmanZScoreCalculator`. This will improve Separation of Concerns (SoC), enhance testability, and align the architecture with our core design principles.

## 3. Implementation Plan

### Track A: Create Data Contract (DTO)

1.  **Create New File:** `simulation/dtos/financial_dtos.py`
2.  **Define DTO:** Add the following `FinancialStatementDTO` class. This object will serve as the standardized data contract between the `FinanceDepartment` and the new calculator, eliminating direct coupling to the `Firm` object.

    ```python
    # simulation/dtos/financial_dtos.py
    from dataclasses import dataclass

    @dataclass
    class FinancialStatementDTO:
        """
        A snapshot of a firm's financial health for solvency analysis.
        This DTO decouples calculators from the main Firm model.
        """
        total_assets: float
        retained_earnings: float
        working_capital: float
        average_profit: float
    ```

### Track B: Create Stateless Calculator

1.  **Create New File:** `simulation/logic/solvency/altman_z_score_calculator.py`
2.  **Implement Calculator:** Create the `AltmanZScoreCalculator` class. It must be **stateless** and depend only on the DTO.

    ```python
    # simulation/logic/solvency/altman_z_score_calculator.py
    from simulation.dtos.financial_dtos import FinancialStatementDTO

    class AltmanZScoreCalculator:
        """
        Calculates the Altman Z-Score based on a standardized financial statement.
        This is a stateless, pure-logic component.
        """
        def calculate(self, statement: FinancialStatementDTO) -> float:
            """
            Calculates the Altman Z-Score for non-manufacturing or service companies.

            Formula: Z = 1.2*X1 + 1.4*X2 + 3.3*X3
            """
            if statement.total_assets == 0:
                return 0.0

            # X1: Working Capital / Total Assets
            x1 = statement.working_capital / statement.total_assets

            # X2: Retained Earnings / Total Assets
            x2 = statement.retained_earnings / statement.total_assets

            # X3: Average Profit / Total Assets (Using 'average_profit' from DTO)
            x3 = statement.average_profit / statement.total_assets

            z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3)
            return z_score
    ```

### Track C: Refactor FinanceDepartment

1.  **Modify File:** `simulation/components/finance_department.py`
2.  **Update `calculate_altman_z_score` method:** Replace the existing calculation logic with the following steps:
    a. Gather the required financial data from the `firm` object.
    b. Populate the `FinancialStatementDTO`.
    c. Instantiate `AltmanZScoreCalculator`.
    d. Call the calculator with the DTO and return the result.

    ```python
    # In simulation/components/finance_department.py

    # Add necessary imports at the top of the file
    from simulation.dtos.financial_dtos import FinancialStatementDTO
    from simulation.logic.solvency.altman_z_score_calculator import AltmanZScoreCalculator

    # ... inside the FinanceDepartment class ...

    def calculate_altman_z_score(self) -> float:
        """
        Calculates the Altman Z-Score by delegating to a specialized, stateless calculator.
        This method is now a "Controller" that gathers data and orchestrates the call.
        """
        total_assets = self.firm.assets + self.firm.capital_stock + self.get_inventory_value()
        if total_assets == 0:
            return 0.0

        working_capital = self.firm.assets - getattr(self.firm, 'total_debt', 0.0)
        avg_profit = sum(self.profit_history) / len(self.profit_history) if self.profit_history else 0.0

        # 1. Create the Data Transfer Object (DTO)
        statement = FinancialStatementDTO(
            total_assets=total_assets,
            retained_earnings=self.retained_earnings,
            working_capital=working_capital,
            average_profit=avg_profit
        )

        # 2. Instantiate and use the stateless calculator
        calculator = AltmanZScoreCalculator()
        z_score = calculator.calculate(statement)

        return z_score

    # The old logic within this method should be completely removed.
    ```

## 4. Verification Plan

1.  **New Unit Tests:** Create a new test file `tests/logic/solvency/test_altman_z_score_calculator.py`. Write unit tests for the `AltmanZScoreCalculator` that verify its calculations against known inputs and edge cases (e.g., `total_assets` is zero).
2.  **Existing Test Suite:** Run the full `pytest` suite. All tests related to firm bankruptcy, solvency, and financial state must pass without modification. The refactoring should be transparent to the rest of the system.
3.  **Code Quality:** Run `ruff check .` to ensure the new code conforms to project standards.

## 5. 🚨 Architectural Constraints (Mandatory)

You must adhere to the findings from the **Pre-flight Audit**.

1.  **Stateless Calculator:** The `AltmanZScoreCalculator` **MUST** remain stateless. It should not have an `__init__` method that stores data and must not modify the input DTO.
2.  **No Circular Dependencies:** The `AltmanZScoreCalculator` **MUST NOT** import `Firm`, `FinanceDepartment`, or any other high-level component. Its only dependency should be the DTO.
3.  **Preserve State Ownership:** This refactoring **DOES NOT** address `TD-073`. `FinanceDepartment` remains the responsible party for gathering data from the `firm` object. Do not move data-gathering logic into the calculator.

---

## 📜 [Routine] Jules' Reporting Duty

As you implement this mission, document any unforeseen challenges, insights, or new technical debt discovered. Create a new markdown file in `communications/insights/` named `WO-088_Jules_Log.md` to record your findings. This is critical for the team's continuous learning process.
