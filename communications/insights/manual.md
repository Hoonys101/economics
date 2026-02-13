# Post-Merge Stabilization Fixes

## 1. Integration & Stress Test Regressions

### Architectural Insights
#### Protocol Purity and Zero-Sum Integrity
To adhere to the "Protocol Purity" guardrail and avoid using `hasattr`, we introduced a new `@runtime_checkable` Protocol `IMintingSystem` in `simulation/finance/api.py`. This protocol defines the `mint_and_distribute` method, which is used for "God Mode" operations like hyperinflation scenarios.

The `EventSystem` now explicitly checks if the `settlement_system` implements this protocol using `isinstance(settlement_system, IMintingSystem)` before attempting to mint currency. This ensures type safety and clarity about which systems support monetary injection, aligning with the "Zero-Sum Integrity" principle where money creation is a privileged operation.

#### DTO Strictness
The `MarketSnapshotDTO` now strictly requires `market_data` to be initialized. This change caused regressions in integration tests where DTOs were instantiated with missing fields. We updated all affected tests to provide `market_data={}`, ensuring compliance with the updated DTO schema.

#### Integer Currency
We observed that `SettlementSystem` operations require integer amounts (pennies) to prevent floating-point errors. The stress scenarios were updated to cast calculated injection amounts to `int` before calling settlement methods, reinforcing the system's financial integrity.

### Test Evidence
```bash
$ pytest tests/integration/test_decision_engine_integration.py tests/integration/scenarios/test_stress_scenarios.py
======================== 13 passed, 2 warnings in 0.26s ========================
```

---

## 2. System Registry Priority & Mocks

### Architectural Insights
#### Registry Priority Inversion
The previous priority configuration (`SYSTEM=10`, `CONFIG=0`) incorrectly allowed internal system defaults to override user-provided configuration files. By inverting this to `SYSTEM=0` (Base Layer) and `CONFIG=10` (Override Layer), we restore the standard configuration hierarchy where external configs take precedence over hardcoded defaults. This change ensures that `config/__init__.py` (verified to use `OriginType.SYSTEM`) serves as the true fallback baseline.

#### Protocol Drift & Mock Fidelity
The regression in `tests/system/test_phase29_depression.py` highlighted two critical issues:
1.  **DTO Synchronization**: `MarketSignalDTO` had evolved to require `total_bid_quantity` and `total_ask_quantity`, but the `Phase_SystemicLiquidation` implementation (and subsequently the test execution path) had not been updated. This caused a `TypeError` during test execution.
2.  **Mock Completeness**: The `config_module` mock was missing numerous fields required by `HouseholdConfigDTO` (e.g., `TARGET_FOOD_BUFFER_QUANTITY`, `WAGE_DECAY_RATE`), which are mandatory for agent initialization. This reinforces the need for mocks to strictly adhere to the schemas of the objects they impersonate.

### Optimization
In `Phase_SystemicLiquidation`, calculating `total_bid_quantity` and `total_ask_quantity` provided an opportunity to optimize `order_book_depth` calculations. Instead of accessing the expensive `buy_orders` property (which constructs DTOs), we now utilize the lightweight `get_all_bids()` method to sum quantities and compute length, reducing overhead during signal generation.

## [Test Evidence]

### tests/system/test_phase29_depression.py
```
tests/system/test_phase29_depression.py::TestPhase29Depression::test_crisis_monitor_logging PASSED [ 50%]
tests/system/test_phase29_depression.py::TestPhase29Depression::test_depression_scenario_triggers PASSED [100%]
======================== 2 passed, 2 warnings in 3.38s =========================
>>>>>>> origin/fix-registry-priority-mocks-3161058196102907555
```
