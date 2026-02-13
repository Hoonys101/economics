# Architectural Insights

## MagicMock Truthiness Trap
The infinite loop in `tests/orchestration/test_state_synchronization.py` was caused by the default behavior of `unittest.mock.MagicMock`. In Python, `MagicMock` instances are truthy by default.

When `TickOrchestrator` iterates over queues using `while state.god_command_queue:`, if `state` is a mock and `god_command_queue` is not explicitly set, `state.god_command_queue` returns a new `MagicMock`, which evaluates to `True`. The `popleft()` call inside the loop also returns a mock, leaving the original "queue" (the mock attribute) unchanged and truthy, resulting in an infinite loop.

### Recommendation
- **Explicit Initialization**: When mocking complex state objects like `WorldState`, explicitly initialize all collection attributes (lists, deques, dicts) that are iterated over or checked for truthiness.
- **Protocol Adherence**: Ensure mocks used in orchestration tests strictly adhere to the expected interface, particularly for iterable or queue-like structures.

# Test Evidence

```
tests/orchestration/test_state_synchronization.py::TestStateSynchronization::test_transient_queue_accumulation PASSED [ 50%]
tests/orchestration/test_state_synchronization.py::TestStateSynchronization::test_reassignment_guardrail PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 2 warnings in 0.54s =========================
```
