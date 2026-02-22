# Forensics & Core Integrity Hardening (Phase Impl)

**Date**: 2026-02-23
**Author**: Jules
**Mission**: `forensics_hardening_impl`

---

## 1. Architectural Insights

### 🛡️ Core Integrity & Hardening
The "Core Integrity Hardening" mission focused on enforcing architectural guardrails that were identified as drift points in recent audits. Specifically, we addressed:

1.  **Stateless Engine Purity**: The `SalesEngine` was found to be accepting mutable `SalesState` objects, violating the "Stateless Engine" pattern which mandates DTOs (`SalesStateDTO`) for inputs. We successfully refactored `SalesEngine` and its consumer `Firm` to strictly pass DTOs, ensuring that engine logic remains pure and side-effect free (returning intents/results rather than mutating state).
2.  **Penny Arithmetic Safety**: The `MatchingEngine` (both Order Book and Stock) utilized `int()` casting for total penny calculations. While functionally "working", simple truncation can lead to cumulative drift or "penny shaving" anomalies. We replaced these with `int(round(...))` to ensure correct rounding behavior for floating-point quantities (e.g. `2.5` qty * `100` price -> `250` pennies, not `249` due to float precision).
3.  **DTO Completeness**: We identified that `Firm.get_snapshot_dto()` was failing to populate `marketing_budget_rate`, causing discrepancies in tests and potential runtime behavior where the DTO default (0.05) overrode the actual state. This highlights the need for strict mapping audits between State Models and their DTO snapshots.

### 🔍 Forensics & Test Robustness
Several forensic tests (`tests/forensics/`) were failing due to regression or incomplete mocking. Fixes included:
-   **Validation Enforcement**: `SagaOrchestrator.submit_saga` lacked validation for missing critical IDs (Buyer/Seller), which `test_saga_integrity.py` correctly flagged. We implemented strict checks to reject malformed Sagas.
-   **Null Safety**: `EscheatmentHandler` crashed when `metadata` was None. We added defensive checks.
-   **Mock Fidelity**: Tests like `test_bond_liquidity.py` and `test_ghost_account.py` failed because Mocks did not accurately reflect the expected behavior of the system (e.g., `dict.get` side effects, registry lookups). We hardened the tests to use stricter specs and side effects.

---

## 2. Regression Analysis

### 🛠️ Fixes Implemented

| Area | Issue | Fix | Impact |
| :--- | :--- | :--- | :--- |
| **SalesEngine** | `SalesState` mutation & protocol violation | Refactored to accept `SalesStateDTO` only. | Enforced "Stateless Engine" pattern. |
| **Firm** | `get_snapshot_dto` missing fields | Populated `marketing_budget_rate`. | Correct state propagation to engines. |
| **MatchingEngine** | Unsafe `int()` truncation | Replaced with `int(round(...))`. | Accurate penny arithmetic. |
| **SagaOrchestrator** | Missing ID validation | Added checks for `household_id` and `seller_context.id`. | Prevents invalid Sagas from starting. |
| **EscheatmentHandler** | Crash on None metadata | Added `if tx.metadata:` check. | Improved runtime robustness. |
| **Test Suite** | Mock Drift & Logic Gaps | Updated mocks in `test_bond_liquidity` and `test_ghost_account`. | Restored test suite trust (100% Pass). |

### 🚨 Broken Tests & Remediation

1.  **`TestSalesEngine` & `TestFirmSales`**: Failed because the refactor changed signatures to expect DTOs, but tests passed mutable State objects or assumed outdated behavior.
    *   *Fix*: Updated tests to construct and pass `SalesStateDTO`.
2.  **`test_saga_orchestrator_rejects_incomplete_dto`**: Failed because the Orchestrator accepted invalid input.
    *   *Fix*: Implemented validation logic in the Orchestrator.
3.  **`test_bond_issuance_checks_liquidity`**: Failed due to `MagicMock` vs `int` comparison.
    *   *Fix*: Configured `bank_state.reserves.get` side effect to return integers.
4.  **`test_settlement_to_unregistered_agent_handling`**: Failed because `SettlementSystem` couldn't resolve agents correctly with simple Mocks.
    *   *Fix*: Updated `registry.get_agent` side effect to return distinct mocks for different IDs.

---

## 3. Test Evidence

### ✅ Full Test Suite Run
**Result**: 100% PASS (1004 passed, 11 skipped)

```bash
=========================== short test summary info ============================
SKIPPED [1] tests/integration/test_server_integration.py:16: websockets is mocked
SKIPPED [1] tests/security/test_god_mode_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/security/test_server_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/security/test_websocket_auth.py:13: websockets is mocked
SKIPPED [1] tests/system/test_server_auth.py:11: websockets is mocked, skipping server auth tests
SKIPPED [1] tests/test_server_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/test_ws.py:11: fastapi is mocked
SKIPPED [1] tests/market/test_dto_purity.py:26: Pydantic is mocked
SKIPPED [1] tests/market/test_dto_purity.py:54: Pydantic is mocked
SKIPPED [1] tests/modules/system/test_global_registry.py:101: Pydantic is mocked
SKIPPED [1] tests/modules/system/test_global_registry.py:132: Pydantic is mocked
================= 1004 passed, 11 skipped, 2 warnings in 7.97s =================
```
