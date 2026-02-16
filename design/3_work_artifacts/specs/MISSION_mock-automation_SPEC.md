# modules/testing/mock_governance/api.py
```python
"""
API Definition for Mock Drift Automation & Protocol Governance.
This module defines the interfaces for creating strictly compliant mocks
and tracking violations where mocks diverge from their defined Protocols.
"""
from __future__ import annotations
from typing import Protocol, Type, Any, TypeVar, List, Optional, runtime_checkable, Dict
from dataclasses import dataclass
from unittest.mock import MagicMock

# Generic Type for Protocols
T = TypeVar("T")

@dataclass
class MockViolationDTO:
    """
    Data Transfer Object representing a detected deviation between a Mock and its Protocol.
    Used for generating the 'Mock Drift' report.
    """
    protocol_name: str
    attribute_name: str
    violation_type: str  # e.g., "UNDEFINED_ATTRIBUTE", "SIGNATURE_MISMATCH"
    location: str        # Test file or function name
    severity: str        # "ERROR" (Fail test) or "WARNING" (Log only)

@runtime_checkable
class IProtocolInspector(Protocol):
    """
    Service interface for analyzing Protocol classes to extract their full contract,
    handling inheritance and MRO (Method Resolution Order) correctly.
    """
    def get_protocol_members(self, protocol_cls: Type[Any]) -> List[str]:
        """
        Returns a list of all public attributes and methods defined in the Protocol,
        including those inherited from parent Protocols.
        """
        ...

    def validate_signature(self, protocol_cls: Type[Any], method_name: str, mock_method: Any) -> bool:
        """
        Checks if the mock's method signature is compatible with the Protocol's definition.
        """
        ...

@runtime_checkable
class IMockFactory(Protocol):
    """
    Centralized factory interface for creating strict mocks.
    Replaces direct `MagicMock()` instantiation in tests.
    """
    def create_mock(self, protocol: Type[T], strict: bool = True, name: Optional[str] = None) -> T:
        """
        Creates a mock object typed as T.

        Args:
            protocol: The Protocol class to mock.
            strict: If True, uses `spec_set` to forbid creating unknown attributes.
            name: Optional name for debugging.

        Returns:
            A MagicMock instance that strictly adheres to T.
        """
        ...

    def create_autospec(self, target: Any, **kwargs) -> Any:
        """
        Wrapper around unittest.mock.create_autospec with additional Protocol awareness.
        """
        ...

@runtime_checkable
class IMockRegistry(Protocol):
    """
    Registry to track mock usage and enforce policies across the test suite.
    """
    def register_violation(self, violation: MockViolationDTO) -> None:
        """Records a violation."""
        ...

    def get_violations(self) -> List[MockViolationDTO]:
        """Retrieves all recorded violations for reporting."""
        ...

```

# design/3_work_artifacts/specs/mock_drift_automation_spec.md
```markdown
# Specification: Mock Drift Automation & Protocol Enforcement

## 1. Overview
This specification addresses **TD-TEST-MOCK-DRIFT-GEN** (High Priority). The goal is to eliminate "Mock Drift"—a state where test mocks possess attributes or methods that do not exist on the actual `Protocol` interfaces—by introducing a strict `MockFactory` and automated verification mechanisms.

## 2. Problem Statement
Currently, tests often use `MagicMock()` without a `spec` or `spec_set`. This allows tests to pass even if they invoke methods that have been renamed or removed from the actual `Protocol`, leading to false positives in the CI pipeline. Complex Protocols like `IBank` (inheriting `IFinancialAgent`) are particularly prone to this drift.

## 3. Core Components

### 3.1 `ProtocolInspector` (Service)
- **Responsibility**: Inspects a `Protocol` class to build a complete list of valid members.
- **Logic (Pseudo-code)**:
  ```python
  def get_protocol_members(self, protocol_cls):
      members = set()
      # Iterate MRO to support inheritance (e.g., IBank -> IFinancialAgent)
      for base in inspect.getmro(protocol_cls):
          if is_protocol(base):
              members.update(base.__annotations__.keys())
              members.update([name for name, val in base.__dict__.items() if callable(val)])
      return list(members)
  ```
- **Constraints**: Must safely handle `TYPE_CHECKING` imports by inspecting `__annotations__` without triggering circular imports where possible.

### 3.2 `StrictMockFactory` (Component)
- **Responsibility**: Produces `MagicMock` instances with `spec_set` configured to the Protocol.
- **Logic**:
  - Accepts a `Protocol` class.
  - Uses `ProtocolInspector` to get valid members.
  - Instantiates `MagicMock(spec_set=True)` (or `create_autospec` if feasible).
  - **Crucial Step**: If `strict=True`, ensures that setting or getting any attribute NOT in the member list raises `AttributeError`.

### 3.3 `MockDriftPlugin` (Pytest Plugin)
- **Responsibility**: Integrates with Pytest to report violations.
- **Mechanism**:
  - Adds a `--strict-mocks` CLI flag.
  - If enabled, monkeypatches `unittest.mock.MagicMock` (scope-limited) or provides a fixture `strict_mock` that delegates to `StrictMockFactory`.

## 4. Migration Strategy (Opt-in)
To prevent immediate "Stop-the-World" failure of existing tests:
1.  **Phase 1 (Strict Factory)**: Implement `StrictMockFactory`.
2.  **Phase 2 (Opt-in Fixture)**: Introduce `strict_mock` fixture. New tests MUST use this.
3.  **Phase 3 (Decorator)**: Add ` @enforce_strict_protocol` decorator for specific test files.
4.  **Phase 4 (Audit)**: Run with `--report-mock-drift` to generate a list of violations without failing tests.

## 5. Verification Plan

### 5.1 New Test Cases
- **Happy Path**: Create a strict mock of `IFinancialAgent`. Call `deposit()`. Should succeed.
- **Drift Detection**: Create a strict mock of `IFinancialAgent`. Call `non_existent_method()`. Should raise `AttributeError`.
- **Inheritance Check**: Create a strict mock of `IBank`. Call `deposit()` (from parent `IFinancialAgent`) and `grant_loan()` (from `IBank`). Both must succeed.

### 5.2 Existing Test Impact
- **Risk**: Existing tests relying on `mock.some_random_flag = True` will fail if converted to strict mocks.
- **Mitigation**: Existing tests remain on standard `MagicMock` until refactored. The `MockRegistry` will log these as warnings in Phase 4.

### 5.3 Risk & Impact Audit
- **Recursion**: `create_autospec` can cause infinite recursion on certain recursive type hints. The `ProtocolInspector` must handle self-references gracefully.
- **Type Checking Guards**: `api.py` files rely heavily on `if TYPE_CHECKING`. The Inspector must rely on `__annotations__` strings rather than evaluating types at runtime to avoid import errors.

## 6. Mandatory Reporting Instruction
**[CRITICAL]** Upon implementation of this spec, you **MUST** create and populate the following file with your findings and the output of the verification tests:
`communications/insights/mock-drift-automation-spec.md`

- **Content**:
  - "Architectural Insights": Note any Protocols that were difficult to inspect.
  - "Test Evidence": Output of `pytest tests/modules/testing/test_mock_governance.py`.

## 7. API Reference
See `modules/testing/mock_governance/api.py`.
```