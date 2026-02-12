# Fix Assertion SSoT: Technical Insight Report

## 1. Problem Description
The codebase is undergoing a migration to a "Single Source of Truth" (SSoT) architecture for financial state, where `SettlementSystem` and `FinanceSystem` hold the authoritative ledger, and agents access their balances via `IFinancialAgent` protocol methods (which delegate to the wallet/ledger).

However, many legacy tests (unit, integration, and system) still rely on direct access to `agent.assets`, which is:
1.  **Deprecated**: `Household` has a legacy `assets` property, but `Firm` does not.
2.  **Unreliable**: Direct attribute modification (`agent.assets = 1000`) bypasses the ledger, creating "Ghost Money" and breaking Zero-Sum Integrity.
3.  **Inconsistent**: Tests pass/fail based on implementation details (e.g., whether the agent is a Mock or a Real object with legacy mixins) rather than the architectural contract.

The goal is to refactor these tests to query the SSoT (`settlement_system.get_balance(agent.id)`) and use proper transfer mechanisms (`settlement_system.transfer` or `_deposit`) for setup.

## 2. Affected Areas

### Unit Tests
*   `tests/unit/test_tax_collection.py`: Uses `MockAgent` with `_add_assets`/`assets` property.
*   `tests/unit/test_tax_incidence.py`: Uses `agent.assets` assertions on `Firm` (which fails as `Firm` lacks the property) and `Household`.

### System Tests
*   `tests/system/test_engine.py`: Uses `agent.assets` on `Firm` objects in `test_process_transactions_invalid_agents` and others.
*   `tests/system/test_phase29_depression.py`: Sets `agent.assets` directly.
*   `tests/system/test_audit_integrity.py`: Sets `agent.assets` directly.

### Integration Tests
*   Government Tests (`test_government_integration.py` etc.): Use `mock_agent.assets` or `agent.assets`.
*   Settlement/Fiscal Tests (`test_atomic_settlement.py`, `test_fiscal_integrity.py`): Assert `agent.assets`.
*   Scenarios (`verify_m2_fix.py`, `verify_mitosis.py`, etc.): Heavy usage of `agent.assets` for verification logic.

## 3. Refactoring Strategy

1.  **Protocol Adherence**: Update Mocks to implement `IFinancialAgent` (`get_balance`, `_deposit`, `_withdraw`).
2.  **SSoT Assertions**: Replace `assert agent.assets == X` with `assert settlement_system.get_balance(agent.id) == X` (or `agent.get_balance(DEFAULT_CURRENCY)` if SSoT is not available in unit test scope).
3.  **Safe Setup**: Replace `agent.assets = X` with `agent._deposit(X)` (unit tests) or `settlement_system.transfer(source, agent, X)` (integration tests).
4.  **Firm Compatibility**: Ensure all tests involving `Firm` use `get_balance()` as `assets` property is removed.

## 4. Risks & Mitigations

*   **Risk**: modifying `Government` or other logic if they internally rely on `assets`.
    *   **Mitigation**: The migration to `IFinancialAgent` in source code is largely complete. If regressions are found, fix the source to use `get_balance`.
*   **Risk**: Mocks in integration tests might not have `get_balance` configured.
    *   **Mitigation**: Update test setup to configure `get_balance.return_value`.

## 5. Conclusion
This refactor aligns the test suite with the Phase 15 "Fortress Finance" architecture, ensuring that tests verify the *system's* view of wealth rather than internal agent state.
