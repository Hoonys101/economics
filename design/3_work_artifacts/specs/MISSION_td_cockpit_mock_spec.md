File: modules/testing/api.py
```python
from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from dataclasses import dataclass

# Import the Target DTO to ensure type alignment
from simulation.dtos.api import SimulationState, SystemCommand, GodCommandDTO

@runtime_checkable
class ISimulationStateBuilder(Protocol):
    """
    Module: Testing
    Protocol for a strict builder that generates SimulationState instances 
    for testing. Ensures that tests do not rely on deprecated fields 
    (like system_command_queue) or ad-hoc mocks.
    """

    def with_time(self, tick: int) -> ISimulationStateBuilder:
        """Sets the current simulation tick."""
        ...

    def with_agent(self, agent_id: int, agent_state: Any) -> ISimulationStateBuilder:
        """Injects an agent into the state."""
        ...

    def with_system_command(self, command: SystemCommand) -> ISimulationStateBuilder:
        """
        Adds a system command to the 'system_commands' list.
        Explicitly replaces legacy 'system_command_queue' usage.
        """
        ...

    def with_god_command(self, command: GodCommandDTO) -> ISimulationStateBuilder:
        """Adds a god command snapshot."""
        ...

    def build(self) -> SimulationState:
        """
        Constructs the SimulationState.
        MUST validate that all required fields (even empty lists) are present.
        """
        ...

@runtime_checkable
class IMockFactory(Protocol):
    """
    Factory for creating strictly-typed mocks of core system components.
    Prevents 'Mock Drift' where mocks diverge from the actual class structure.
    """
    
    def create_state_mock(self, spec_compliant: bool = True) -> Any:
        """
        Returns a MagicMock strictly spec'd to SimulationState.
        """
        ...
```

File: design/3_work_artifacts/specs/cockpit_mock_fix_spec.md
```markdown
# Specification: Cockpit Test Mock Modernization (TD-TEST-COCKPIT-MOCK)

## 1. Context & Objective
- **Goal**: Resolve Technical Debt `TD-TEST-COCKPIT-MOCK` where Cockpit 2.0 tests rely on the deprecated `system_command_queue` attribute of `SimulationState`.
- **Scope**: 
    - Identify all test files utilizing `system_command_queue`.
    - Refactor mocks to use the correct `system_commands` (List[SystemCommand]) or `god_command_snapshot` (List[GodCommandDTO]) fields.
    - Implement a strict `SimulationStateBuilder` to prevent future regression.
- **Reference Standards**: 
    - `SEO_PATTERN.md` (Stateless Engine)
    - `TESTING_STABILITY.md` (Mock Purity)

## 2. Technical Approach

### 2.1. Audit & Cleanup (Logic)
The refactoring process follows a strict "Find-Replace-Verify" loop:

1.  **Discovery**:
    - `grep -r "system_command_queue" tests/`
    - `grep -r "system_command_queue" modules/`
2.  **Mapping Strategy**:
    - **Usage Type A (Injection)**: Test injects a command to be processed.
        - *Old*: `state.system_command_queue.append(cmd)`
        - *New*: `state.system_commands.append(cmd)`
    - **Usage Type B (Assertion)**: Test checks if a command was queued.
        - *Old*: `assert cmd in state.system_command_queue`
        - *New*: `assert cmd in state.system_commands`
3.  **Strict Mocking Implementation**:
    - Replace loose mocks: `mock_state = MagicMock()` 
    - With strict specs: `mock_state = MagicMock(spec=SimulationState)`
    - This will immediately raise `AttributeError` if `system_command_queue` is accessed, enforcing the fix.

### 2.2. Test Infrastructure Updates
We will introduce a `SimulationStateBuilder` in `modules/testing/utils.py` (or similar) to standardize state creation.

```python
# Pseudo-code for Builder Implementation
class SimulationStateBuilder:
    def __init__(self):
        self._state = SimulationState(
            time=0,
            system_commands=[], # Explicitly initialized
            god_command_snapshot=[],
            # ... initialize all other required fields with safe defaults ...
        )

    def with_command(self, cmd):
        self._state.system_commands.append(cmd)
        return self

    def build(self):
        return self._state
```

## 3. Interface Specifications

### 3.1. DTO Impact
- **No changes** to `SimulationState` schema.
- **Strict Enforcement**: The refactor enforces the *existing* schema defined in `simulation/dtos/api.py`.

### 3.2. Affected Test Modules (Predicted)
- `tests/cockpit/test_cockpit_integration.py` (Hypothetical location)
- `tests/simulation/test_tick_orchestrator.py`
- `tests/modules/system/test_command_service.py`

## 4. Verification Plan

### 4.1. Pre-Verification
- Run `pytest` to confirm current failure state (or pass state if the debt is silent).
- Capture baseline failure logs for `TD-TEST-COCKPIT-MOCK`.

### 4.2. Refactor Verification
- **Unit Tests**:
    - Verify `SimulationStateBuilder` correctly populates `system_commands`.
    - Verify `MagicMock(spec=SimulationState)` raises error on `system_command_queue` access.
- **Integration Tests**:
    - Re-run all Cockpit-related tests.
    - Ensure `SystemCommand`s injected via the new field are correctly picked up by the `CommandService` or `Orchestrator`.

### 4.3. Mandatory Report
- Generate `communications/insights/spec_cockpit_test_regression.md` containing:
    - List of modified files.
    - Evidence of `system_command_queue` eradication (0 grep matches).
    - Final `pytest` output showing 100% pass rate.

## 5. Risk & Impact Audit

### 5.1. Mock Drift Risk
- **Risk**: Using `MagicMock(spec=SimulationState)` might reveal *other* missing attributes besides `system_command_queue` that tests were implicitly relying on.
- **Mitigation**: The `SimulationStateBuilder` must populate ALL fields defined in the dataclass `__init__`. We will use `factory-boy` or a custom helper to ensure default values for optional fields (like `monetary_ledger` or `saga_orchestrator`) are provided to avoid `NoneType` errors in consumers.

### 5.2. Circular Dependency
- **Risk**: `SimulationState` imports many DTOs.
- **Mitigation**: The Builder should be placed in `modules/testing` or `tests/utils` to avoid importing test code into production modules.

### 5.3. Legacy Code Compatibility
- **Risk**: Some legacy engine code might *still* be using `system_command_queue` internally (violating the DTO definition).
- **Check**: The `grep` audit must cover `modules/` and `simulation/` source code, not just tests. If source code uses the deprecated field, it must be refactored to use `system_commands`.

## 6. Implementation Checklist
- [ ] Create `communications/insights/spec_cockpit_test_regression.md`.
- [ ] Implement `SimulationStateBuilder` in `tests/utils/builders.py`.
- [ ] `grep` codebase for `system_command_queue`.
- [ ] Refactor source code (if any) to use `system_commands`.
- [ ] Refactor tests to use `SimulationStateBuilder` or strict mocks.
- [ ] Verify 0 occurrences of deprecated field.
- [ ] Run full test suite.
```

File: design/2_operations/ledgers/TECH_DEBT_LEDGER.md
```markdown
### ID: TD-TEST-COCKPIT-MOCK
- **Title**: Cockpit 2.0 Mock Regressions
- **Symptom**: Tests usage of deprecated `system_command_queue` on `SimulationState` mocks.
- **Risk**: Silent failure where tests pass but test nothing (phantom queue), leading to runtime errors in Cockpit 2.0.
- **Solution**: 
    1. Implement `SimulationStateBuilder` for strict DTO compliance.
    2. Replace all `system_command_queue` references with `system_commands`.
    3. Enforce `MagicMock(spec=SimulationState)` in all related tests.
- **Status**: **IN PROGRESS** (Spec Created)
```