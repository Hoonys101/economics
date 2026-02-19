# Current Test Failures (2026-02-19)

Below are the critical failures observed after Wave 3.1 merge and Lifecycle Hotfix.

## 1. Lifecycle Manager - Missing Mandatory Factory
- **Symptom**: `ValueError: IHouseholdFactory is mandatory for AgentLifecycleManager.`
- **Affected Tests**:
    - `tests/integration/test_wo167_grace_protocol.py`
    - `tests/unit/test_lifecycle_reset.py`

## 2. Transaction Processor - Penny vs Dollar Unit Mismatch
- **Symptom**: `AssertionError: assert 1000 == 10.0`
- **Affected Tests**:
    - `tests/unit/test_transaction_processor.py`
    - `tests/modules/finance/transaction/test_processor.py` (assert False is True - potentially unit related)

## 3. Housing Handler - Mock Assertion Failures
- **Symptom**: `AssertionError: transfer(...) call not found` or `expected call not found`.
- **Reason**: Handlers now use `total_pennies` and integer math, but mocks are still asserting against float values or old transfer signatures.
- **Affected Tests**:
    - `tests/unit/markets/test_housing_transaction_handler.py`
    - `tests/unit/systems/handlers/test_housing_handler.py`

---

## Pytest Logs Short Summary:
```
FAILED tests/integration/test_wo167_grace_protocol.py::TestGraceProtocol::test_firm_grace_protocol - ValueError: IHouseholdFactory is mandatory for AgentLifecycleManager.
FAILED tests/integration/test_wo167_grace_protocol.py::TestGraceProtocol::test_household_grace_protocol - ValueError: IHouseholdFactory is mandatory for AgentLifecycleManager.
FAILED tests/modules/finance/transaction/test_processor.py::test_processor_dispatch_legacy_price - AssertionError: assert False is True      
FAILED tests/unit/markets/test_housing_transaction_handler.py::test_housing_transaction_success - AssertionError: transfer(...)
FAILED tests/unit/systems/handlers/test_housing_handler.py::TestHousingTransactionHandler::test_handle_disbursement_failure - AssertionError: expected call not found.
FAILED tests/unit/systems/handlers/test_housing_handler.py::TestHousingTransactionHandler::test_handle_government_seller - AssertionError: False is not true
FAILED tests/unit/systems/handlers/test_housing_handler.py::TestHousingTransactionHandler::test_handle_payment_failure - AssertionError: expected call not found.
FAILED tests/unit/systems/handlers/test_housing_handler.py::TestHousingTransactionHandler::test_handle_purchase_success - AssertionError: False is not true
FAILED tests/unit/test_lifecycle_reset.py::TestLifecycleReset::test_reset_tick_state - ValueError: IHouseholdFactory is mandatory for AgentLifecycleManager.
FAILED tests/unit/test_transaction_processor.py::test_goods_handler_uses_atomic_settlement - assert 1000 == 10.0
```
