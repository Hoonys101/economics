# Insight Report: Platform Robustness Fix (WO-FIX-PLATFORM-TESTS)

## 1. Architectural Insights

### 1.1. Lock Manager Robustness
The `PlatformLockManager` was identified as having potential robustness issues, particularly regarding:
- **Missing Locking Primitives**: If `fcntl` (Unix) or `msvcrt` (Windows) were missing, the manager would log a warning and return success, effectively running without a lock. This defeats the purpose of the lock manager.
- **Windows File Position**: On Windows (using `msvcrt`), file locking is position-dependent. Using `open(..., 'a+')` sets the file pointer to the end, potentially causing different processes to lock different regions of the file if not reset.

**Decision**:
- Enforced strict failure (`LockAcquisitionError`) if locking primitives are unavailable.
- Added explicit `seek(0)` before locking on Windows to ensure consistent locking of the file header.

### 1.2. Configuration Migration (Labor Market)
The `LaborMarket` configuration structure has evolved from a raw dictionary (`LABOR_MARKET`) to a structured DTO (`LaborMarketConfigDTO`).
- **Legacy**: `labor_market.config.LABOR_MARKET["compatibility"]`
- **New Architecture**: `labor_market.config.compatibility` (Flattened attributes on the DTO).

**Decision**:
- Updated `tests/system/test_labor_config_migration.py` to assert against the flattened DTO structure, aligning the test with the current architecture.

## 2. Regression Analysis

### 2.1. `test_lock_manager_robustness.py`
- **Issue**: The test expected `LockAcquisitionError` when a second process tried to acquire the lock. If the lock manager failed silently (due to missing primitives or logic errors), the error wasn't raised, causing the test failure.
- **Fix**: Hardened `PlatformLockManager` to raise errors when locking fails or primitives are missing. Added `seek(0)` to prevent race conditions on Windows.

### 2.2. `test_labor_config_migration.py`
- **Issue**: `test_labor_market_config_loaded` failed because it tried to access the legacy `LABOR_MARKET` attribute on the `LaborMarketConfigDTO`.
- **Fix**: Updated the test to access `compatibility` directly on the config object.

## 3. Test Evidence

The following output demonstrates that all affected tests now pass.

```
tests/test_lock_manager_robustness.py::TestLockManagerRobustness::test_acquire_creates_pid_file
-------------------------------- live log call ---------------------------------
INFO     modules.platform.infrastructure.lock_manager:lock_manager.py:56 Acquired exclusive lock on test_simulation.lock
INFO     modules.platform.infrastructure.lock_manager:lock_manager.py:193 Released lock on test_simulation.lock
PASSED                                                                   [ 14%]
tests/test_lock_manager_robustness.py::TestLockManagerRobustness::test_recover_stale_lock_file
-------------------------------- live log call ---------------------------------
INFO     modules.platform.infrastructure.lock_manager:lock_manager.py:56 Acquired exclusive lock on test_simulation.lock
INFO     modules.platform.infrastructure.lock_manager:lock_manager.py:193 Released lock on test_simulation.lock
PASSED                                                                   [ 28%]
tests/test_lock_manager_robustness.py::TestLockManagerRobustness::test_fail_on_active_lock
-------------------------------- live log call ---------------------------------
INFO     modules.platform.infrastructure.lock_manager:lock_manager.py:56 Acquired exclusive lock on test_simulation.lock
INFO     modules.platform.infrastructure.lock_manager:lock_manager.py:193 Released lock on test_simulation.lock
PASSED                                                                   [ 42%]
tests/system/test_labor_config_migration.py::TestLaborConfigMigration::test_household_majors_assigned PASSED [ 57%]
tests/system/test_labor_config_migration.py::TestLaborConfigMigration::test_firm_majors_mapped PASSED [ 71%]
tests/system/test_labor_config_migration.py::TestLaborConfigMigration::test_labor_market_config_loaded PASSED [ 85%]
tests/system/test_labor_config_migration.py::TestLaborConfigMigration::test_firm_config_dto_has_labor_market PASSED [100%]

========================= 7 passed, 1 warning in 0.54s =========================
```
