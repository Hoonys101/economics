# Mission Spec: Registry & System Integrity

## Goal
1. Restore `LOCK_PATH` access in Registry service.
2. Resolve the M2 integrity leak in neutral transfers.

## Identified Failures

### 1. Registry Service Lock
- **Error**: `AttributeError: <module '_internal.registry.service'> ... does not have attribute 'LOCK_PATH'`.
- **Cause**: `LOCK_PATH` was moved to an instance attribute `self.lock_path` but tests are likely accessing it via the class or the module.
- **Fix**: Add a module-level or class-level `LOCK_PATH` as a default, or update tests to use `service.lock_path`.

### 2. M2 Integrity Leak
- **Error**: `AssertionError: -100.0 != 0.0` in `test_internal_transfers_are_neutral`.
- **Cause**: `loan_interest` transactions are causing a contraction in `MonetaryLedger`.
- **Fix**: Update `modules/government/components/monetary_ledger.py` to ensure `loan_interest` and `deposit_interest` are treated as neutral transfers (within M2) rather than supply changes.

## Verification
- Run `pytest tests/unit/registry/test_service.py`
- Run `pytest tests/integration/test_m2_integrity.py`
