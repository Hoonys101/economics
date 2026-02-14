# Architectural Insight Report: Test Fidelity & Protocol Purity

## 1. Architectural Insights

### 1.1 The "Protocol Purity" Paradox in Mocking
We discovered a critical nuance in Python's `typing.Protocol` when used with Mocks.
While `@runtime_checkable` protocols allow `isinstance(obj, Protocol)` to work structurally, standard `Mock` or `MagicMock` objects do **not** automatically pass this check unless they explicitly implement the required methods or have a `spec` that does.
Previously, tests relied on `hasattr(mock, 'method')`, which always returns `True` for Mocks (as they create attributes on access). This created "False Positive" fidelity, where tests passed even if the mock didn't actually implement the interface required by the production code.
**Decision:** We enforcing `isinstance(mock, Protocol)` checks. This required updating mocks (e.g., in `test_double_entry.py`) to explicitly implement all protocol methods (like `get_all_balances`), significantly increasing test fidelity.

### 1.2 The "Mock Spec" Trap with Global Modules
Mocking the `config` module revealed that tests were relying on "magic" attributes (e.g., `GOVERNMENT_INITIAL_ASSETS`) that did not exist in the actual `config.py`.
By switching to `MagicMock(spec=config)`, we exposed these discrepancies.
**Decision:** We strictly limit `mock_config` to attributes present in the real `config` module or explicitly acknowledge "hidden/dynamic" configs. We removed test-only magic numbers from the shared `mock_config` fixture and moved them to local variables within specific tests/fixtures.

### 1.3 `sys.modules` Patching and `__spec__`
When mocking missing dependencies (like `numpy`) by patching `sys.modules`, modern Python import machinery (Python 3.12+) inspects `__spec__` on the module object.
Standard `MagicMock` does not provide a compliant `__spec__` by default, causing `AttributeError: __spec__` during import.
**Fix:** We explicitly set `mock.__spec__ = None` on mocks injected into `sys.modules` to satisfy the import system.

## 2. Test Evidence

### 2.1 System Tests (`tests/system/test_engine.py`)
Tests passed after refactoring `hasattr` to direct attribute access and fixing `conftest.py`.

```text
tests/system/test_engine.py::TestSimulation::test_simulation_initialization PASSED          [ 11%]
tests/system/test_engine.py::TestSimulation::test_prepare_market_data_basic PASSED          [ 22%]
tests/system/test_engine.py::TestSimulation::test_prepare_market_data_no_goods_market PASSED [ 33%]
tests/system/test_engine.py::TestSimulation::test_prepare_market_data_with_best_ask PASSED  [ 44%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_goods_trade PASSED   [ 55%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_labor_trade PASSED   [ 66%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_research_labor_trade PASSED [ 77%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_invalid_agents PASSED [ 88%]
tests/system/test_engine.py::test_handle_agent_lifecycle_removes_inactive_agents PASSED     [100%]

======================== 9 passed, 2 warnings in 0.86s =========================
```

### 2.2 Unit Tests (`tests/unit/modules/finance/test_double_entry.py`)
Tests passed after updating `MockGovernment` and others to implement `get_all_balances` required by `IFinancialAgent`.

```text
tests/unit/modules/finance/test_double_entry.py::TestDoubleEntry::test_bailout_loan_generates_command PASSED [ 33%]
tests/unit/modules/finance/test_double_entry.py::TestDoubleEntry::test_market_bond_issuance_generates_transaction PASSED [ 66%]
tests/unit/modules/finance/test_double_entry.py::TestDoubleEntry::test_qe_bond_issuance_generates_transaction PASSED [100%]

======================== 3 passed, 2 warnings in 0.15s =========================
```

### 2.3 Inheritance Tests (`tests/unit/systems/test_inheritance_manager.py`)
Verified no regressions in related systems.

```text
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_distribution_transaction_generation PASSED [ 20%]
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_multiple_heirs_metadata PASSED [ 40%]
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_escheatment_when_no_heirs PASSED [ 60%]
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_zero_assets_distribution PASSED [ 80%]
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_tax_transaction_generation PASSED [100%]

======================== 5 passed, 2 warnings in 0.21s =========================
```
