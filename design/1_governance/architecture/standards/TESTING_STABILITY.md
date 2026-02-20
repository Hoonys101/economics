# 🧪 Testing Standard: Integrity & Stability

## 🔍 Context
Test failures in isolated/lean environments often stem from brittle mocks and library dependencies that drift from production code.

---

## 🛡️ Hard Rules

### 1. Mock Purity (Preventing MagicMock Poisoning)
- **Primitive Injection is Mandatory**: When mocking objects or their sub-states (e.g., `agent.social_state`), you MUST configure the mock to return primitive values (int, float, bool, str) for any attributes that will be accessed. By default, a `MagicMock` returns another `MagicMock`, which is not serializable.
  - **WRONG (CRITICAL VIOLATION)**: `h = MagicMock()` -> `h.social_state.conformity` returns another `MagicMock`. This will crash any system that creates a DTO from this agent.
  - **RIGHT**: `h.social_state.conformity = 0.5`.
- **Serialization Check**: Any mock that will be passed into a `get_state_dto()` call, logged, or persisted MUST be configured to respond with serializable types for all accessed attributes.

### 2. Golden Fixture Priority
- **Prefer Real State**: Test logic MUST prefer loading a "Golden Sample" (a serialized snapshot of a real agent state) over manual `MagicMock` construction for complex objects like `Firm` or `Household`. Manual mocks are brittle and cause "Test Mock Drift" as production code evolves.
- **Standard Fixtures**: Use the pre-defined fixtures `golden_households`, `golden_firms`, and `golden_ledger` from `conftest.py` whenever possible.
- **Mock Factories**: If a custom mock is unavoidable, it should be generated via a dedicated Factory function that ensures all necessary attributes and DTO-related fields are populated with correct primitive types.

### 3. External Dependency Faking
- **Fake Objects**: For complex libraries like `numpy` or `yaml`, use specialized "Fake" classes (e.g., `FakeNumpy`) that implement the minimal interface with primitive return values.

### 4. Protocol Compliance
- **Strict Mocking**: Always create mocks with `spec=IProtocol` (e.g., `MagicMock(spec=IFinancialEntity)`) to ensure the mock fails immediately if the underlying interface changes. This prevents "Mock Drift" where tests pass against an outdated API.

### 5. Test Collection & Packaging
- **Explicit Packages**: All subdirectories within `tests/` MUST contain an `__init__.py` file to be recognized as proper Python packages. This prevents `import file mismatch` errors and namespace collisions during test collection.
- **Unique Test Filenames**: Test files should be named uniquely across the entire project (e.g., `test_service_unit.py` vs `test_service_int.py`) to avoid conflicts when `pytest` collects tests from multiple directories.
- **Absolute Path Resolution**: Code that loads configuration files or resources (e.g., `SchemaLoader`) MUST resolve paths relative to `__file__` using `pathlib.Path`, rather than relying on `os.getcwd()` or relative paths. This ensures tests run correctly regardless of the execution context.

### 6. Data Structure Fidelity (DTOs vs Dicts)
- **No Raw Dictionaries for DTOs**: When testing components that expect a DTO (Data Transfer Object), NEVER pass a raw dictionary.
  - **Risk**: Production components often use dot-notation (`obj.field`) which fails on dictionaries (`obj['field']`), or vice-versa.
  - **Requirement**: Instantiate the actual DTO class (e.g., `HousingTransactionSagaStateDTO`) with test data. This validates the DTO's `__init__` signature and ensures the test object matches the runtime object structure.

---

## 🚨 Violations
- **Severity: High**: Tests failing with `MagicMock is not JSON serializable`.
- **Severity: Medium**: Over-mocking that hides real logic drift between Agents and DTOs.

