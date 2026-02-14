# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR significantly improves test fidelity by enforcing **Protocol Purity** in mocks. It moves away from loose `hasattr` checks to strict `isinstance(obj, Protocol)` validation, requiring mocks to explicitly implement interface methods (e.g., `get_all_balances`). It also refactors `conftest.py` to fix `sys.modules` patching for Python 3.12+ and enforces strict attribute checking on `mock_config` to reveal hidden dependencies.

## 🚨 Critical Issues
*None detected.* The changes are confined to the test suite and do not introduce security risks or logic errors in the production codebase.

## ⚠️ Logic & Spec Gaps
*None.* The refactoring aligns with the goal of increasing system stability and test reliability.

## 💡 Suggestions
*   **Future Cleanup**: The split in `conftest.py` between "verified" config attributes and "legacy/hidden" ones (`Attributes likely not in config.py`) exposes significant technical debt. A future task should be scheduled to migrate these hidden attributes into the actual `config` module or remove them if unused.

## 🧠 Implementation Insight Evaluation

*   **Original Insight**:
    > "We discovered a critical nuance in Python's `typing.Protocol` when used with Mocks... standard `Mock` objects do **not** automatically pass `isinstance(obj, Protocol)` checks... We enforcing `isinstance(mock, Protocol)` checks... strictly limit `mock_config` to attributes present in the real `config` module."

*   **Reviewer Evaluation**:
    This is a **High-Value Insight**. The distinction between `Protocol` structural typing and `MagicMock` behavior is a common pitfall in Python testing. Adopting strict `isinstance` checks ensures that mocks don't just "act" like the object (duck typing) but actually satisfy the interface contract, preventing "False Positive" tests where the production code relies on methods the mock "magically" provides but the real object might not. The `sys.modules` `__spec__` fix is also critical for future-proofing against Python 3.12+ import machinery.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (or `design/1_governance/architecture/standards/TESTING_STABILITY.md`)

```markdown
### [Architectural Pattern] Protocol-Compliant Mocking

**Context**: Python's `typing.Protocol` supports structural subtyping (`isinstance` checks), but `unittest.mock.MagicMock` does not pass these checks by default even if it has the matching methods, unless `spec` is used or the methods are defined explicitly.

**Decision**:
1.  **Strict Typing**: Prefer `isinstance(agent, IFinancialAgent)` over `hasattr(agent, 'method_name')` in production code to enforce contracts.
2.  **Mock Implementation**: When mocking Protocols, explicitly define the required methods in the Mock class or use `spec_set` carefully. Do not rely on `MagicMock`'s auto-creation of attributes for interface compliance.
3.  **Config mocking**: Use `MagicMock(spec=config_module)` to prevent tests from relying on configuration variables that do not exist in the actual source code.

**Anti-Pattern**:
- `hasattr(mock, 'anything')` returns `True`. Relying on this leads to tests passing even if the real object lacks the method.
```

## ✅ Verdict
**APPROVE**