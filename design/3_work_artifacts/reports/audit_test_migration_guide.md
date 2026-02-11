# Report: Migration Guide for Deprecated Deposit/Withdraw Methods

## Executive Summary

The `NotImplementedError: Direct deposit is deprecated` failures stem from a fundamental shift in the simulation's architecture. Direct asset manipulation via `agent.deposit()` and `agent.withdraw()` is now prohibited to ensure all financial activities are processed through the new, more realistic `TransactionManager` and `SettlementSystem`. Tests must be updated to distinguish between initial state setup and simulated transactions, using constructor arguments for the former and the transaction processor for the latter.

## Detailed Analysis

### 1. Problem Identification: `NotImplementedError`
- **Status**: ✅ Implemented
- **Evidence**: The error `NotImplementedError: Direct deposit is deprecated` is intentionally raised by the base `Agent` class to prevent direct, untracked modification of an agent's assets. This forces all value transfers to be auditable and realistic.
- **Notes**: This change invalidates test patterns that manually call `deposit()` or `withdraw()` for either setting up a test scenario or simulating a transaction's effects.

### 2. Migration Strategy
- **Status**: ✅ Implemented
- **Evidence**: Analysis of `tests/unit/test_tax_incidence.py` and `tests/system/test_engine.py` reveals two primary use cases for the deprecated methods, requiring distinct migration paths.
- **Notes**: The core principle is to differentiate between **Test State Initialization** (setting up an agent's starting assets) and **Simulating Transactions** (testing the effects of a trade, payment, or tax).

---

## Migration Guide for JULE

### Path 1: Test State Initialization

When a test needs to create an agent with a specific starting balance, the `initial_assets_record` parameter in the constructor should be used. The manual, subsequent call to `.deposit()` is the source of the error and must be removed.

The constructor and internal state systems are responsible for placing these initial assets into the agent's wallet.

**File: `tests/unit/test_tax_incidence.py`**

- **Analysis**: The helper functions `_create_household` and `_create_firm` correctly pass the `initial_assets_record` but then make an unnecessary and now-illegal call to `.deposit()`.
- **Evidence**: `tests/unit/test_tax_incidence.py:L57-58`, `tests/unit/test_tax_incidence.py:L81-82`
- **Required Change**: Remove the `.deposit()` lines.

**Before:**
```python
# tests/unit/test_tax_incidence.py:L51-L58
def _create_household(self, id: int, assets: float):
    # ... (constructor call) ...
    h = Household(
        # ...
        initial_assets_record=assets
    )
    # Manually deposit initial assets as per new Household behavior
    if assets > 0:
        h.deposit(int(assets), DEFAULT_CURRENCY) # <--- THIS IS DEPRECATED
    return h
```

**After:**
```python
# tests/unit/test_tax_incidence.py
def _create_household(self, id: int, assets: float):
    # ... (constructor call) ...
    h = Household(
        # ...
        initial_assets_record=assets
    )
    # The constructor now handles placing the initial_assets_record
    # into the agent's wallet. No manual deposit is needed.
    return h
```
*(This same change applies to `_create_firm` in the same file and the agent setup in `tests/system/test_engine.py:setup_simulation_for_lifecycle`)*

### Path 2: Simulating Transactions & Mocking

When a test needs to verify the financial outcome of a simulated event (like a trade or wage payment), it must not call `deposit`/`withdraw` directly. Instead, it should create a `Transaction` object and pass it to `simulation._process_transactions()`. Furthermore, mocking of `deposit`/`withdraw` must be removed entirely, as it creates brittle tests that hide the system's actual behavior.

**File: `tests/system/test_engine.py`**
- **Analysis**: The `mock_households` fixture creates extensive but incorrect mocks for `deposit` and `withdraw`. These mocks simply add or subtract from a Python attribute, completely bypassing the entire financial system (`Wallet`, `TransactionManager`, `SettlementSystem`) that the tests are supposed to be verifying.
- **Evidence**: `tests/system/test_engine.py:L213-220`, `tests/system/test_engine.py:L268-275`
- **Required Change**: Remove the mocked `deposit` and `withdraw` methods. The tests for `_process_transactions` already use a `simulation_instance` which has a real `TransactionManager`. The tests should rely on this real processor to execute the transfers and then assert the final state of the *actual* agent objects.

**Before:**
```python
# tests/system/test_engine.py:L213-220
def withdraw_side_effect_hh1(amount, currency=DEFAULT_CURRENCY):
    hh1.assets -= amount
hh1.withdraw = Mock(side_effect=withdraw_side_effect_hh1)

def deposit_side_effect_hh1(amount, currency=DEFAULT_CURRENCY):
    hh1.assets += amount
hh1.deposit = Mock(side_effect=deposit_side_effect_hh1)
```

**After:**
The `mock_households` fixture should be simplified to create more realistic agent objects, not mocks with reimplemented logic. Let the `Simulation` and its components manage the state.

```python
# tests/system/test_engine.py
@pytest.fixture
def mock_households(mock_config_module, mock_logger):
    # Create REAL Household objects for testing, not deep mocks.
    # Use the same initialization pattern as in test_tax_incidence.
    
    # ... existing initial_needs setup ...

    core_config1 = AgentCoreConfigDTO(id=1, ..., logger=mock_logger)
    hh1 = Household(
        core_config=core_config1,
        engine=Mock(), # Engine can be mocked
        talent=Mock(spec=Talent),
        goods_data=[],
        config_dto=create_household_config_dto(),
        initial_assets_record=100.0
    )
    hh1.is_active = True
    
    # ... setup hh2 similarly ...
    
    return [hh1, hh2]
```
The tests like `test_process_transactions_goods_trade` will now fail because they use a mix of Mocks and real objects. They should be refactored to use the real `Household` objects created above, allowing `simulation_instance._process_transactions` to apply changes to their actual wallets.

## Risk Assessment
- **High Impact**: This is a breaking change that affects a large number of tests. The `test_engine.py` file, in particular, requires significant refactoring due to its reliance on incorrect mocks.
- **Technical Debt**: The previous testing pattern (mocking `deposit`/`withdraw`) was a form of technical debt. While the migration requires effort, it will result in more robust and accurate tests that verify the true behavior of the system.

## Conclusion
The `deposit`/`withdraw` deprecation is a necessary step towards a more robust simulation. To migrate, developers must:
1.  **For Test Setup**: Rely exclusively on the `initial_assets_record` constructor parameter to set an agent's starting balance.
2.  **For Simulating Transfers**: Use `simulation._process_transactions()` to execute a `Transaction` and assert the resulting agent balances.
3.  **For Mocking**: Cease mocking `deposit`/`withdraw`. Instead, create real or partially-mocked agents and allow the simulation's financial systems to operate on them as designed.
