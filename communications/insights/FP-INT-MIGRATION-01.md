# Insight: Float to Integer (Pennies) Migration

## Context
The simulation currently uses floating-point numbers (`float`) to represent currency. This has led to persistent issues with zero-sum integrity, where fractional pennies are created or destroyed during calculations (e.g., interest, taxes, division) or aggregation. These "leaks" accumulate over time, violating the core economic principle of the simulation.

## Technical Debt
*   **Floating Point Imprecision:** `float` cannot accurately represent all decimal fractions, leading to rounding errors (e.g., `0.1 + 0.2 != 0.3`).
*   **Inconsistent Rounding:** Different parts of the system may round differently (floor, ceil, round), causing drift.
*   **Lack of Atomic Units:** There is no smallest indivisible unit, allowing fractional cents to exist in state.

## Solution: The Penny Standard
Migration to an integer-based system where all monetary values are stored as pennies (1/100th of the currency unit).

*   **Storage:** `int` type for all currency fields (e.g., `balance_pennies`).
*   **Calculation:** Perform intermediate calculations using `Decimal` for precision, then strictly round to integer pennies using **Banker's Rounding (Round Half to Even)** at the point of result generation.
*   **Interfaces:** Update all financial interfaces (`IFinancialAgent`, `IBank`, `ISettlementSystem`) to enforce `int`.

## Impact
This is a global refactoring that invalidates the entire financial layer and its dependents.
*   **DTOs:** `MoneyDTO`, `LoanDTO`, etc., must change.
*   **Agents:** `Household`, `Firm`, `Government`, `Bank` must update their internal state and decision logic.
*   **Engines:** All stateless engines (`BudgetEngine`, `TaxationEngine`, etc.) must accept and return integer values.
*   **Tests:** The entire test suite involving finance must be rewritten.

## Strategic Plan
1.  **Foundation:** Create rounding helpers and update core DTOs/Interfaces.
2.  **State Migration:** Update `Wallet` and Core Agents (`Household`, `Firm`, `Gov`, `Bank`) to hold `int` state.
3.  **Logic Update:** Update all Engines to perform `Decimal` calc and return `int`.
4.  **System Hardening:** Update `SettlementSystem` to strictly enforce zero-sum with integers.
5.  **Verification:** Rewrite tests to assert integer exactness.
