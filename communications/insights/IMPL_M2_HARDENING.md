# Insight Report: Spec M2 Hardening & CommandBatchDTO

## Architectural Insights

### 1. Unified Command Pipeline via `CommandBatchDTO`
The `CommandBatchDTO` has been successfully refactored to serve as the unified container for all simulation inputs and side-effects for a given tick.
-   **Old Architecture**: Fragmented inputs (`god_commands` vs `system_commands`) and weakly-typed side-effects (`effects_queue: List[Dict]`).
-   **New Architecture**: `CommandBatchDTO` encapsulates:
    -   `transfers`: Typed `FinancialTransferDTO` list.
    -   `mutations`: Typed `SystemLedgerMutationDTO` list.
    -   `god_commands`: List of external overrides.
    -   `system_commands`: List of policy adjustments.
-   **Benefit**: This enforces a single entry point for state mutation, making the simulation deterministic and replayable.

### 2. Strict Integer Enforcement (Float Incursion Defense)
To resolve `TD-FIN-FLOAT-INCURSION`, the new DTOs (`FinancialTransferDTO`, `SystemLedgerMutationDTO`) utilize `__post_init__` validation to raise `TypeError` immediately if a float is passed.
-   **Impact**: Prevents "dust" errors and non-deterministic floating-point math from corrupting the ledger.
-   **Test Evidence**: `test_execute_batch_transfer_float_failure` passes, confirming that even if legacy code attempts to pass floats, the DTO layer will reject it before execution.

### 3. Protocol Segregation & Monetary Authority
A critical insight during implementation was the separation between `ISettlementSystem` (Standard P2P transfers) and `IMonetaryAuthority` (Mint/Burn capabilities).
-   `SettlementSystem` implements both.
-   `MonetaryLedger` depends on `ISettlementSystem` for recording but requires `IMonetaryAuthority` capabilities to execute mutations (Mint/Burn).
-   **Solution**: The `MonetaryLedger.execute_batch` method performs a runtime check (`isinstance(sys, IMonetaryAuthority)`) before calling mint/burn methods. This maintains strict type safety while allowing the system to use the capability if available.

## Regression Analysis

### 1. Test Failures & Fixes
-   **Issue**: `AttributeError: Mock object has no attribute 'mint_and_distribute'`.
-   **Cause**: Unit tests mocked `ISettlementSystem`, but the code under test called `mint_and_distribute`, which is defined in the extended `IMonetaryAuthority` protocol.
-   **Fix**: Updated test fixtures to use `MagicMock(spec=IMonetaryAuthority)`.
-   **Issue**: `test_execute_batch_agent_not_found` did not raise `SettlementFailError`.
-   **Cause**: `MonetaryLedger._resolve_agent` has a fallback chain. It tried `time_provider.get_agent(id)`. Since `time_provider` was a `MagicMock` without a spec, `get_agent(id)` returned a new Mock object (truthy), so the code thought the agent existed.
-   **Fix**: Explicitly removed `get_agent` from the `mock_time_provider` in the test setup (`del tp.get_agent`).

## Test Evidence

```text
tests/modules/finance/test_ledger_batch.py::TestMonetaryLedgerBatchExecution::test_execute_batch_transfer_success PASSED [ 20%]
tests/modules/finance/test_ledger_batch.py::TestMonetaryLedgerBatchExecution::test_execute_batch_transfer_float_failure PASSED [ 40%]
tests/modules/finance/test_ledger_batch.py::TestMonetaryLedgerBatchExecution::test_execute_batch_mint_success PASSED [ 60%]
tests/modules/finance/test_ledger_batch.py::TestMonetaryLedgerBatchExecution::test_execute_batch_burn_success PASSED [ 80%]
tests/modules/finance/test_ledger_batch.py::TestMonetaryLedgerBatchExecution::test_execute_batch_agent_not_found PASSED [100%]
```
