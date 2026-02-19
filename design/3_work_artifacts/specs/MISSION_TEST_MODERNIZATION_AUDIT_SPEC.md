# Full-Suite Test Modernization Audit Report

## Executive Summary
The test suite is currently in a "Critical Failure" state following the Wave 3.1 architectural shift towards integer-based (Penny) accounting and Lifecycle API hardening. 40% of the core financial and lifecycle tests are failing due to unit mismatches (USD float vs. Penny int) and stale mock configurations that lack mandatory dependencies (e.g., `IHouseholdFactory`). Immediate modernization is required to align tests with the `total_pennies` SSoT and updated `AgentLifecycleManager` signatures.

## Detailed Analysis

### 1. Unit Mismatch: Penny vs. Dollar
- **Status**: ❌ Missing Alignment
- **Evidence**: 
    - `tests/unit/test_transaction_processor.py:L74` (Failure: `assert 1000 == 10.0`)
    - `tests/unit/markets/test_housing_transaction_handler.py:L86-105` (Asserting `200.0` instead of `20000`)
- **Notes**: Production code in `HousingTransactionHandler` and `TransactionProcessor` now strictly operates on integers. Tests continue to inject and assert floats, leading to magnitude errors (100x discrepancy) or type comparison failures.

### 2. Stale Mocks & Protocol Violations
- **Status**: ⚠️ Partial / Outdated
- **Evidence**: 
    - `tests/integration/test_wo167_grace_protocol.py:L51` & `tests/unit/test_lifecycle_reset.py:L11`: `AgentLifecycleManager` instantiation fails because it now requires `IHouseholdFactory` (Missing in mocks).
    - `tests/unit/markets/test_housing_transaction_handler.py:L41`: Mocking `buyer.assets` as a float-valued dict, violating the `IFinancialAgent` penny-int mandate.
- **Notes**: Mocks are "poisoning" tests by returning `MagicMock` objects instead of primitive integers for balance checks, causing serialization errors or logic drifts.

### 3. Direct Agent Attribute Access (SSoT Violations)
- **Status**: ⚠️ Partial
- **Evidence**: `tests/unit/test_lifecycle_reset.py:L57-65`
- **Notes**: Tests directly modify `agent._econ_state` attributes. While necessary for some unit tests, it bypasses the `Wallet` abstraction layer defined in `ARCH_TRANSACTIONS.md:Sec 9`.

## Risk Assessment
- **High Risk**: Technical debt in `test_housing_transaction_handler.py` masks potential money leaks because the mock `SettlementSystem` doesn't verify the zero-sum nature of the transaction.
- **Medium Risk**: `TD-TEST-TX-MOCK-LAG` identified in the ledger is now a blocker for verifying mortgage disbursement logic.

## Modernization Spec for Jules

### A. Lifecycle Suite (Priority 1)
1.  **Dependency Injection**: Update all `AgentLifecycleManager` constructors to include a mocked `IHouseholdFactory`.
2.  **Protocol Spec**: Use `MagicMock(spec=IHouseholdFactory)` to ensure future-proofing.

### B. Financial Core Suite (Priority 2)
1.  **Penny Conversion**: Systematic replacement of all `10.0` (USD) assertions with `1000` (pennies).
2.  **Transaction Hardening**: Update `Transaction` model construction in tests to include `total_pennies`.
3.  **Settlement Assertions**: Update `settlement_system.transfer.assert_called_with` to expect integer pennies.

### C. Housing & Markets (Priority 3)
1.  **Lien Integrity**: Update `test_housing_transaction_success` to verify the `liens` list on `RealEstateUnit` using `LienDTO` structure (integers).
2.  **Escrow Mocking**: Ensure `EscrowAgent` mocks return `balance_pennies` as `int`.

## Conclusion
The test suite is lagging behind the "Sacred Sequence" and "Penny-Int" architectural mandates. The transition from float to integer accounting in the engine has rendered legacy mocks invalid. Modernization must focus on **strict integer typing** and **mandatory dependency injection** to restore CI stability.

---

# Insight Report: Spec Test Modernization Audit
**File Path**: `communications/insights/spec-test-modernization-audit.md`

## 1. Architectural Insights
- **Unit Drift**: The system has successfully transitioned to `total_pennies` for settlement, but the test suite remains in the "Dollar Era." This drift causes 100x magnitude assertion errors.
- **Dependency Hardening**: `AgentLifecycleManager` has been hardened to require a factory, but integration tests were not updated in parallel, breaking the "Walking Skeleton."
- **Mock Poisoning**: Use of `MagicMock` without primitives is causing serialization failures in state-heavy tests.

## 2. Test Evidence (Current Failure Log)
```text
FAILED tests/integration/test_wo167_grace_protocol.py::TestGraceProtocol::test_firm_grace_protocol - ValueError: IHouseholdFactory is mandatory for AgentLifecycleManager.
FAILED tests/unit/test_transaction_processor.py::test_goods_handler_uses_atomic_settlement - assert 1000 == 10.0
FAILED tests/unit/markets/test_housing_transaction_handler.py::test_housing_transaction_success - AssertionError: transfer(...)
```