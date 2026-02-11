# Insight Report: Migration of Deprecated Deposit/Withdraw Methods

## 1. Problem: "Magic Money" in Tests
**Severity:** High (Integrity Violation)
**Status:** Resolved

### Description
Tests were frequently utilizing the public `agent.deposit()` and `agent.withdraw()` methods to set up initial state or simulate transactions. This created "Magic Money" — assets that appeared or disappeared without a corresponding counterparty or record in the `SettlementSystem`. This violated the "Zero-Sum Integrity" architectural guardrail.

The recent deprecation of these public methods (raising `NotImplementedError`) caused widespread test failures, blocking CI/CD pipelines.

### Root Cause
- **Legacy API Usage:** Tests relied on convenient but unsafe methods for state manipulation.
- **Mocking Strategy:** Unit tests often mocked these methods to bypass logic, masking the underlying architectural violations.

## 2. Solution: Internalization & Settlement Enforcement

### Architectural Changes
1.  **Internalized Methods:** The `deposit` and `withdraw` methods in `IFinancialAgent` and implementations (e.g., `Government`, `Household`, `Firm`) have been replaced or aliased by protected `_deposit` and `_withdraw` methods.
    -   **Constraint:** These are now *only* for use by the `SettlementSystem` (which manages the ledger) or for *explicit* test setup where direct state injection is necessary and safe.
2.  **Protocol Compliance:** The `Government` agent was updated to correctly implement the `IFinancialAgent` protocol by adding `_deposit`/`_withdraw`, ensuring it can participate in `SettlementSystem` transfers.

### Test Refactoring Pattern
1.  **Setup Phase:** For initializing agents with assets in tests, we now use `_deposit` (or `initial_assets_record` constructor args where applicable, though direct injection was often clearer for legacy tests).
    *   *Before:* `agent.deposit(100)`
    *   *After:* `agent._deposit(100)`
2.  **Operational Phase:** For simulating transfers during test execution, we utilize the `SettlementSystem`.
    *   *Before:* `agent.withdraw(10)`; `other.deposit(10)`
    *   *After:* `settlement_system.transfer(agent, other, 10, ...)`
3.  **Mocking Strategy:** In `tests/system/test_engine.py`, deep mocks of `Household` were replaced with **Real Objects**. This ensures that the complex interplay between `EconState`, `Inventory`, and `Wallet` is tested correctly, rather than relying on potentially incorrect side-effect mocks.

## 3. Verification Results

The following test suites were successfully verified:

*   **`tests/unit/test_tax_incidence.py`**:
    *   `test_firm_payer_scenario`: PASSED
    *   `test_household_payer_scenario`: PASSED
    *   *Note:* Fixed `AssertionError` by correctly implementing `IFinancialAgent` in `Government` mock/stub.

*   **`tests/system/test_engine.py`**:
    *   `test_process_transactions_goods_trade`: PASSED (Fixed `AttributeError` by accessing `_econ_state`)
    *   `test_process_transactions_labor_trade`: PASSED
    *   All other engine tests: PASSED

*   **Integration Tests**:
    *   `tests/integration/test_phase20_scaffolding.py`: PASSED
    *   `tests/integration/scenarios/test_stress_scenarios.py`: PASSED
    *   `tests/integration/test_td194_integration.py`: PASSED
    *   `tests/integration/test_wo058_production.py`: PASSED (Updated `Bootstrapper` calls to mock `SettlementSystem`)

## 4. Learnings & Guidelines
*   **Agent State Mutability:** Agents should not mutate their own financial state directly. Always go through the `SettlementSystem`.
*   **Testing Real Objects:** When testing complex state transitions (like `Household` behavior), preferring real objects over deep mocks significantly reduces brittleness and improves "Groundedness".
*   **Protocol Adherence:** Mocks must strictly adhere to Protocols (`IFinancialAgent`). Missing methods (like `_deposit` on a mock used by a real `SettlementSystem`) cause confusing runtime errors.

## 5. Metadata
*   **Author:** Jules
*   **Date:** 2026-02-12
*   **Related PR:** fix-not-implemented-deposit
