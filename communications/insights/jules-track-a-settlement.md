# Settlement & Logic Purity Insight Report (TD-CRIT-FLOAT-SETTLE)

## Architectural Insights

### 1. Protocol Purity and Settlement System
The codebase previously used `Any` for the `settlement_system` dependency in `FinanceSystem` (`modules/finance/system.py`). This violated the **Protocol Purity** guardrail by bypassing type checking and allowing implicit dependencies.

We identified that `FinanceSystem` relies on administrative methods (`register_account`) that were not part of the base `ISettlementSystem` protocol in `modules/finance/api.py`. The `ISettlementSystem` protocol is intentionally restricted to basic agent operations (`transfer`, `get_balance`).

**Decision:**
- We identified `IMonetaryAuthority` (which inherits from `ISettlementSystem`) as the correct protocol for administrative financial operations.
- We updated `IMonetaryAuthority` in `modules/finance/api.py` to include `register_account` and `deregister_account`.
- We updated `FinanceSystem` to strictly type hint `settlement_system` as `Optional[IMonetaryAuthority]`.

This enforces that any system passed to `FinanceSystem` must explicitly implement the required administrative capabilities, preventing runtime `AttributeError` and clarifying architectural boundaries.

### 2. Float Settlement Migration
The codebase has largely migrated to integer-based settlement ("pennies").
- `SettlementSystem` explicitly checks `isinstance(amount, int)` and raises `TypeError` otherwise.
- Financial handlers (e.g., `FinancialTransactionHandler`, `LaborTransactionHandler`) use `int()` casting or `round_to_pennies` helper function before invoking settlement.
- `Transaction` model still uses `float` for `price` and `quantity`, which requires careful handling in handlers to ensure conversion to integer pennies happens before settlement calls.

### 3. Protocol Alignment
There was a discrepancy between `simulation.finance.api.ISettlementSystem` (ABC) and `modules.finance.api.ISettlementSystem` (Protocol). The `SettlementSystem` implementation implements the Protocol (via `IMonetaryAuthority` inheritance) but mirrors the ABC's structure. By enriching the `IMonetaryAuthority` Protocol in `modules/finance/api.py`, we aligned the Protocol definition with the actual implementation in `simulation/systems/settlement_system.py`, ensuring `isinstance` checks pass correctly.

## Test Evidence

### `tests/unit/modules/finance/test_settlement_purity.py`
Verified that `SettlementSystem` implements the updated `IMonetaryAuthority` protocol and `FinanceSystem` correctly interacts with a mock of it.

```
tests/unit/modules/finance/test_settlement_purity.py::TestSettlementPurity::test_settlement_system_implements_monetary_authority PASSED [ 50%]
tests/unit/modules/finance/test_settlement_purity.py::TestSettlementPurity::test_finance_system_uses_monetary_authority PASSED [100%]

============================== 2 passed in 0.72s ===============================
```

### `tests/unit/modules/finance/test_system.py`
Verified that existing functionality in `FinanceSystem` remains intact and no regressions were introduced.

```
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_startup_pass PASSED [ 10%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_startup_fail PASSED [ 20%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_established_pass PASSED [ 30%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_established_fail PASSED [ 40%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_market PASSED [ 50%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_qe PASSED [ 60%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_fail PASSED [ 70%]
tests/unit/modules/finance/test_system.py::test_bailout_fails_with_insufficient_government_funds PASSED [ 80%]
tests/unit/modules/finance/test_system.py::test_grant_bailout_loan PASSED [ 90%]
tests/unit/modules/finance/test_system.py::test_service_debt_central_bank_repayment PASSED [100%]

============================== 10 passed in 0.35s ==============================
```
