## 📝 Code Review Report: [S3-1] Scenario Runner Leak Fix

### 🔍 Summary
Refactored `MockRepository` in the test infrastructure to eliminate cyclic references, preventing garbage collection blocks. Introduced deterministic simulation teardown (`finalize_simulation()`) and an aggressive global mock reset strategy (`gc_collect_harder`) to mitigate memory leaks caused by `unittest.mock` retaining massive call histories.

### 🚨 Critical Issues
*   **None**. The changes are fully isolated to test infrastructure and do not introduce security vulnerabilities, hardcoding, or production logic errors.

### ⚠️ Logic & Spec Gaps
*   **Global State Mutation in Tests (Duct-Tape Debugging)**: The `gc_collect_harder()` function iterates over `gc.get_objects()` and calls `reset_mock()` on *every* `Mock` instance in the Python process. This is extremely aggressive. If there are session-scoped or module-scoped fixtures (e.g., `mock_platform_lock_manager` or `mock_fcntl` in `conftest.py`) that rely on their mock call history or state across multiple test runs, this will silently wipe them out. While it solves the immediate OOM issue, it acts as a brittle patch that pollutes the global test environment state.
*   **Performance Overhead**: `gc.get_objects()` creates a list of all objects tracked by the GC, which can be massive and cause a temporary memory spike or CPU delay, especially when called at the end of every parameterized scenario run.

### 💡 Suggestions
*   **Targeted Mock Reset**: Instead of globally nuking all Mocks via `gc.get_objects()`, track the specific heavy mocks created during the test and explicitly reset them. Alternatively, use lightweight dummy classes (Test Doubles) instead of `MagicMock` for high-frequency objects that don't need interaction verification.
*   **Repository Pattern Praise**: The breakdown of the monolithic `MockRepository` into distinct sub-repositories (`MockRunRepository`, etc.) is an excellent architectural fix that correctly resolves the root cause of the structural leak without relying on GC hacks.

### 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > 3. **Hard Garbage Collection (`gc_collect_harder`)**: We recognized that `MagicMock` caches its entire call history (via `call_args_list`), trapping the massive `SimulationState` in memory. To break this, we implemented `gc_collect_harder()`, which uses `gc.get_objects()` to isolate all `Mock` instances and forcefully trigger `reset_mock()`, severing the reference chain before explicitly invoking `gc.collect()`.
*   **Reviewer Evaluation**: The insight correctly identifies `unittest.mock`'s `call_args_list` as a primary source of memory leaks in long-running tests with heavy mocks. The first two points in the original insight (Cyclic Reference breaking and explicit finalization) are excellent, root-cause fixes. However, the third point (`gc_collect_harder`) should be recognized as technical debt rather than a permanent architectural solution. Iterating `gc.get_objects()` to wipe all mocks globally is a side-effect-heavy hack. The insight should acknowledge this as a temporary workaround.

### 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### [TD-TEST-GLOBAL-MOCK-RESET] Aggressive GC Workaround in Scenario Tests
    - **Date**: 2026-03-03
    - **Context**: In `test_scenario_runner.py`, a global mock reset (`gc_collect_harder` using `gc.get_objects()`) was introduced to clear `unittest.mock` call histories that trap `SimulationState` in memory, causing OOM errors.
    - **Issue**: This is a global side-effect. Wiping all `Mock` objects in the process can unpredictably break session/module-scoped mocked fixtures (like `mock_fcntl`) that might rely on state or call history in subsequent tests.
    - **Resolution Strategy**: Replace `gc.get_objects()` with targeted mock resets. Either explicitly track and reset the heavy mocks instantiated within the scenario run, or replace `MagicMock` with lightweight dummy classes (Test Doubles) for high-frequency objects that do not require interaction verification.
    ```

### ✅ Verdict
**APPROVE**
*(The modifications successfully prevent CI/CD memory crashes, and the cyclic reference fix is structurally sound. The aggressive GC method is acceptable to unblock the pipeline but is flagged as test-infrastructure technical debt.)*