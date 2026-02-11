```markdown
# Spec: Float to Integer (Pennies) Currency Migration

## 1. Introduction & Goal

This document outlines the architectural specification for migrating the simulation's entire financial system from `float`-based currency representation to `int`-based, representing all monetary values in the smallest currency unit (pennies).

The primary goal is to eliminate floating-point precision errors, enforce perfect zero-sum integrity across all transactions, and improve the robustness and predictability of the economic simulation. This change is foundational and impacts all modules that handle monetary values.

## 2. Core Principles

1.  **The Penny Standard**: All monetary values held in agent state, transferred via DTOs, passed in function arguments, or stored in the database **MUST** be integers representing pennies. The `float` type is explicitly forbidden for representing currency.
2.  **Calculation Before Transaction**: All calculations that can result in fractional pennies (e.g., interest, taxes, division) **MUST** be performed and rounded to an integer *at the source* of the calculation.
3.  **Transactional Purity**: Core financial systems, particularly `SettlementSystem`, **MUST** operate exclusively on integers. They are forbidden from performing rounding and must reject any non-integer inputs.

## 3. Global Rounding Rule

To ensure consistency and prevent systemic monetary drift, a single, global rounding rule is mandated for all financial calculations that produce fractional results.

-   **Rule**: **Banker's Rounding (Round Half to Even)**. This method rounds to the nearest value, with ties rounded to the nearest value with an even least significant digit.
-   **Implementation**: The Python `decimal` module should be used for intermediate calculations to maintain precision, followed by quantization to an integer.

```python
from decimal import Decimal, ROUND_HALF_EVEN

def round_to_pennies(value: Decimal) -> int:
    """
    Applies Banker's Rounding to a Decimal value to get an integer number of pennies.
    """
    # Quantize to the nearest penny (0.01), then convert to an integer.
    # The '1.00' defines precision to two decimal places.
    pennies_decimal = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    return int(pennies_decimal * 100)

# --- Example Usage ---
# interest_rate = Decimal('0.035') # 3.5%
# principal_pennies = 10050 # $100.50
#
# # Incorrect: principal_pennies * interest_rate -> float
# # Correct:
# principal_decimal = Decimal(principal_pennies) / 100
# interest_amount_decimal = principal_decimal * interest_rate # Decimal('3.5175')
#
# interest_pennies = round_to_pennies(interest_amount_decimal) # 352 pennies ($3.52)
```

## 4. Data Model & API Changes

All currency fields will be renamed with the `_pennies` suffix to make the unit explicit.

### 4.1. DTOs (`modules/finance/dtos.py`)

-   **`MoneyDTO` will be deprecated in favor of direct `int` usage.** Where a currency code is needed, a tuple `(int, CurrencyCode)` or a new DTO should be used.
-   **`LoanApplicationDTO`**:
    -   `amount: float` -> `amount_pennies: int`
-   **`LoanDTO`**:
    -   `principal: float` -> `principal_pennies: int`
    -   `remaining_principal: float` -> `remaining_principal_pennies: int`
-   **`DepositDTO`**:
    -   `balance: float` -> `balance_pennies: int`

### 4.2. API Interfaces (`modules/finance/api.py`, etc.)

-   **`IFinancialAgent`**:
    -   `deposit(self, amount_pennies: int, currency: CurrencyCode)`
    -   `withdraw(self, amount_pennies: int, currency: CurrencyCode)`
    -   `get_balance(self, currency: CurrencyCode) -> int`
    -   `get_all_balances(self) -> Dict[CurrencyCode, int]`
-   **`IBank`**:
    -   `grant_loan(..., amount_pennies: int, ...)`
    -   `repay_loan(..., amount_pennies: int)`
    -   `get_customer_balance(self, agent_id: AgentID) -> int`
    -   `withdraw_for_customer(self, agent_id: AgentID, amount_pennies: int) -> bool`
    -   `get_total_deposits(self) -> int`
-   **`ISettlementSystem`**:
    -   `transfer(..., amount_pennies: int, ...)`
    -   `create_and_transfer(..., amount_pennies: int, ...)`
    -   `transfer_and_destroy(..., amount_pennies: int, ...)`

### 4.3. Agent & System State

-   **`Household._econ_state`**:
    -   `wallet: Wallet` balances will be `int`.
    -   `current_wage: float` -> `current_wage_pennies: int`
    -   `labor_income_this_tick: float` -> `labor_income_this_tick_pennies: int`
    -   etc.
-   **`Bank`**:
    -   `_wallet` balances will be `int`.
    -   `initial_assets: float` in constructor -> `initial_assets_pennies: int`.
-   **`SettlementSystem`**:
    -   `escrow_cash: float` -> `escrow_cash_pennies: int`
    -   `total_liquidation_losses: float` -> `total_liquidation_losses_pennies: int`

## 5. Calculation Hotspot Refactoring

The following areas require modification to implement precise calculation and rounding *before* values are sent to financial systems.

| Location | Problem | Mandated Solution |
| :--- | :--- | :--- |
| **`simulation/bank.py`** (and future `DebtServicingEngine`) | Interest calculation (`principal * rate`). | 1. Convert principal pennies to a `Decimal`. 2. Multiply by interest rate (`Decimal`). 3. Use `round_to_pennies()` to get the integer interest amount. |
| **`simulation/government.py`** (and future `TaxationEngine`) | Tax calculation (`income * tax_rate`). | 1. Convert income pennies to a `Decimal`. 2. Multiply by tax rate (`Decimal`). 3. Use `round_to_pennies()` to get the integer tax amount. |
| **Marketplaces** (e.g., `GoodsMarket`) | Price determination (e.g., `total_value / total_quantity`). | 1. Perform division using `Decimal` objects. 2. Store the resulting price as a high-precision `Decimal`. 3. When calculating final transaction value (`price * quantity`), use `round_to_pennies()` on the final `Decimal` result. |
| **`modules/household/engines/budget.py`** | Budget allocation (e.g., `total_budget * percentage`). | 1. Convert budget pennies to a `Decimal`. 2. Multiply by allocation percentage (`Decimal`). 3. Use `round_to_pennies()` on the result. The sum of all allocated budgets **MUST** be validated against the original total budget to prevent penny leakage due to rounding. Any remainder must be explicitly handled (e.g., added to savings). |
| **`simulation/core_agents.py:L1115`** (`update_perceived_prices`) | Inflation calculation (`(actual - last) / last`). | This calculation produces a ratio, not a monetary value. It can remain `float` or `Decimal`, but any resulting monetary projection **MUST** use the standard rounding protocol. |
| **`simulation/settlement_system.py:L275`** (`record_liquidation`) | `loss_amount = inv_val + cap_val - recovered_cash` | All inputs (`inventory_value`, `capital_value`, `recovered_cash`) must be provided in pennies (`int`). The calculation becomes simple integer arithmetic. |

## 6. `SettlementSystem` Hardening

The `SettlementSystem` is the guardian of zero-sum integrity. It must be hardened as follows:

1.  **Strict Type Enforcement**: All methods accepting a monetary amount (e.g., `transfer`, `execute_settlement`) **MUST** check `isinstance(amount_pennies, int)`. If the check fails, it must raise a `TypeError` and abort the transaction.
2.  **Remove Float Tolerance**: The overdraft check in `execute_settlement` (`simulation/settlement_system.py:L218`) `> account.escrow_cash + 0.01` **MUST** be removed.
3.  **Replace with Integer Check**: The check must be replaced with a strict integer comparison: `> account.escrow_cash_pennies`.
4.  **Zero Balance Verification**: The `verify_and_close` method **MUST** check for `account.escrow_cash_pennies == 0`. Any non-zero balance is a critical error and indicates a leak elsewhere in the system.

## 7. Testing & Verification Strategy

The existing test suite will be invalidated by this change. A full overhaul is required.

1.  **Update Assertions**: All tests that assert monetary values must be updated to use integers (e.g., `assert agent.get_balance() == 10050`).
2.  **Rewrite Calculation Tests**: Tests for interest, tax, and other financial calculations must be rewritten to use `Decimal` for inputs and assert the correctly rounded integer penny output.
3.  **New Rounding Tests**: Create dedicated unit tests for the `round_to_pennies` function and its application at critical calculation hotspots.
4.  **Golden Data Overhaul**: All mock objects, test fixtures (`golden_households`), and file-based snapshots containing financial data must be updated to use integer penny representation. The `scripts/fixture_harvester.py` may need to be modified to handle this conversion.
5.  **Zero-Sum Integration Test**: A new suite of integration tests must be created to verify system-wide zero-sum integrity. This test should:
    -   Sum the total money supply (M0/M2) at the start of a tick.
    -   Run a complex tick with many transactions (trades, taxes, interest, etc.).
    -   Sum the total money supply at the end of the tick.
    -   Assert that the starting and ending totals are *exactly* equal (unless money was explicitly created/destroyed by the Central Bank).

## 8. 🚨 Risk & Impact Audit

-   **Risk**: Hidden floating-point calculations in untested or legacy code paths remain.
    -   **Mitigation**: A comprehensive code search for `float` type hints and floating-point arithmetic (`*`, `/`) in financial contexts must be performed. Code review must be exceptionally strict in rejecting any new `float`-based currency logic.
-   **Risk**: The "big bang" nature of the change is difficult to coordinate and deploy.
    -   **Mitigation**: The migration **MUST** be performed on a dedicated branch. All work must be completed and all new/updated tests must pass before merging. No partial implementation is acceptable.
-   **Risk**: Performance degradation due to `Decimal` object overhead.
    -   **Mitigation**: `Decimal` usage should be confined to the *moment of calculation*. Values should be immediately converted to `int` for storage and transfer. Performance profiling should be done before and after the change to quantify the impact.

## 9. 🚨 Mandatory Reporting Verification

-   This specification was created to address the critical technical debt of using floating-point numbers for currency, as identified by the pre-flight audit. The primary insight is that **achieving zero-sum integrity is impossible without strict control over rounding at the point of calculation**.
-   A full report on this architectural change and its implications has been recorded in `communications/insights/FP-INT-MIGRATION-01.md`.

```
---
```api.py
from typing import TypedDict, Dict, Optional, List, TypeAlias, Literal
from modules.simulation.api import AgentID

CurrencyCode: TypeAlias = str

# --- Core Interfaces (Updated) ---

class IFinancialAgent:
    """Interface for any agent that can hold and transfer funds."""

    def deposit(self, amount_pennies: int, currency: CurrencyCode = "USD") -> None:
        """Deposits an integer amount of pennies into the agent's wallet."""
        ...

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = "USD") -> None:
        """Withdraws an integer amount of pennies from the agent's wallet."""
        ...

    def get_balance(self, currency: CurrencyCode = "USD") -> int:
        """Returns the agent's balance in integer pennies."""
        ...

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        """Returns all currency balances in integer pennies."""
        ...


class ISettlementSystem:
    """Interface for the system that handles atomic transfers."""

    def transfer(
        self,
        debit_agent: IFinancialAgent,
        credit_agent: IFinancialAgent,
        amount_pennies: int,
        memo: str,
        tick: int,
        currency: CurrencyCode = "USD"
    ) -> Optional[object]: # Returns a transaction-like object on success
        """Executes an atomic transfer of an integer amount of pennies."""
        ...


# --- Bank & Loan DTOs (Updated) ---

LoanStatus = Literal["PENDING", "ACTIVE", "PAID", "DEFAULTED"]

class LoanApplicationDTO(TypedDict):
    """Specifies the details for a new loan application."""
    applicant_id: AgentID
    amount_pennies: int
    purpose: str
    term_months: int


class LoanDTO(TypedDict):
    """Represents the state of an existing loan."""
    loan_id: str
    borrower_id: AgentID
    principal_pennies: int
    interest_rate: float  # Interest rate itself remains a float for calculation purposes
    term_months: int
    remaining_principal_pennies: int
    status: LoanStatus
    origination_tick: int
    due_tick: Optional[int]


class DepositDTO(TypedDict):
    """Represents a customer's deposit at a bank."""
    owner_id: AgentID
    balance_pennies: int
    interest_rate: float # Interest rate remains a float


# --- DEPRECATED DTOs ---

class MoneyDTO(TypedDict):
    """
    DEPRECATED. Use `int` for all monetary amounts (pennies).
    This DTO couples amount and currency, but the new standard is to handle them
    as separate parameters in function calls, e.g., `(amount_pennies, currency_code)`.
    """
    amount: float
    currency: CurrencyCode

```
