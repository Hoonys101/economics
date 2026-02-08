# Technical Insight Report: TD-274 Bank Class Decomposition

## 1. Problem Phenomenon (Stack traces, symptoms)
The `Bank` class in `simulation/bank.py` had grown into a "God Class", violating the Single Responsibility Principle (SRP). It managed:
-   Reserves and liquidity (Wallet).
-   Loan lifecycle (creation, interest, default, repayment).
-   Deposit lifecycle (creation, interest, withdrawal).
-   Central Banking functions (Lender of Last Resort, OMO - partially).
-   Direct agent manipulation (modifying `shares_owned`, `education_xp` on default), violating "No Raw Agent Access" rules.

This resulted in:
-   High coupling: Changes to loan logic risked breaking deposit logic.
-   Abstraction Leaks: `Bank` accessed agent internals directly instead of using protocols.
-   Protocol Bypass: `SettlementSystem` was often bypassed for direct asset manipulation (`agent.assets -= x`).

## 2. Root Cause Analysis
-   **Organic Growth**: Features were added to `Bank` over time without architectural boundaries.
-   **Lack of dedicated Managers**: Financial instruments (Loans, Deposits) were treated as simple data structures (`Dict[str, Loan]`) rather than domains requiring their own logic.
-   **Legacy Patterns**: Code relied on direct dictionary manipulation and attribute access (`hasattr`) instead of `IFinancialEntity` protocols.

## 3. Solution Implementation Details
The `Bank` class was refactored into a **Facade** that orchestrates two new managers:
1.  **LoanManager (`modules/finance/managers/loan_manager.py`)**:
    -   Implements `ILoanManager`.
    -   Manages `_Loan` lifecycle.
    -   Calculates interest and defaults purely based on logic (no agent access).
    -   Uses a callback mechanism to request payments, keeping it decoupled from the payment execution system.

2.  **DepositManager (`modules/finance/managers/deposit_manager.py`)**:
    -   Implements `IDepositManager`.
    -   Manages `_Deposit` accounts.
    -   Calculates interest payouts.
    -   Provides `withdraw` functionality for the Bank.

3.  **Bank Facade (`simulation/bank.py`)**:
    -   Holds `self.loan_manager` and `self.deposit_manager`.
    -   Delegates business logic to managers.
    -   Acts as the **Context Root** for `SettlementSystem` interactions.
    -   Injects callbacks into `LoanManager.service_loans` that bridge the gap between `borrower_id` and the `Agent` object required by `SettlementSystem`.
    -   Handles the "consequences" of default (e.g., penalties) since it has access to the `agents_dict`, respecting the boundary that Managers should not touch Agents.

## 4. Lessons Learned & Technical Debt Identified
-   **Facade Pattern**: Effective for breaking down God Classes while maintaining the existing public API (`IBankService`), minimizing disruption to consumers (`Household`, `Firm`).
-   **Callback Injection**: Passing a `payment_callback` to `LoanManager` allowed the manager to remain "Pure" (operating on IDs and Math) while the "Impure" side (Database/Agent lookups/Settlement) remained in the Facade.
-   **Tech Debt**: The `Bank` still handles `process_default` consequences (XP penalty, credit freeze) which feels like it belongs in a `CreditBureau` or `JudicialSystem`. Moving this logic out would further purify `Bank`.
-   **Tech Debt**: `DepositManager` does not natively support reserve ratio checks; the `Bank` currently approximates or skips strict reserve enforcement based on aggregated data. This should be formalized.