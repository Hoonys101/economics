# Insight Report: Registry & System Integrity Fixes

## Architectural Insights

### Registry Service Lock
The `MissionRegistryService` was failing due to a missing `LOCK_PATH` module-level constant which was expected by tests and potentially other consumers.
- **Fix**: Restored `LOCK_PATH` in `_internal/registry/service.py` pointing to `_internal/registry/mission_db.lock`.
- **Improvement**: Updated `MissionLock.__init__` to use `LOCK_PATH` as a fallback via runtime lookup (`lock_file or LOCK_PATH`) rather than a bind-time default argument. This allows tests to patch `LOCK_PATH` effectively without needing to patch the class constructor, improving testability and robustness.

### M2 Integrity Leak
The `MonetaryLedger` was incorrectly classifying `loan_interest` as M2 contraction and `deposit_interest` as M2 expansion.
- **Analysis**: While these transactions affect agent balances, they represent transfers of existing money (between Banks and Agents) rather than the creation or destruction of money supply (M2).
- **Fix**: Removed `deposit_interest` from the expansion list and `loan_interest` from the contraction list in `modules/government/components/monetary_ledger.py`.
- **Result**: Validated that internal transfers are now neutral (0.0 delta) in M2 calculations, adhering to the "Zero-Sum Integrity" guardrail.

## Test Evidence

```
tests/unit/registry/test_service.py::test_load_missions_empty PASSED     [ 10%]
tests/unit/registry/test_service.py::test_register_and_get_mission PASSED [ 20%]
tests/unit/registry/test_service.py::test_delete_mission PASSED          [ 30%]
tests/unit/registry/test_service.py::test_get_mission_prompt PASSED      [ 40%]
tests/unit/registry/test_service.py::test_migration PASSED               [ 50%]
tests/unit/registry/test_service.py::test_lock_timeout PASSED            [ 60%]
tests/unit/registry/test_service.py::test_lock_success PASSED            [ 70%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_credit_creation_expansion PASSED [ 80%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_credit_destruction_contraction PASSED [ 90%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_internal_transfers_are_neutral PASSED [100%]

============================== 10 passed in 0.46s ==============================
```
