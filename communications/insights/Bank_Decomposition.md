# Technical Insight Report: Bank Decomposition

## 1. Problem Phenomenon
The `Bank` class in `simulation/bank.py` had evolved into a "God Class," violating the Single Responsibility Principle (SRP). It directly managed:
- Loan lifecycle (creation, interest, repayment, termination).
- Deposit lifecycle (creation, interest, withdrawal).
- Monetary policy enforcement (Reserve Requirements, Gold Standard).
- Default consequences (Asset seizure, Share forfeiture, Credit freezing, XP penalties).

Furthermore, the implementation relied heavily on `hasattr()` checks to apply penalties to agents (e.g., checking for `shares_owned` or `education_xp`), violating the architectural guardrail for **Protocol Purity**. This made the code brittle and hard to test with mocks.

## 2. Root Cause Analysis
- **Organic Growth**: Features were added to `Bank` incrementally without refactoring logic into dedicated components.
- **Loose Typing**: Python's dynamic nature encouraged `hasattr` checks instead of defining formal Protocols for agent capabilities (like "Educated" or "Credit Frozen").
- **Facade Misuse**: `Bank` was intended to be a facade but implemented the logic itself instead of delegating to `LoanManager` and `DepositManager`.

## 3. Solution Implementation Details
The decomposition was executed as follows:

### A. Protocol Definition
Defined strict protocols to formalize agent capabilities and enforce type safety:
- **`ICreditFrozen`** (`modules/finance/api.py`): For agents susceptible to credit freezes (Bankruptcy).
- **`IEducated`** (`modules/simulation/api.py`): For agents with education mechanics (Households).
- **`IFinancialEntity`**: Added `@runtime_checkable` to allow `isinstance` checks.

### B. Agent Updates
Updated `BaseAgent`, `Household`, and `Firm` to implement these protocols explicitly.
- `BaseAgent` implements `ICreditFrozen` logic.
- `Household` implements `IEducated` logic via `HouseholdPropertiesMixin`.

### C. Component Decomposition
- **`LoanManager`**: Enhanced to handle `assess_and_create_loan`, `get_debt_status`, and `get_debt_summary`. It now encapsulates the logic for creating loans and checking reserves (via injected wallet).
- **`DepositManager`**: Enhanced with `get_total_deposits` and a robust `withdraw` method (handling multiple deposits).

### D. Bank Refactoring
- **`grant_loan`**: Now delegates entirely to `LoanManager.assess_and_create_loan`.
- **`run_tick`**: Delegates loan servicing to `LoanManager` and deposit interest to `DepositManager`.
- **`_handle_default`**: A new private method encapsulates the complex logic of handling default consequences. It uses `isinstance()` checks against the new protocols to apply penalties (Share seizure, XP reduction, Credit freeze) safely and cleanly.
- **Dependency Injection**: Injected `IShareholderRegistry` into `Bank` to properly handle share seizure (updating the global registry) instead of just clearing local lists.

## 4. Lessons Learned & Technical Debt
- **Protocol Purity requires `@runtime_checkable`**: We encountered a `TypeError` during testing because `IFinancialEntity` was missing this decorator. Protocols used with `isinstance` must be decorated.
- **Refactoring Risks**: Replacing large code blocks (like `run_tick`) via diffs is error-prone regarding indentation. Rewriting the file ensured structural integrity.
- **Remaining Debt**:
    - `Bank` still constructs `Transaction` objects. Future refactoring could move this to a `TransactionFactory` or have Managers return transaction descriptions.
    - `LoanManager` accepts `is_gold_standard` and `reserve_req_ratio` as arguments. While this decouples it from `ConfigManager`, it leaks some "Bank Policy" knowledge into the Manager. A strict "Policy Strategy" pattern could be applied in the future.
