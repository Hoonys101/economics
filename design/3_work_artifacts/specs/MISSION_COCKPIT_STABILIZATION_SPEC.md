File: design\3_work_artifacts\specs\spec-cockpit-stabilization.md
```markdown
# Spec: Cockpit 2.0 Stabilization (Test Fixes)

## 1. Executive Summary
This specification outlines the necessary refactoring to stabilize the codebase following the migration to Pydantic-based DTOs (`RegistryValueDTO`, `ParameterSchemaDTO`) in Cockpit 2.0. The migration introduced strict schema validation which broke legacy unit tests and the Dashboard UI that relied on dictionary-style access or incomplete object instantiation.

## 2. Targeted Refactoring

### 2.1. Dashboard Controls (`dashboard/components/controls.py`)
**Problem**: The `render_dynamic_controls` function treats `ParameterSchemaDTO` objects as dictionaries (`schema['key']`), causing `TypeError: 'ParameterSchemaDTO' object is not subscriptable`.

**Change Specification**:
- **Target**: `dashboard/components/controls.py`
- **Action**: Replace dictionary subscript syntax with dot notation for all `ParameterSchemaDTO` field accesses.

```python
# BEFORE
key = schema['key']
label = schema['label']
# ...
if schema['category'] == category:

# AFTER
key = schema.key
label = schema.label
# ...
if schema.category == category:
```

### 2.2. Unit Tests (`tests/unit/modules/system/test_command_service_unit.py`)
**Problem**: `RegistryEntry` (alias for `RegistryValueDTO`) is a Pydantic model requiring a `key` field. Tests instantiate it with only `value` and `origin`, raising `pydantic_core.ValidationError`.

**Change Specification**:
- **Target**: `tests/unit/modules/system/test_command_service_unit.py`
- **Action**: Update all `RegistryEntry` instantiations to include the `key` parameter matching the test context.

```python
# BEFORE
previous_entry = RegistryEntry(value=50, origin=OriginType.SYSTEM)

# AFTER
previous_entry = RegistryEntry(key="test_param", value=50, origin=OriginType.SYSTEM)
```

**Specific Locations**:
1. `test_dispatch_set_param`: `key="test_param"`
2. `test_rollback_set_param_restorable`: `key="test_param"`
3. `test_rollback_set_param_fallback`: `key="test_param"`
4. `test_commit_last_tick_clears_stack`: `key="test"`

### 2.3. System Tests (`tests/system/test_command_service_rollback.py`)
**Problem**: Similar `ValidationError` in rollback integration tests.

**Change Specification**:
- **Target**: `tests/system/test_command_service_rollback.py`
- **Action**: Add `key` field to `RegistryEntry` (via `mock_registry` setup).

```python
# IN: test_rollback_set_param_preserves_origin
# The mock_registry.get_entry(key) returns a DTO. 
# We must ensure the mock returns a valid DTO structure if it's not using the real class, 
# or if it IS using the real class (GlobalRegistry), the setup `mock_registry.set` must internally create it correctly.
# NOTE: The test uses `GlobalRegistry` (real implementation).
# GlobalRegistry.set() creates RegistryValueDTO internally. 
# GlobalRegistry.set implementation:
#   new_entry = RegistryValueDTO(key=key, value=value, ...)
# This is ALREADY CORRECT in the source code provided in context.
# HOWEVER, the test setups might be manually creating entries or asserting against them?
# Looking at test code:
#   entry = mock_registry.get_entry(key)
#   assert entry.value == initial_value
# This should work IF GlobalRegistry.set works.
```

**Refined Analysis for 2.3**:
- The failure in `test_command_service_rollback.py` might be due to `UndoRecord` instantiation in `CommandService` if `previous_entry` is invalid, OR if the test manually calls `command_service._handle_set_param(cmd)` which captures `previous_entry`.
- **Logic Check**: `CommandService._handle_set_param` calls `self.registry.get_entry(cmd.parameter_key)`.
- In `test_rollback_set_param_preserves_origin`, `mock_registry` is a real `GlobalRegistry`.
- `GlobalRegistry.set` creates the entry.
- **Hypothesis**: The issue is likely in `test_command_service_rollback.py`'s imports or setup if it relies on `RegistryEntry` generic mocking.
- **Correction**: The provided context for `tests/system/test_command_service_rollback.py` shows it uses `GlobalRegistry`. `GlobalRegistry` uses `RegistryValueDTO`.
- **Action**: If `GlobalRegistry` is real, verify `modules/system/registry.py` imports `RegistryValueDTO`.
    - Context `modules/system/registry.py`: `from modules.system.api import ... RegistryValueDTO ...`
    - Context `modules/system/api.py`: `class RegistryValueDTO(BaseModel): key: str ...`
    - `GlobalRegistry.set`: `new_entry = RegistryValueDTO(key=key, ...)` -> **Correct**.
- **Conclusion**: The failures in `test_command_service_rollback.py` are likely **not** in the registry usage itself, but potentially in how `UndoRecord` is verified or if `RegistryEntry` is manually constructed in other tests within the file (not shown in snippet but implied by "11 failures").
- **Fallback**: If `test_command_service_rollback.py` has tests that *mock* `get_entry` to return a `RegistryEntry` (like `test_rollback_creation_restorable` in unit tests), those need fixing.
    - `tests/unit/...` definitely needs fixing.
    - `tests/system/...` -> Ensure `mock_registry` (if any mocks are used) returns valid DTOs. The provided snippet uses a fixture `mock_registry` returning `GlobalRegistry()`. This *should* work unless `GlobalRegistry` itself is broken.

### 2.4. Command Service (`modules/system/services/command_service.py`)
**Problem**: `UndoRecord` expects `previous_entry` to be `Optional[RegistryEntry]`.
- **Change**: None required in code, but verification needed that `previous_entry` captured from `registry.get_entry()` is a valid Pydantic model.

## 3. Verification Plan

### 3.1. Manual Verification Steps
1. **Apply Fixes**: Update `dashboard/components/controls.py` and `tests/unit/modules/system/test_command_service_unit.py`.
2. **Run Unit Tests**: `pytest tests/unit/modules/system/test_command_service_unit.py` -> EXPECT PASS.
3. **Run System Tests**: `pytest tests/system/test_command_service_rollback.py` -> EXPECT PASS.

### 3.2. Automated Test Case (for new Spec)
Add a test specifically checking `RegistryValueDTO` constraints to ensure future regressions are caught.

```python
def test_registry_value_dto_validation():
    from modules.system.api import RegistryValueDTO, OriginType
    import pytest
    from pydantic import ValidationError

    # Valid
    dto = RegistryValueDTO(key="test", value=1, origin=OriginType.SYSTEM)
    assert dto.key == "test"

    # Invalid (Missing Key)
    with pytest.raises(ValidationError):
        RegistryValueDTO(value=1, origin=OriginType.SYSTEM)
```

## 4. Mandatory Reporting
> The following file MUST be created/updated with insights from this specification work:
> `communications/insights/spec-cockpit-stabilization.md`
```

File: communications\insights\spec-cockpit-stabilization.md
```markdown
# Insight Report: Cockpit 2.0 Stabilization

## 1. Architectural Insights
- **Pydantic Migration Impact**: The shift from `dataclasses` to `pydantic` for `RegistryValueDTO` and `ParameterSchemaDTO` exposed strict validation requirements that were previously ignored by loose dictionary typing or permissive dataclass constructors.
- **UI/Backend Coupling**: `dashboard/components/controls.py` was tightly coupled to the implementation detail (dictionary access) of the schema objects. Moving to Dot Notation aligns with the Object-Oriented interface of Pydantic models and improves type safety, but requires a synchronous update with the backend DTO definitions.
- **Test Fragility**: Unit tests were constructing "partial" objects (`RegistryEntry` without `key`). This highlights a risk where tests do not accurately reflect the production data constraints. Future tests should use "Factory" methods or valid fixtures to generate DTOs rather than manual instantiation.

## 2. Technical Debt Identified
- **TD-TEST-DTO-PARTIAL**: Tests instantiating DTOs with missing required fields.
- **TD-UI-DICT-ACCESS**: UI components accessing DTOs as dictionaries.

## 3. Recommended Actions
- **Immediate**: Apply the specified fixes to `dashboard/components/controls.py` and `tests/unit/modules/system/test_command_service_unit.py`.
- **Long-term**: Introduce a `DTOFactory` in `tests/conftest.py` to generate valid Pydantic models for testing, ensuring all required fields (like `key`) are populated with sensible defaults if not specified.
```