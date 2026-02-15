# Mission Spec: Resident Test Stabilization

## 1. Goal
Fix the 5 failing tests identified after the architecture refactor. Ensure the `GlobalRegistry`, `Config Bridge`, and `CommandService` (undo/rollback) logic is spec-compliant and stable.

## 2. Immediate Fixes

### 2.1. Registry Priority and Locking (Target: `modules/system/registry.py`)
- **Authority**: In `set()`, if the key is locked (`active_entry.is_locked`), **RAISE** `PermissionError` if `origin < OriginType.GOD_MODE`. The current implementation returns `False`, which causes `test_locking_mechanism` to fail.
- **Priority**: In `set()`, if `origin` is strictly lower than `active_entry.origin`, **RETURN** `False`. The current implementation returns `True`, which causes `test_origin_priority` to fail.

### 2.2. Config Bridge Proxy (Target: `config/__init__.py`)
- **Dir Listing**: In `__dir__()`, ensure `"registry"` is included in the returned list. This resolves `tests/unit/modules/system/test_config_bridge.py`.

### 2.3. Command Rollback Integrity (Target: `modules/system/services/command_service.py`)
- **Rollback Effectiveness**: `test_rollback_set_param_preserves_origin` fails because rollback doesn't remove the added layer.
- **Action**: Modify `rollback_last_tick` to explicitly remove the entry from `registry._layers[key][origin]` that was added by the command. This ensures state reverts to the next available lower-priority layer.

### 2.4. Mission Registry Service (Target: `_internal/registry/service.py`)
- **Missing Method**: Add `migrate_from_legacy(self, legacy_file_path: str) -> int` method. It should perform the same logic as the migration in the test, scanning for `JULES_MISSIONS` and `GEMINI_MISSIONS` in a file, registering them, and renaming the file to `.py.bak`.

## 3. Verification Criteria
- `pytest tests/unit/modules/system/test_registry.py` -> **PASS**
- `pytest tests/unit/modules/system/test_config_bridge.py` -> **PASS**
- `pytest tests/unit/registry/test_service.py` -> **PASS**
- `pytest tests/system/test_command_service_rollback.py` -> **PASS**
- Global `pytest` -> **PASS**
