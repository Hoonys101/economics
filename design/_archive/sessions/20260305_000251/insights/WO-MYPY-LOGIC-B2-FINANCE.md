# Mypy Logic Hardening (Finance) Report

**Date**: 2026-02-24
**Mission**: WO-MYPY-LOGIC-B2-FINANCE

## 1. Architectural Insights

### Circular Dependency in System API
The `modules/system/api.py` file (Foundation Layer) was importing `IAgent` from `modules/simulation/api.py` (Simulation Layer), which in turn imported `ISettlementSystem` from `simulation/finance/api.py`, which imported `modules/system/api.py` for `CurrencyCode`. This created a dependency cycle that caused "IAgent not defined" errors during static analysis.
**Decision**: Moved `IAgent` protocol definition to `modules/system/api.py`. This correctly positions the base Agent protocol in the Foundation layer, breaking the cycle and adhering to the layered architecture.

### Finance Protocol Drift
The `IBank` and `IBankService` protocols in `modules/finance/api.py` had drifted from the actual implementation in `simulation/bank.py` and usage in `HousingTransactionHandler`. Specifically, `grant_loan` was missing the `borrower_profile` argument.
**Decision**: Updated `IBankService` to include `borrower_profile` and optional `due_tick`, restoring Liskov Substitution Principle compliance.

### Penny Standard Enforcement
Several key financial components were using `float` for monetary values or performing float arithmetic on prices without explicit integer casting.
**Decisions**:
- `Portfolio.add`: Now accepts `price: int` (pennies) and performs integer division for acquisition price calculation.
- `TransactionProcessor`: Explicitly initializes `amount_settled` as `int` and casts settlement amounts.
- `CentralBank`: Added runtime type guards to `deposit`, `withdraw`, and `mint` to strictly enforce `int` inputs, catching float incursions early.

## 2. Regression Analysis

### Type Safety Improvements
- **Initializer Hardening**: `SimulationInitializer` now strictly casts `ID_BANK` to `AgentID` and includes type guards when distributing initial balances, preventing "MagicMock > int" comparison errors in tests.
- **Testing Utils**: Annotated `SimulationStateBuilder` helper sets to prevent "unannotated helper" errors.

### Test Impact
- No existing tests were modified, ensuring strict regression testing.
- `tests/modules/finance` and `tests/simulation/agents` suites passed 100%, confirming that the protocol updates and penny standard enforcement did not break existing logic.
- `tests/unit/test_transaction_handlers.py` passed, confirming core transaction logic remains intact.

## 3. Test Evidence

```
tests/modules/finance/engines/test_monetary_engine.py::TestMonetaryEngine::test_calculate_rate_neutral PASSED [  2%]
tests/modules/finance/engines/test_monetary_engine.py::TestMonetaryEngine::test_calculate_rate_high_inflation PASSED [  4%]
tests/modules/finance/engines/test_monetary_engine.py::TestMonetaryEngine::test_calculate_rate_recession PASSED [  7%]
tests/modules/finance/engines/test_monetary_engine.py::TestMonetaryEngine::test_strategy_override PASSED [  9%]
tests/modules/finance/engines/test_monetary_engine.py::TestMonetaryEngine::test_rate_multiplier PASSED [ 12%]
tests/modules/finance/monetary/test_strategies.py::test_taylor_rule PASSED [ 14%]
tests/modules/finance/monetary/test_strategies.py::test_taylor_rule_no_explicit_output_gap PASSED [ 17%]
tests/modules/finance/monetary/test_strategies.py::test_friedman_rule PASSED [ 19%]
tests/modules/finance/monetary/test_strategies.py::test_mccallum_rule PASSED [ 21%]
tests/modules/finance/registry/test_bank_registry.py::TestBankRegistry::test_initialization_empty PASSED [ 24%]
tests/modules/finance/registry/test_bank_registry.py::TestBankRegistry::test_initialization_with_data PASSED [ 26%]
tests/modules/finance/registry/test_bank_registry.py::TestBankRegistry::test_register_bank PASSED [ 29%]
tests/modules/finance/registry/test_bank_registry.py::TestBankRegistry::test_get_deposit PASSED [ 31%]
tests/modules/finance/registry/test_bank_registry.py::TestBankRegistry::test_get_loan PASSED [ 34%]
tests/modules/finance/registry/test_bank_registry.py::TestBankRegistry::test_shared_reference PASSED [ 36%]
tests/modules/finance/test_exchange_engine.py::TestCurrencyExchangeEngine::test_convert PASSED [ 39%]
tests/modules/finance/test_exchange_engine.py::TestCurrencyExchangeEngine::test_load_parity PASSED [ 41%]
tests/modules/finance/test_exchange_engine.py::TestCurrencyExchangeEngine::test_missing_config PASSED [ 43%]
tests/modules/finance/transaction/test_engine.py::test_validator_success PASSED [ 46%]
tests/modules/finance/transaction/test_engine.py::test_validator_negative_amount PASSED [ 48%]
tests/modules/finance/transaction/test_engine.py::test_validator_invalid_type PASSED [ 51%]
tests/modules/finance/transaction/test_engine.py::test_validator_account_not_exists PASSED [ 53%]
tests/modules/finance/transaction/test_engine.py::test_validator_insufficient_funds PASSED [ 56%]
tests/modules/finance/transaction/test_engine.py::test_executor_success PASSED [ 58%]
tests/modules/finance/transaction/test_engine.py::test_executor_rollback_success PASSED [ 60%]
tests/modules/finance/transaction/test_engine.py::test_executor_critical_rollback_failure PASSED [ 63%]
tests/modules/finance/transaction/test_engine.py::test_process_transaction_success PASSED [ 65%]
tests/modules/finance/transaction/test_engine.py::test_process_transaction_validation_fail PASSED [ 68%]
tests/modules/finance/transaction/test_engine.py::test_process_batch_atomicity PASSED [ 70%]
tests/modules/finance/transaction/test_engine.py::test_process_batch_rollback_failure PASSED [ 73%]
tests/modules/finance/transaction/test_processor.py::test_processor_dispatch_success PASSED [ 75%]
tests/modules/finance/transaction/test_processor.py::test_processor_dispatch_legacy_price PASSED [ 78%]
tests/modules/finance/transaction/test_processor.py::test_processor_handler_failure PASSED [ 80%]
tests/modules/finance/transaction/test_processor.py::test_processor_handler_exception PASSED [ 82%]
tests/modules/finance/transaction/test_processor.py::test_processor_public_manager PASSED [ 85%]
tests/modules/finance/transaction/test_processor.py::test_processor_public_manager_fail_missing_buyer PASSED [ 87%]
tests/modules/finance/transaction/test_processor.py::test_processor_public_manager_exception PASSED [ 90%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_initialization PASSED [ 92%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_step_delegates_to_strategy PASSED [ 95%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_omo_execution PASSED [ 97%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_snapshot_construction PASSED [100%]
```
