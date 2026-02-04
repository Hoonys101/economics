# Mission TD-226: Government Agent Decoupling & WelfareManager Extraction

## Overview
This mission focused on extracting `WelfareManager` from the `Government` agent and refactoring the Tax and Welfare logic to use stateless services and DTOs. This resolves circular dependencies and SRP violations.

## Technical Debt & Issues Encountered

### 1. `BailoutLoanDTO` Mismatch
There was a mismatch between the `BailoutLoanDTO` definition in `modules/finance/api.py` and the local definition I initially added to `modules/government/dtos.py`.
- **Issue**: `modules/finance/api.py` includes `firm_id` in the DTO, while my local definition did not. This caused a `TypeError` during testing.
- **Resolution**: Removed the redundant definition in `modules/government/dtos.py` and imported the canonical one from `modules/finance/api.py`.
- **Insight**: Canonical DTOs must be strictly reused. "Forward declaration placeholders" are dangerous if they drift from the source of truth.

### 2. `run_welfare_check` Return Type Change
Legacy `run_welfare_check` returned `List[Transaction]`, which were then appended to the global transaction ledger by the orchestrator (`phases.py`).
- **Change**: The new implementation executes transfers immediately via `SettlementSystem` (which handles ledger recording). Thus, `run_welfare_check` (and the new `execute_social_policy`) now returns `[]` (empty list) or `None`.
- **Risk**: Any system relying on the *returned* list of transactions will see nothing. However, since the side effects (transfers) are applied, the simulation state should be correct.
- **Status**: Updated `Government.run_welfare_check` to return `[]` to satisfy type hints while performing actions internally.

### 3. `IAgent` Definition
`IAgent` was not exported by `modules/system/api.py` as implied by the spec, causing some confusion. I defined a local Protocol `IAgent` in `modules/government/dtos.py` to ensure type safety without circular imports.

## Architectural Insights
- **Orchestrator Pattern**: The `Government` agent now acts as a true orchestrator. It queries `WelfareManager` for *what to do* (DTOs) and then *does it* (SettlementSystem). This separation is much cleaner than the previous "Service does everything" approach.
- **Stateless Services**: `WelfareManager` and `TaxService` are now stateless regarding agent assets/wallets. They only calculate and recommend. This makes them extremely easy to test in isolation, as demonstrated by `test_welfare_manager.py`.

## Remaining Work / Follow-up
- **Phases Update**: `simulation/orchestration/phases.py` still calls `run_welfare_check`. It should eventually be updated to call `execute_social_policy` directly, and the return value expectation should be removed if it's no longer used.
- **FinanceSystem Integration**: `provide_firm_bailout` still relies on `FinanceSystem.grant_bailout_loan` for execution. A cleaner separation might involve `FinanceSystem` accepting a `BailoutLoanDTO` to create the loan, rather than calculating terms itself.

## Conclusion
The decoupling is successful. `Government` no longer passes `self` to its services, breaking the circular dependency. Tests confirm the logic is preserved.
