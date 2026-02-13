modules/system/api.py
```python
from typing import Protocol, Any, Optional, Union, runtime_checkable
from dataclasses import dataclass
from enum import Enum

class OriginType(Enum):
    SYSTEM = "system"
    USER = "user"
    GOD_MODE = "god_mode"
    # Add other origins as needed

@dataclass
class RegistryEntry:
    value: Any
    origin: OriginType
    is_locked: bool = False

@runtime_checkable
class IGlobalRegistry(Protocol):
    """
    Base interface for the Global Registry.
    """
    def get(self, key: str, default: Any = None) -> Any:
        ...

    def get_entry(self, key: str) -> Optional[RegistryEntry]:
        ...

    def set(self, key: str, value: Any, origin: OriginType = OriginType.SYSTEM) -> bool:
        ...

@runtime_checkable
class IRestorableRegistry(IGlobalRegistry, Protocol):
    """
    Extended interface for Registries that support state restoration/undo operations.
    Required for CommandService rollback functionality.
    """
    def delete_entry(self, key: str) -> bool:
        """
        Removes an entry completely. Used when rolling back a creation.
        Returns True if successful.
        """
        ...

    def restore_entry(self, key: str, entry: RegistryEntry) -> bool:
        """
        Restores a specific entry state (value + origin + lock).
        Used when rolling back a modification.
        Returns True if successful.
        """
        ...
```

design/3_work_artifacts/specs/fix_command_undo_spec.md
```markdown
# Spec: Command Service & Undo System Repair

## 1. Introduction

- **Purpose**: Resolve critical regressions in `CommandService` causing command execution failures and test suite breakages. Address architectural risks regarding `UndoRecord` mismatch and loose typing in rollback logic.
- **Scope**: `modules/system/services/command_service.py` and `tests/unit/modules/system/test_command_service_unit.py`.
- **Goals**:
  1.  Restore command processing by removing shadowed methods.
  2.  Fix `UndoRecord` instantiation in tests to match implementation (`previous_entry`).
  3.  Harden rollback logic by introducing `IRestorableRegistry` protocol (removing `hasattr` checks).

## 2. Detailed Design

### 2.1. Module: `CommandService` (Refactoring)

- **Shadowed Method Removal**:
  - The `pop_commands` method defined at lines 82-87 (returning empty list `[]`) MUST be deleted.
  - The functional `pop_commands` at line 76 must remain the sole entry point for draining the queue.

- **Rollback Logic Hardening**:
  - **Current**: Uses `hasattr(self.registry, 'restore_entry')` which hides dependencies.
  - **New**: Cast `self.registry` to `IRestorableRegistry` (defined in `api.py`) inside `rollback_last_tick` using `isinstance` check or strict typing if possible.
  - **Logic**:
    ```python
    # Pseudo-code for rollback_last_tick refinement
    if record.command_type == "SET_PARAM":
        if isinstance(self.registry, IRestorableRegistry):
            if record.previous_entry is None:
                self.registry.delete_entry(record.parameter_key)
            else:
                self.registry.restore_entry(record.parameter_key, record.previous_entry)
        else:
            # Log critical warning: Registry does not support rollback
            # Fallback to .set() but log the loss of 'origin/lock' fidelity
            pass
    ```

### 2.2. Test Suite Updates (`test_command_service_unit.py`)

- **UndoRecord Instantiation**:
  - All instances of `UndoRecord(..., previous_value=val)` must be updated to `UndoRecord(..., previous_entry=RegistryEntry(value=val, origin=...))`.
  - Requires importing `RegistryEntry` and `OriginType` into the test file.

## 3. Interfaces & APIs

### 3.1. `UndoRecord` (DTO)

No schema change, but strict usage enforcement:
```python
@dataclass
class UndoRecord:
    command_id: UUID
    command_type: str
    target_domain: Optional[str] = None
    parameter_key: Optional[str] = None
    previous_entry: Optional[RegistryEntry] = None # STRICT: Must be RegistryEntry, not raw value
    # ... other fields unchanged
```

### 3.2. `IRestorableRegistry` (New Protocol)

See `modules/system/api.py`.

## 4. Verification Plan

### 4.1. New Test Cases
- **Scenario**: Rollback with `IRestorableRegistry`.
  - **Setup**: Mock a registry implementing `IRestorableRegistry`.
  - **Action**: Execute `SET_PARAM`, then `rollback_last_tick`.
  - **Expect**: `restore_entry` to be called with correct `RegistryEntry`.

- **Scenario**: Rollback with Basic `IGlobalRegistry` (Fallback).
  - **Setup**: Mock a registry NOT implementing `IRestorableRegistry` (only basic `set`).
  - **Action**: Execute `SET_PARAM`, then `rollback_last_tick`.
  - **Expect**: Fallback to `set()` is called, warning logged.

### 4.2. Regression Checks
- Run `pytest tests/unit/modules/system/test_command_service_unit.py`.
- Run `pytest tests/unit/test_god_command_protocol.py`.
- **Success Criteria**: All `TypeError` regarding `previous_value` and `AssertionError` regarding missing calls must be resolved.

## 5. Risk & Impact Audit

### 5.1. Architectural Risks
- **Test Data Coupling**: Tests currently rely on raw values. Forcing `RegistryEntry` usage in tests increases setup verbosity but improves type safety.
- **God Object Persistence**: This fix does NOT address the SRP violations (Bank Run/Inventory logic in CommandService). This remains a technical debt to be logged.

### 5.2. Pre-Implementation Checklist
- [ ] Confirm `modules/system/api.py` exists or create it with `OriginType` and `RegistryEntry`.
- [ ] Ensure `IGlobalRegistry` is available for import in `test_command_service_unit.py`.

## 6. Mandatory Reporting

- **Insight Report**: `communications/insights/spec-fix-command-undo.md` MUST be created summarizing the `pop_commands` shadow bug and the `UndoRecord` schema drift.
- **Tech Debt**: Log the SRP violation of `CommandService` handling "Bank Run" logic directly.

```