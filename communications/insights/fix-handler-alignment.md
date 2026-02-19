# Fix Handler Alignment Insight Report

## Architectural Insights

1.  **Double Counting Resolved**: Identified and fixed a double-counting issue where `FinanceEngine` was recording expenses (holding cost, maintenance fee) locally before generating a transaction, while `FinancialTransactionHandler` was *also* recording the expense upon execution. The fix was to remove the local recording in `FinanceEngine` and rely solely on the Handler, ensuring "Action -> Result" consistency.
2.  **Missing Handlers Registered**: Added handlers for `repayment` (bailout) and `loan_repayment`. These handlers perform the transfer but deliberately do *not* call `record_expense`, as principal repayment is a balance sheet transaction, not an expense (and profit deduction for bailout is handled separately in the Engine).
3.  **Investment Handler**: Added a handler for `investment` (CAPEX) to support `FinanceEngine` generated transactions, ensuring future compatibility, although `FirmActionExecutor` currently performs direct transfers for internal orders.
4.  **Government Execution Inconsistency**: Noted that `Government` agent often bypasses `TransactionProcessor` by calling `settlement_system.transfer` directly for welfare and infrastructure (though it generates transaction records). `GovernmentSpendingHandler` exists but may be underutilized. This was out of scope to refactor but is a point for future alignment.

## Test Evidence

### Reproduction of Fix (Double Counting Check)

The reproduction test asserted that `FinanceEngine` does *not* update `expenses_this_tick` locally, confirming the fix.

```
tests/reproduce_issue.py::TestFinanceEngineDoubleCounting::test_holding_cost_double_counting_logic PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 1 passed, 2 warnings in 0.28s =========================
```

### Regression Testing (Firm Refactor)

Existing tests passed, ensuring no regression in Firm logic.

```
tests/simulation/test_firm_refactor.py::test_firm_initialization_states PASSED [ 33%]
tests/simulation/test_firm_refactor.py::test_command_bus_internal_orders_delegation
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:88 INTERNAL_EXEC | Firm 1 invested 100.0 in INVEST_AUTOMATION.
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:112 INTERNAL_EXEC | Firm 1 R&D SUCCESS (Budget: 100.0)
PASSED                                                                   [ 66%]
tests/simulation/test_firm_refactor.py::test_produce_orchestration PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 3 passed, 2 warnings in 0.23s =========================
```
