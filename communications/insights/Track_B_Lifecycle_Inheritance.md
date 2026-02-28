# [Architectural Insights]
- Completely removed the `get_balance()` fallback from `InheritanceHandler.handle` to strictly enforce Protocol Purity and rely on the Single Source of Truth (`tx.total_pennies`) provided by the `InheritanceManager`. This properly fixes the bug where spouse's shared wallet assets were inadvertently liquidated.
- Refactored `InheritanceHandler.rollback` to ensure double-entry rollback atomicity via `context.settlement_system.execute_multiparty_settlement()`. If an heir fails to pay back their inheritance portion during a rollback, the entire operation correctly aborts instead of causing a partial zero-sum violation.
- Validated `EstateRegistry` logic natively uses `ID_PUBLIC_MANAGER` and `ID_GOVERNMENT` rather than routing escheated funds to `ID_ESCROW`.

# [Regression Analysis]
- Tests in `tests/unit/systems/test_inheritance_manager.py` all continue to pass completely.
- `EscheatmentHandler.rollback` and `InheritanceHandler.rollback` methods now cleanly revert double-entry balance updates.

# [Test Evidence]
```
$ pytest tests/unit/systems/test_inheritance_manager.py
========================= test session starts ==========================
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_distribution_transaction_generation PASSED [ 20%]
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_multiple_heirs_metadata PASSED [ 40%]
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_escheatment_when_no_heirs PASSED [ 60%]
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_zero_assets_distribution PASSED [ 80%]
tests/unit/systems/test_inheritance_manager.py::TestInheritanceManager::test_tax_transaction_generation PASSED [100%]

========================= 5 passed, 1 warning in 0.48s =========================
```

```
$ pytest tests/unit/simulation/registries/test_estate_registry.py
========================= test session starts ==========================
tests/unit/simulation/registries/test_estate_registry.py::TestEstateRegistry::test_process_estate_distribution_to_heir PASSED [ 25%]
tests/unit/simulation/registries/test_estate_registry.py::TestEstateRegistry::test_process_estate_distribution_escheatment_fallback PASSED [ 50%]
tests/unit/simulation/registries/test_estate_registry.py::TestEstateRegistry::test_escheatment_fallback_to_government_id PASSED [ 75%]
tests/unit/simulation/registries/test_estate_registry.py::TestEstateRegistry::test_wealth_orphanage_fix_heir_transfer_fail_triggers_escheatment PASSED [100%]

========================= 4 passed, 1 warning in 0.35s =========================
```