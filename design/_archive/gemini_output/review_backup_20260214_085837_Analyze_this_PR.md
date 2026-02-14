# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
Fixed a test regression in `test_parameter_rollback` within `mission_int_02_stress_test.py`. The fix corrects the `IGlobalRegistry` mock setup to providing a concrete `RegistryEntry` for state snapshotting, preventing `MagicMock` objects from polluting the undo history. Additionally, the rollback assertion was updated to correctly verify that parameters are restored to their original `OriginType.CONFIG` state, not `OriginType.GOD_MODE`.

## 🚨 Critical Issues
*   None detected.

## ⚠️ Logic & Spec Gaps
*   None detected. The logic changes correctly reflect the "restore to previous state" behavior.

## 💡 Suggestions
*   **Future Refactoring**: The insight regarding "Mock Leaks" (mocks propagating into data structures) is valuable. Consider enforcing type checks in `UndoRecord` or the `CommandService` to raise an error if a `MagicMock` is ever stored as a snapshot value, catching this class of test errors earlier.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "The failure in `test_parameter_rollback` was caused by an incomplete mock configuration... The test mocked `registry.get()` but not `registry.get_entry()`, causing the `UndoRecord` to store a `MagicMock` as the `previous_entry`... Additionally, the original assertion expected the rollback to set the origin to `OriginType.GOD_MODE`. ... the correct expected behavior is for the origin to be restored to `OriginType.CONFIG`."
*   **Reviewer Evaluation**:
    *   **High Value**: The insight accurately identifies a common testing pitfall: **Partial Mocking of Stateful Services**. When a service (`CommandService`) takes a snapshot of another component (`Registry`), the mock must return concrete data structures (DTOs/Value Objects) for that snapshot, otherwise the "state" becomes a mock, leading to confusing failures during restoration.
    *   **Correct Domain Logic**: The correction regarding `OriginType.CONFIG` vs `GOD_MODE` demonstrates a good understanding of the lifecycle. A rollback negates the "God Mode" intervention, so the origin should revert to the baseline.

## 📚 Manual Update Proposal (Draft)

*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (or `TESTING_STABILITY.md` if available)
*   **Draft Content**:

```markdown
### Testing Pattern: Mocking Stateful Snapshots
*   **Context**: Services that implement Undo/Rollback functionality often "snapshot" the state of dependencies (e.g., `CommandService` reading `Registry`).
*   **Problem**: If the dependency is a Mock, and the snapshot method (e.g., `get_entry`) is not explicitly stubbed to return a concrete object, the "snapshot" becomes a `MagicMock`.
*   **Symptom**: Rollback operations fail because the system tries to restore a `MagicMock` into the state, or assertions fail because `mock.set()` is called with a mock instead of a value.
*   **Solution**: Always mock the "Getter" used for snapshotting to return a concrete Value Object (e.g., `RegistryEntry`, `DTO`), not a Mock.
    ```python
    # BAD
    registry.get.return_value = 10 
    # (If service uses get_entry() for snapshot, it gets a fresh MagicMock)

    # GOOD
    registry.get_entry.return_value = RegistryEntry(value=10, origin=OriginType.CONFIG)
    ```
```

## ✅ Verdict
**APPROVE**

The PR fixes a clear test logic error, improves mock fidelity, and includes the required test evidence and insights. The assertion change is logically sound for a rollback operation.