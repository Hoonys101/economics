# Post-Merge Stabilization Fixes

## 1. Integration & Stress Test Regressions

### Architectural Insights
#### Protocol Purity and Zero-Sum Integrity
To adhere to the "Protocol Purity" guardrail and avoid using `hasattr`, we introduced a new `@runtime_checkable` Protocol `IMintingSystem` in `simulation/finance/api.py`. This protocol defines the `mint_and_distribute` method, which is used for "God Mode" operations like hyperinflation scenarios.

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
The previous priority configuration (`SYSTEM=10`, `CONFIG=0`) incorrectly allowed internal system defaults to override user-provided configuration files. By inverting this to `SYSTEM=0` (Base Layer) and `CONFIG=10` (Override Layer), we restore the standard configuration hierarchy where external configs take precedence over hardcoded defaults.

#### Protocol Drift & Mock Fidelity
The regression in `tests/system/test_phase29_depression.py` highlighted two critical issues:
1.  **DTO Synchronization**: `MarketSignalDTO` had evolved to require `total_bid_quantity` and `total_ask_quantity`.
2.  **Mock Completeness**: The `config_module` mock was missing numerous fields required by `HouseholdConfigDTO` (e.g., `TARGET_FOOD_BUFFER_QUANTITY`, `WAGE_DECAY_RATE`). This reinforces the need for mocks to strictly adhere to the schemas of the objects they impersonate.

### Test Evidence
#### tests/system/test_phase29_depression.py
```
======================== 2 passed, 2 warnings in 3.38s =========================
```

---

## 3. Server Integration & Async Dependencies

### Architectural Insights
*   **Dependency Management**: Cleaned up `requirements.txt` to remove redundant `pytest-asyncio` entries and pinned the version to `>=0.24.0`.
*   **Async Testing Configuration**: Verified `pytest.ini` enforces `asyncio_default_fixture_loop_scope = function`, ensuring test isolation.
*   **Server Integration**: Integration tests correctly utilize a threaded `SimulationServer` alongside async test functions for safe network simulation.

### Test Evidence
```bash
$ pytest tests/integration/test_server_integration.py
============================== 2 passed in 2.95s ===============================
```

---

## 4. Household Module DTO Schema Mismatch

### Architectural Insights
*   **Schema Evolution Risk**: `MarketSnapshotDTO` (in `modules/system/api.py`) now enforces `market_data` as a required field. Independent unit tests for the Household module were broken due to this structural change.
*   **Test Hygiene**: The fix applied (`market_data={}`) is a temporary measure to restore build stability. This regression highlights the urgent need for a centralized **DTO Factory** in the test suite to prevent "Shotgun Surgery" when shared DTO architectures evolve.

### Test Evidence
#### tests/unit/modules/household/test_decision_unit.py
```
======================== 2 passed, 2 warnings in 0.19s =========================
```

---

## 5. PublicManager DTO Signature Mismatch
### Architectural Insights
- **Liquidity Analysis**: `MarketSignalDTO` now includes `total_bid_quantity` and `total_ask_quantity`.
- **Fixture Sync**: Updated `PublicManager` tests to provide these required liquidity fields.

### Test Evidence
```bash
$ pytest tests/unit/modules/system/execution/test_public_manager_compliance.py
============================== 4 passed in 0.18s ===============================
```

---

## 6. Stress Test Rollback Assertion
### Architectural Insights
- **Snapshot Fidelity**: `CommandService` requires `registry.get_entry()` to be mocked with a concrete `RegistryEntry`, not a `MagicMock`, to prevent "Mock Leaks" into the undo history.
- **Rollback Provenance**: Rollback logic correctly restores the *original* origin (e.g., `OriginType.CONFIG`), not the intervention origin (`GOD_MODE`).

### Test Evidence
```bash
$ pytest tests/integration/mission_int_02_stress_test.py
============================== 4 passed in 0.23s ===============================
```
