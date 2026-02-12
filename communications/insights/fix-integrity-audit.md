# Fix Integrity Audit Report

## Insight
The `test_birth_gift_rounding` in `test_audit_integrity.py` was failing because `DemographicManager` was initialized without a `HouseholdFactory` (dependency injection missing), and the class lacked a mechanism to resolve it internally. This caused `process_births` to fail silently (caught exception) when trying to create a newborn, skipping the birth gift transfer logic.

Initial attempt to fix by injecting the dependency in the test was rejected because it bypassed the underlying code deficiency (lack of default resolution).

The correct fix involved:
1.  **Implementing Lazy Initialization**: Modified `DemographicManager.process_births` to lazily instantiate `HouseholdFactory` if it is missing, using the `simulation` object to construct the required `HouseholdFactoryContext`. This ensures the class can function without explicit injection, adhering to the design intent implied by the test setup.
2.  **Updating Test Patch**: Updated `test_audit_integrity.py` to patch `simulation.systems.demographic_manager.HouseholdFactory` instead of the deprecated `simulation.factories.agent_factory.HouseholdFactory`. This ensures the test mocks the class actually used by `DemographicManager` (imported from `simulation.factories.household_factory`), allowing the lazy initialization to return a mock instance and verify the birth gift transfer.

## Test Evidence

### `pytest tests/system/test_audit_integrity.py`

```
tests/system/test_audit_integrity.py::TestEconomicIntegrityAudit::test_birth_gift_rounding
-------------------------------- live log call ---------------------------------
WARNING  simulation.systems.demographic_manager:demographic_manager.py:45 DemographicManager initialized without a HouseholdFactory. Births may fail.
INFO     simulation.systems.demographic_manager:demographic_manager.py:48 DemographicManager initialized.
PASSED                                                                   [ 33%]
tests/system/test_audit_integrity.py::TestEconomicIntegrityAudit::test_inheritance_distribution PASSED [ 66%]
tests/system/test_audit_integrity.py::TestEconomicIntegrityAudit::test_public_manager_tax_atomicity PASSED [100%]

============================== 3 passed in 0.11s ===============================
```
