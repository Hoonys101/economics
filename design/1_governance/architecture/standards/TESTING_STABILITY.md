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

---

## 🚨 Violations
- **Severity: High**: Tests failing with `MagicMock is not JSON serializable`.
- **Severity: Medium**: Over-mocking that hides real logic drift between Agents and DTOs.
