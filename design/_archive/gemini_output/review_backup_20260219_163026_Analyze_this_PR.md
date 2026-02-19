# 🐙 Gemini CLI System Prompt: Git Reviewer

## 📝 Code Review Report

### 1. 🔍 Summary
This PR addresses "Mock Drift" in the Governance module tests by enforcing **Spec-Based Mocking** (`spec=Government`). This ensures that mocks strictly adhere to the production class interface, preventing tests from passing against outdated APIs. It also refactors protocol guardrail tests to use robust dummy classes instead of fragile `MagicMock` manipulation.

### 2. 🚨 Critical Issues
*   None.

### 3. ⚠️ Logic & Spec Gaps
*   **Missing Documentation Commit**: The PR Context included full content for `design/1_governance/architecture/standards/TESTING_STABILITY.md` and `design/1_governance/architecture/ARCH_TESTS.md`, but these files **do not appear in the provided Diff**. Ensure these files are staged and committed to formalize the new standards.

### 4. 💡 Suggestions
*   **Global Application**: The `spec=Class` pattern should be applied incrementally to `modules/finance` and `simulation/agents` tests to eliminate similar drift risks identified in `TD-TEST-TX-MOCK-LAG`.
*   **Fixture Standardization**: Consider moving the `MagicMock(spec=FiscalPolicyDTO)` setup into a reusable fixture in `tests/conftest.py` if used across multiple governance test files.

### 5. 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "The previous implementation... utilized `MagicMock()` without specifying a `spec`. This approach allows 'Mock Drift'... We are replacing generic `MagicMock()` with `MagicMock(spec=RealClass)`... to ensure the mock only exposes attributes that exist on the real class."
*   **Reviewer Evaluation**:
    *   **Technical Accuracy**: High. `spec=True` or `spec=Class` is the correct solution for `unittest.mock` drift.
    *   **Relevance**: Critical for ensuring that the ongoing large-scale refactoring (DTO implementation) doesn't silently break tests.
    *   **Value**: This establishes a "Hard Rule" for the testing architecture, significantly increasing confidence in the test suite.

### 6. 📚 Manual Update Proposal (Draft)
*Since `TESTING_STABILITY.md` was provided in context but missing from the Diff, I propose creating it to enforce this standard.*

*   **Target File**: `design/1_governance/architecture/standards/TESTING_STABILITY.md`
*   **Draft Content**:
```markdown
# 🧪 Testing Standard: Integrity & Stability

## 🔍 Context
Test failures in isolated/lean environments often stem from brittle mocks and library dependencies that drift from production code.

---

## 🛡️ Hard Rules

### 1. Mock Purity (Preventing MagicMock Poisoning)
- **Primitive Injection is Mandatory**: When mocking objects or their sub-states (e.g., `agent.social_state`), you MUST configure the mock to return primitive values (int, float, bool, str).
  - **WRONG**: `h = MagicMock()` -> `h.social_state.conformity` returns another `MagicMock`.
  - **RIGHT**: `h.social_state.conformity = 0.5`.

### 2. Protocol Compliance (Anti-Drift)
- **Spec-Based Mocking**: Always create mocks with `spec=RealClass` or `spec=IProtocol` (e.g., `MagicMock(spec=Government)`).
  - This prevents "Mock Drift" where tests pass despite the real class renaming or removing methods.
  - It ensures `isinstance(mock, Protocol)` checks function correctly.

### 3. Golden Fixture Priority
- **Prefer Real State**: Use `golden_households` or `golden_ledger` fixtures over manual mock construction for complex entities.

### 4. Test Collection
- **Explicit Packages**: All `tests/` subdirectories MUST contain an `__init__.py`.
- **Absolute Path Resolution**: Use `pathlib.Path(__file__)` for loading resources.

---

## 🚨 Violations
- **Severity: High**: Tests passing on attributes that no longer exist in production code (Drift).
- **Severity: High**: Tests failing with `MagicMock is not JSON serializable`.
```

### 7. ✅ Verdict
**APPROVE**

The code changes are technically sound and improve test reliability. Please ensure the documentation files (`TESTING_STABILITY.md`, `ARCH_TESTS.md`) are included in the final commit.