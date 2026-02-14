# Post-Merge Stabilization Fixes

## 1. Integration & Stress Test Regressions
### Architectural Insights
- **Protocol Purity**: Introduced `@runtime_checkable` `IMintingSystem` to avoid `hasattr`.
- **DTO Strictness**: `MarketSnapshotDTO` now strictly requires `market_data`.
- **Integer Currency**: Enforced `int` casting in `SettlementSystem` to prevent float drift.

## 2. System Registry Priority & Mocks
### Architectural Insights
- **Priority Inversion**: Inverted registry priority to `SYSTEM=0`, `CONFIG=10` to allow user overrides.
- **Mock Fidelity**: Updated `MarketSignalDTO` and `config_module` mocks to match evolved schemas.

## 3. Server Integration & Async Dependencies
### Architectural Insights
- **Dependency Sync**: Pinned `pytest-asyncio >= 0.24.0`.
- **Async Isolation**: Enforced `function` loop scope in `pytest.ini`.

## 4. Household Module DTO Schema Mismatch
### Architectural Insights
- **Schema Evolution**: Standardized `market_data={}` across unit tests.
- **Future Debt**: Identified need for a centralized **DTO Factory**.

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
