# `modules/system/api.py`

```python
from __future__ import annotations
from typing import TypedDict, Dict

# Assuming CurrencyCode is defined elsewhere, e.g., modules.finance.api
# For standalone definition:
# from typing import NewType
# CurrencyCode = NewType('CurrencyCode', str)
from modules.finance.api import CurrencyCode

class MarketContextDTO(TypedDict):
    """
    A Data Transfer Object to hold market-wide contextual data for a given tick.
    This replaces the need for passing multiple individual parameters (parameter drilling).
    """
    exchange_rates: Dict[CurrencyCode, float]
    benchmark_rates: Dict[str, float]  # e.g., {'cpi': 1.02, 'central_bank_rate': 0.05}

```

# `design/3_work_artifacts/specs/firm_market_context_refactor_spec.md`

```markdown
# Technical Specification: MarketContext DTO Refactoring

## 1. Introduction

- **Purpose**: This document outlines the technical design for introducing a `MarketContextDTO`. This DTO will encapsulate market-wide data (like exchange rates and benchmark interest rates) and be passed to `Firm` and its sub-departments. This refactoring aims to improve code clarity, enforce the Single Responsibility Principle (SRP), and eliminate "parameter drilling."
- **Scope**: The changes will primarily affect `Firm`, `HRDepartment`, `FinanceDepartment`, and `SalesDepartment`, along with their corresponding unit tests.
- **Goals**:
  - Replace loose, individual parameters (`exchange_rates`, `market_data`, etc.) with a single, structured `MarketContextDTO`.
  - Enforce SRP by relocating the marketing budget calculation logic from `Firm` to `SalesDepartment`.
  - Standardize the method signatures for financial and operational calculations across departments.
  - Mitigate risks identified in the pre-flight audit, particularly regarding testability and architectural consistency.

## 2. DTO & Interface Specification

### 2.1. New DTO Definition (`modules/system/api.py`)

A new DTO will be created to hold all relevant market-level context.

```python
from typing import TypedDict, Dict
from modules.finance.api import CurrencyCode

class MarketContextDTO(TypedDict):
    """
    A Data Transfer Object to hold market-wide contextual data for a given tick.
    This replaces the need for passing multiple individual parameters (parameter drilling).
    """
    exchange_rates: Dict[CurrencyCode, float]
    benchmark_rates: Dict[str, float]  # e.g., {'cpi': 1.02, 'central_bank_rate': 0.05}
```

### 2.2. Modified Method Signatures

The following method signatures will be updated to accept the `MarketContextDTO`.

- **Firm**:
  - `generate_transactions(self, government: Optional[Any], all_households: List[Household], current_time: int, market_context: MarketContextDTO) -> List[Transaction]`

- **HRDepartment**:
  - `process_payroll(self, current_time: int, government: Optional[Any], market_context: MarketContextDTO) -> List[Transaction]`

- **FinanceDepartment**:
  - `generate_financial_transactions(self, government: Optional[Any], all_households: List[Household], current_time: int, market_context: MarketContextDTO) -> List[Transaction]`
  - `calculate_valuation(self, market_context: MarketContextDTO) -> MoneyDTO`

- **SalesDepartment**:
  - `adjust_marketing_budget(self, market_context: MarketContextDTO) -> None`
  - **New Method**: `generate_marketing_transaction(self, government: Optional[Any], current_time: int, market_context: MarketContextDTO) -> Optional[Transaction]`

## 3. Refactoring Logic (Pseudo-code)

### 3.1. `Firm.generate_transactions`

The marketing budget calculation logic will be removed and delegated to the `SalesDepartment`.

```python
# Before
def generate_transactions(self, ..., exchange_rates: Dict[CurrencyCode, float] = None) -> List[Transaction]:
    transactions = []
    # 1. Wages & Income Tax (HR)
    tx_payroll = self.hr.process_payroll(..., exchange_rates)
    transactions.extend(tx_payroll)
    # 2. Finance Transactions
    tx_finance = self.finance.generate_financial_transactions(..., exchange_rates)
    transactions.extend(tx_finance)
    # 3. Marketing (Direct Calculation here)
    # ... complex logic to calculate marketing_spend ...
    if marketing_spend > 0:
        tx_marketing = self.finance.generate_marketing_transaction(...)
        transactions.append(tx_marketing)
    self.marketing_budget = marketing_spend
    # ...
    return transactions

# After
def generate_transactions(self, ..., market_context: MarketContextDTO) -> List[Transaction]:
    transactions = []
    # 1. Delegate payroll to HR with full context
    tx_payroll = self.hr.process_payroll(..., market_context=market_context)
    transactions.extend(tx_payroll)

    # 2. Delegate financial transactions to Finance with full context
    tx_finance = self.finance.generate_financial_transactions(..., market_context=market_context)
    transactions.extend(tx_finance)

    # 3. Delegate marketing transaction generation to Sales with full context
    tx_marketing = self.sales.generate_marketing_transaction(..., market_context=market_context)
    if tx_marketing:
        transactions.append(tx_marketing)

    # 4. Brand update logic remains (or is also moved if deemed appropriate later)
    self.brand_manager.update(self.sales.marketing_budget, ...)
    self.sales.adjust_marketing_budget(market_context)

    return transactions
```

### 3.2. `SalesDepartment.generate_marketing_transaction` (New Method)

This new method encapsulates the marketing budget calculation and transaction creation.

```python
# In SalesDepartment
def generate_marketing_transaction(self, government: Optional[Any], current_time: int, market_context: MarketContextDTO) -> Optional[Transaction]:
    """Calculates marketing budget and generates a transaction if applicable."""
    primary_cur = self.firm.finance.primary_currency
    primary_balance = self.firm.finance.get_balance(primary_cur)

    total_revenue = 0.0
    for cur, amount in self.firm.finance.revenue_this_turn.items():
        total_revenue += self.firm.finance.convert_to_primary(amount, cur, market_context.exchange_rates)

    if primary_balance > 100.0:
        marketing_spend = max(10.0, total_revenue * self.firm.marketing_budget_rate)
    else:
        marketing_spend = 0.0

    if primary_balance < marketing_spend:
         marketing_spend = 0.0

    # Update internal state
    self.marketing_budget = marketing_spend

    if marketing_spend > 0:
        # Delegate actual transaction creation to FinanceDepartment to maintain single-source-of-truth for financial ops
        tx_marketing = self.firm.finance.generate_marketing_transaction(government, current_time, marketing_spend)
        return tx_marketing

    return None
```

### 3.3. `HRDepartment` & `FinanceDepartment`

These departments will be updated to consume the `market_context` object instead of the raw `exchange_rates` dictionary.

```python
# In HRDepartment.process_payroll
# def process_payroll(self, ..., exchange_rates: ...):
#     ... self.firm.finance.convert_to_primary(..., rates=exchange_rates)
def process_payroll(self, ..., market_context: MarketContextDTO):
    ... self.firm.finance.convert_to_primary(..., rates=market_context.exchange_rates)

# In FinanceDepartment.calculate_valuation
# def calculate_valuation(self, exchange_rates: ...):
#     ... self.convert_to_primary(..., rates=exchange_rates)
def calculate_valuation(self, market_context: MarketContextDTO):
    ... self.convert_to_primary(..., rates=market_context.exchange_rates)
```

## 4. Verification Plan

- **Test Modification Strategy**: The widespread, cascading test breakage is the primary cost of this refactoring. The strategy is to manage this cost systematically.
  1.  **Fixture Creation**: Create a reusable fixture in `tests/conftest.py` named `default_market_context` that returns a valid `MarketContextDTO` instance (e.g., `{'exchange_rates': {'USD': 1.0, 'KRW': 1300.0}, 'benchmark_rates': {'cpi': 1.0}}`).
  2.  **Systematic Update**: Go through each failing test for `Firm`, `HRDepartment`, `FinanceDepartment`, and `SalesDepartment`. Update the test signature to accept the `default_market_context` fixture and pass it into the method under test.
  3.  **Behavioral Verification**: Add/modify tests to specifically assert that the marketing transaction is now generated via `SalesDepartment`, and that `Firm.generate_transactions` no longer contains this logic.

- **Golden Data**: No changes to Golden Data (`golden_households`, `golden_firms`) are required. The refactoring changes the context passed *to* the agents, not their internal state structure.

## 5. Mocking Guide

- **DO**: When a test requires a `MarketContextDTO`, inject the `default_market_context` fixture from `conftest.py`. For custom scenarios, create a new fixture or override the default one within the test function.
- **Example**:
  ```python
  def test_process_payroll_with_context(hr_department, default_market_context):
      # Act
      transactions = hr_department.process_payroll(
          current_time=1,
          government=None,
          market_context=default_market_context
      )
      # Assert
      assert len(transactions) > 0
  ```
- **DO NOT**: Use `MagicMock` to create a `MarketContextDTO`. Use the typed fixture to ensure type safety and consistency.

## 6. Risk & Impact Audit

This design directly addresses the findings of the pre-flight audit:

- **[MITIGATED] Architectural Constraint: God Class Decomposition**: This refactoring *advances* the decomposition of the `Firm` God Class. By moving the marketing budget calculation from `Firm` into `SalesDepartment`, it further clarifies the separation of concerns.
- **[MITIGATED] Architectural Constraint: Single Responsibility Principle**: The SRP violation identified in `Firm.generate_transactions` is explicitly resolved by delegating marketing logic to `SalesDepartment`.
- **[ADDRESSED] Risk: Widespread Test Breakage**: The risk is accepted as a necessary cost for architectural improvement. The verification plan provides a clear and systematic approach to managing this cost by using a centralized test fixture.
- **[ADDRESSED] Risk: Circular Dependency**: The `MarketContextDTO` is a pure data container with no logic or dependencies. It will be instantiated by the high-level simulation engine and passed unidirectionally down the call stack (`Engine` -> `Firm` -> `Departments`). This maintains a strict one-way data flow and prevents circular dependencies.

## 7. Mandatory Reporting Verification

- **Insight Report Generated**: A report has been recorded at `communications/insights/SPEC-MarketContext-Refactor.md`.
- **Summary of Insight**: The introduction of `MarketContextDTO` is a strategic payment of technical debt. It forces a one-time, high-effort update of test suites in exchange for long-term gains in code clarity, reduced parameter drilling, and stronger adherence to SRP. This formalizes the flow of market-wide data, making the system more robust and easier to reason about.
```
