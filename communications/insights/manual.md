# Fix: Market DTO Schema Synchronization

## [Architectural Insights]

### Root Cause
The DTOs (`MarketContextDTO`, `MarketSnapshotDTO`, `MarketSignalDTO`) were evolved to support new features (e.g., Global Economy, detailed market signals), but the test suite was not refactored in tandem. This led to a schema desynchronization where tests were instantiating DTOs with missing fields or incorrect arguments.

### Tech Debt
The lack of a centralized `DTOFactory` or builder pattern for tests led to brittle "Shotgun Surgery" requirements. Every time a DTO definition changes, multiple test files need to be manually updated. Implementing a factory pattern for DTO instantiation in tests would mitigate this in the future.

### Architectural Decisions
- **Backward Compatibility**: `exchange_rates` was added as an `Optional` field to `MarketContextDTO` to allow existing production code (if any) to continue working without immediate changes, while enabling the new multi-currency logic in tests.
- **DTO Purity**: We enforced the presence of mandatory fields in `MarketSignalDTO` (`total_bid_quantity`, `total_ask_quantity`, `is_frozen`) and `MarketSnapshotDTO` (`market_data`) to ensure strict typing and reliable data contracts across the system.

## [Test Evidence]

### tests/unit/test_sales_engine_refactor.py
```
tests/unit/test_sales_engine_refactor.py::test_adjust_marketing_budget PASSED [ 50%]
tests/unit/test_sales_engine_refactor.py::test_adjust_marketing_budget_zero_revenue PASSED [100%]
======================== 2 passed, 2 warnings in 0.42s =========================
```

### tests/unit/test_household_ai.py
```
tests/unit/test_household_ai.py::test_ai_creates_purchase_order PASSED      [ 50%]
tests/unit/test_household_ai.py::test_ai_evaluates_consumption_options PASSED [100%]
======================== 2 passed, 2 warnings in 0.20s =========================
```

### tests/unit/modules/system/execution/test_public_manager.py
```
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_process_bankruptcy_event PASSED [ 16%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_generate_liquidation_orders PASSED [ 33%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_confirm_sale PASSED [ 50%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_deposit_revenue PASSED [ 66%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_generate_liquidation_orders_no_signal PASSED [ 83%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_generate_liquidation_orders_resets_metrics PASSED [100%]
======================== 6 passed, 2 warnings in 0.15s =========================
```

### tests/integration/test_public_manager_integration.py
```
tests/integration/test_public_manager_integration.py::TestPublicManagerIntegration::test_full_liquidation_cycle PASSED [100%]
======================== 1 passed, 2 warnings in 0.14s =========================
```

### tests/integration/scenarios/diagnosis/test_agent_decision.py
```
tests/integration/scenarios/diagnosis/test_agent_decision.py::test_household_makes_decision PASSED [ 50%]
tests/integration/scenarios/diagnosis/test_agent_decision.py::test_firm_makes_decision PASSED [100%]
======================== 2 passed, 2 warnings in 0.14s =========================
```
