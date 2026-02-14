# Audit Specification: Test Fidelity & Isolation

This specification defines the principles and criteria for auditing the test suite to ensure high fidelity, reliability, and isolation. It focuses on preventing common mocking pitfalls and global state pollution.

## 1. Auditing Principles

### 1.1 Interface Fidelity (The "MagicMock" Rule)
Mocks must strictly adhere to the interfaces of the objects they replace.
- **Rule**: Use `autospec=True` (or `spec=RealClass`) whenever possible.
- **Why**: Prevents "False Positives" where tests pass on renamed or removed methods.
- **Exception**: Ad-hoc mocks for simple data bags (though DTOs are preferred).

### 1.2 Global Namespace Purity
Tests must not permanently alter the global environment.
- **Rule**: No module-level (top-level) manipulation of `sys.modules`.
- **Rule**: Use `unittest.mock.patch` or `pytest` monkeypatch fixtures for scoped changes.
- **Why**: Prevents cross-test interference and "Shadowing" errors (e.g., websockets is not a package).

### 1.3 Package Mocking Protocol
When mocking a package/module that contains submodules:
- **Rule**: Any mock assigned to `sys.modules` must have `mock.__path__ = []`.
- **Why**: Satisfies Python's import system which expects packages to have a path attribute.

### 1.4 State Isolation & Cleanliness
- **Rule**: Each test must start with a clean state.
- **Rule**: Reset singletons and clear shared caches in `setUp`/`tearDown` or via fixtures.
- **Detection**: Look for `Mock` objects leaking into `simulation` snapshots or persistence logs.

## 2. Audit Criteria (Checklist)

| ID | Category | Checkpoint | Severity |
|:---|:---|:---|:---|
| FID-01 | Mocking | Is `MagicMock` used without `autospec` for core classes? | High |
| ISO-01 | Isolation | Is `sys.modules` modified at the module level (outside functions)? | Critical |
| ISO-02 | Isolation | Do mocked packages lack the `__path__` attribute? | High |
| LEAK-01 | Leakage | Are Mock objects persisting in shared caches/singletons after test? | Medium |
| FID-02 | Data | Are pure mocks used where a real DTO/Dataclass would be safer? | Medium |

## 3. Reporting Format

Audit reports must follow this structure for each identified issue:

- **File**: `tests/path/to/test_file.py`
- **Location**: Line number or Function name
- **Issue**: Short description (e.g., "Non-scoped sys.modules manipulation")
- **Severity**: Critical / High / Medium / Low
- **Fix Suggestion**: Specific code correction or refactoring advice.

## 4. Remediation Guidelines

1. **Relocate Mocks**: Move "Mock if missing" logic for CI/Sandbox to `tests/conftest.py`.
2. **Scope Mocks**: Use context managers or fixtures for temporary mocks.
3. **Formalize Fakes**: If a mock becomes too complex, create a dedicated `FakeModule` class in `tests/mocks/`.
