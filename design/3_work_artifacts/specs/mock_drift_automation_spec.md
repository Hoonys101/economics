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
