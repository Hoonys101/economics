# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
Refactored test configuration to resolve `ModuleNotFoundError` regressions caused by global `sys.modules` patching in `test_socket_manager.py`. Moved conditional dependency mocking (e.g., `websockets`, `streamlit`) to `conftest.py` with proper package emulation (`__path__ = []`), ensuring test isolation and stability across environments.

## 🚨 Critical Issues
*   None detected.

## ⚠️ Logic & Spec Gaps
*   None detected.

## 💡 Suggestions
*   None. The solution effectively addresses the root cause of the test pollution.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: "Global `sys.modules` Patching in Tests is Harmful: Manually modifying `sys.modules` in a test file affects the entire test process... Conditional Mocking in `conftest.py` is Robust: Centralizing mocks... Adding `mock.__path__ = []` is crucial for mimicking packages..."
*   **Reviewer Evaluation**: **High Value**. The insight accurately identifies a common anti-pattern (global state mutation in unit tests) that leads to "flaky" or order-dependent test failures. The specific note about `mock.__path__ = []` is a crucial technical detail for mocking Python packages that contain submodules, often overlooked.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### [Testing] Global `sys.modules` Patching vs `conftest.py`
    - **Context**: `ModuleNotFoundError` regressions occurred because `test_socket_manager.py` manually patched `sys.modules["websockets"]` with a mock, polluting the global namespace for subsequent tests.
    - **Resolution**: Moved conditional mocking to `tests/conftest.py`.
    - **Lesson**: NEVER patch `sys.modules` directly in individual test files. Use `conftest.py` for environment-wide mocks.
    - **Technique**: When mocking a package (to allow `from package import module`), set `mock.__path__ = []`.
    - **Date**: 2026-02-14
    ```

## ✅ Verdict
**APPROVE**