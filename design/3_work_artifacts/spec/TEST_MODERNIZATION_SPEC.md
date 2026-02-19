# Design Document: Test Suite Modernization (Mission: modernize-tests)

## 1. Introduction

- **Purpose**: To align the test suite with the Phase 19/20 architectural standards, specifically addressing the deprecation of `Government.collect_tax`, the introduction of `FiscalEngine`, and the Dependency Injection pattern in `HouseholdFactory`.
- **Scope**:
  - `tests/integration/test_government_fiscal_policy.py`
  - `tests/system/test_audit_integrity.py`
  - `tests/unit/test_transaction_handlers.py`
  - `tests/simulation/factories/test_agent_factory.py`
  - `tests/integration/test_government_refactor_behavior.py`
  - `tests/unit/test_tax_collection.py`
- **Goals**: Eliminate deprecated API usage, fix "AttributeError" on mocks, and restore Green build status while enforcing Zero-Sum integrity.

## 2. Detailed Design

### 2.1. Component: Government Fiscal Policy Tests
- **File**: `tests/integration/test_government_fiscal_policy.py`
- **Current State**: Calls `government.collect_tax(...)` which is deprecated/removed.
- **Target Logic**:
  - Remove direct calls to `collect_tax`.
  - Simulate tax collection by invoking `government.tax_service.record_revenue(...)` directly if testing internal state, OR
  - **Preferred**: Use `settlement_system.transfer(payer, government, ...)` to simulate the economic event and assert `government.tax_revenue` updates.
- **Refactoring Plan**:
  ```python
  def test_tax_collection_mechanism(government):
      # ... setup ...
      # Replace government.collect_tax(...) with:
      tx_result = government.settlement_system.transfer(
          payer, government, amount, "income_tax", currency=DEFAULT_CURRENCY
      )
      
      # Manually trigger revenue recording if not hooked via signals yet
      # (Depending on if SettlementSystem emits events or if we need to call service)
      government.record_revenue({
          "amount_collected": amount,
          "tax_type": "income_tax",
          # ...
      })
      
      assert government.get_balance() == expected_balance
  ```

### 2.2. Component: Audit Integrity (Birth Gift)
- **File**: `tests/system/test_audit_integrity.py`
- **Current State**: Mocks `HouseholdFactory` class, preventing the actual transfer logic in `create_newborn` from running.
- **Target Logic**:
  - Use **Real** `HouseholdFactory`.
  - Mock **Context** (`HouseholdFactoryContext`) and `SettlementSystem`.
  - Verify `settlement_system.transfer` is called with integer amounts.
- **Refactoring Plan**:
  - Instantiate `HouseholdFactory` with a `HouseholdFactoryContext` containing a mocked `SettlementSystem`.
  - Pass this factory to `DemographicManager`.
  - Assert `mock_settlement_system.transfer.assert_called_with(...)`.

### 2.3. Component: Transaction Handlers (Mock Hardening)
- **File**: `tests/unit/test_transaction_handlers.py`
- **Current State**: Mocks use `spec=ISolvent`. If `ISolvent` protocol lacks `id`, `mock.id` access fails or is fragile.
- **Target Logic**:
  - Define `MockFinancialAgent` class or use `MagicMock(spec=IFinancialAgent)` which definitely includes `id`.
  - Ensure `government` mock implements `ITaxCollector` AND `IFinancialAgent` (or at least has `id`).
- **Refactoring Plan**:
  ```python
  # Ensure mocks have IDs
  self.buyer = MagicMock(spec=ISolvent)
  self.buyer.id = 1
  self.seller = MagicMock(spec=ISolvent) 
  self.seller.id = 2
  self.government = MagicMock(spec=ITaxCollector)
  self.government.id = 99
  ```

### 2.4. Component: Agent Factory Tests
- **File**: `tests/simulation/factories/test_agent_factory.py`
- **Current State**: Instantiates `HouseholdFactory` with raw `config_module`.
- **Target Logic**:
  - Instantiate with `HouseholdFactoryContext`.
- **Refactoring Plan**:
  ```python
  context = HouseholdFactoryContext(
      core_config_module=mock_config,
      household_config_dto=...,
      goods_data=[],
      # ... other fields mocked ...
  )
  factory = HouseholdFactory(context)
  ```

### 2.5. Component: Government Refactor Tests
- **File**: `tests/integration/test_government_refactor_behavior.py`
- **Current State**: Imports `GovernmentDecisionEngine`.
- **Target Logic**:
  - Import `FiscalEngine` from `modules.government.engines.fiscal_engine`.
  - Test `FiscalEngine.decide` with `FiscalStateDTO`.
- **Refactoring Plan**:
  - Rename test class to `TestFiscalEngine`.
  - Construct inputs matching `FiscalEngine.decide(fiscal_state, market_snapshot, requests)`.

### 2.6. Component: Tax Collection Unit Test
- **File**: `tests/unit/test_tax_collection.py`
- **Current State**: Tests `government.collect_tax` adapter.
- **Target Logic**:
  - Deprecate/Remove `test_government_collect_tax_adapter_*` tests if the method is gone.
  - Or update to test `Government.tax_service.calculate_tax_liability`.

## 3. Risk Assessment

- **Legacy Dependency**: `LaborTransactionHandler` (production code) might still be calling `collect_tax`. If so, removing the test without fixing the handler will hide a bug.
  - **Mitigation**: I will check `LaborTransactionHandler` logic (via tests) and if it fails, I will flag it. The immediate task is ensuring tests match the *current intended* architecture.
- **Context Complexity**: `HouseholdFactoryContext` has many fields. Mocking all of them might be verbose.
  - **Mitigation**: Use a helper `create_mock_context()` in `conftest.py` if needed.

## 4. Verification Plan

1.  **Run Affected Tests**:
    ```bash
    pytest tests/integration/test_government_fiscal_policy.py
    pytest tests/system/test_audit_integrity.py
    pytest tests/unit/test_transaction_handlers.py
    pytest tests/simulation/factories/test_agent_factory.py
    pytest tests/integration/test_government_refactor_behavior.py
    ```
2.  **Audit Output**: Ensure no `AttributeError` or `ImportError`.
3.  **Zero-Sum Check**: `test_audit_integrity.py` must pass, confirming integer math on birth gifts.

---

# 📝 Spec: Test Modernization

## 1. `tests/conftest.py` (Update)

Add fixtures for `HouseholdFactoryContext` if not present.

```python
@pytest.fixture
def mock_household_factory_context(mock_config_module):
    from modules.household.api import HouseholdFactoryContext
    return HouseholdFactoryContext(
        core_config_module=mock_config_module,
        household_config_dto=MagicMock(),
        goods_data=[],
        loan_market=MagicMock(),
        ai_training_manager=MagicMock(),
        settlement_system=MagicMock(),
        markets={},
        memory_system=MagicMock(),
        central_bank=MagicMock(),
        demographic_manager=MagicMock()
    )
```

## 2. `tests/system/test_audit_integrity.py` (Refactor)

```python
# ... imports ...
from modules.household.api import HouseholdFactoryContext
from simulation.factories.household_factory import HouseholdFactory

class TestEconomicIntegrityAudit(unittest.TestCase):
    # ... setUp ...

    def test_birth_gift_rounding(self):
        """
        Verify that birth gift is calculated in pennies (integer) using REAL Factory logic.
        """
        # 1. Setup Context & Dependencies
        mock_settlement = MagicMock()
        mock_config = self.config
        
        context = HouseholdFactoryContext(
            core_config_module=mock_config,
            household_config_dto=MagicMock(),
            goods_data=[],
            loan_market=MagicMock(),
            ai_training_manager=MagicMock(),
            settlement_system=mock_settlement,
            markets={},
            memory_system=MagicMock(),
            central_bank=MagicMock(),
            demographic_manager=MagicMock()
        )
        
        # 2. Instantiate Real Factory
        real_factory = HouseholdFactory(context)
        
        # 3. Setup Manager with Real Factory
        dm = DemographicManager(config_module=mock_config, household_factory=real_factory)
        dm.settlement_system = mock_settlement # Redundant if factory uses context, but safe
        
        # 4. Setup Parent
        parent = MagicMock()
        parent.id = 10
        parent.age = 30
        parent.wallet = MagicMock()
        parent.wallet.get_balance.return_value = 10000  # 100.00
        # ... other parent attributes ...
        
        # 5. Execute
        # process_births calls factory.create_newborn -> context.settlement_system.transfer
        dm.process_births(MagicMock(), [parent])
        
        # 6. Verify Transfer
        # Expect 10% of 10000 = 1000
        args = mock_settlement.transfer.call_args
        self.assertIsNotNone(args)
        
        # args[1] is kwargs usually, or check positional
        # Signature: (sender, receiver, amount, ...)
        # Check call_args_list if multiple
        
        amount = args[0][2] # Assuming positional
        self.assertIsInstance(amount, int)
        self.assertEqual(amount, 1000)
```

## 3. `tests/unit/test_transaction_handlers.py` (Refactor)

Explicitly set `id` on mocks to satisfy potential protocol checks or attribute access.

```python
    def setUp(self):
        # ...
        self.buyer = MagicMock(spec=ISolvent)
        self.buyer.id = 1  # Explicit ID
        self.seller = MagicMock(spec=ISolvent)
        self.seller.id = 2 # Explicit ID
        
        self.government = MagicMock(spec=ITaxCollector)
        self.government.id = 99 # Explicit ID
        # ...
```

## 4. `tests/simulation/factories/test_agent_factory.py` (Refactor)

Use `HouseholdFactoryContext`.

```python
def test_create_household(mock_config_module):
    # Setup Context
    context = HouseholdFactoryContext(
        core_config_module=mock_config_module,
        household_config_dto=MagicMock(),
        goods_data=[],
        # ...
    )
    
    factory = HouseholdFactory(context)
    
    # ... rest of test ...
```

## 5. `tests/integration/test_government_refactor_behavior.py` (Refactor)

Target `FiscalEngine`.

```python
    def test_fiscal_engine_logic(self, mock_config):
        from modules.government.engines.fiscal_engine import FiscalEngine
        from modules.government.engines.api import FiscalStateDTO
        
        engine = FiscalEngine(mock_config)
        
        state: FiscalStateDTO = {
            "tick": 1,
            "assets": {"USD": 1000},
            "total_debt": 0,
            "income_tax_rate": 0.1,
            "corporate_tax_rate": 0.2,
            "approval_rating": 0.5,
            "welfare_budget_multiplier": 1.0,
            "potential_gdp": 1000.0
        }
        
        market_snapshot = {
            "tick": 1,
            "inflation_rate_annual": 0.0,
            "current_gdp": 800.0
        }
        
        decision = engine.decide(state, market_snapshot, [])
        
        # Assert outputs (TypedDict)
        assert "new_income_tax_rate" in decision
```

---

## 📢 Reporting

As per mandatory instruction, `communications/insights/modernize-tests.md` will be created with:
1.  Summary of changes (Factory Pattern adoption, Deprecation cleanup).
2.  Logs of passing tests.

**[Debt Review]**:
-   **Resolves**: `TD-TEST-MOCK-STALE` (partially), `TD-DEPR-GOV-TAX` (in tests).
-   **New Risk**: None identified; strict type enforcement improves stability.

---
**Status**: Ready for Implementation.