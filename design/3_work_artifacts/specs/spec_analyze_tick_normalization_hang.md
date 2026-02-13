# Mission Guide: Analyze Tick Normalization Test Hang

## 1. Objectives
- Analyze the root cause of the hang in `tests/integration/test_tick_normalization.py::TestTickNormalization::test_run_tick_executes_phases`.
- Confirm the hypothesis of an infinite loop in `TickOrchestrator._create_simulation_state_dto`.
- Propose a fix for the test setup or the orchestrator logic.

## 2. Reference Context (MUST READ)
- **conflicted file**: [tick_orchestrator.py](file:///c:/coding/economics/simulation/orchestration/tick_orchestrator.py#L113-L114)
- **test file**: [test_tick_normalization.py](file:///c:/coding/economics/tests/integration/test_tick_normalization.py)
- **engine facade**: [engine.py](file:///c:/coding/economics/simulation/engine.py)

## 3. Analysis Findings (Bounty Hunter's Lead)
A preliminary analysis suggests that `TickOrchestrator._create_simulation_state_dto` contains a `while` loop that drains `state.god_command_queue`. 
```python
# tick_orchestrator.py:113
while state.god_command_queue:
    god_commands_for_tick.append(state.god_command_queue.popleft())
```
In `test_tick_normalization.py`, `mock_world_state` is a `MagicMock`. By default, `state.god_command_queue` will also be a `MagicMock`, which evaluates to `True` in a boolean context. `popleft()` will return another mock, and the loop will never terminate.

## 4. Implementation Roadmap
### Phase 1: Verification
- Run the specific test with a timeout or debugger to confirm the loop location.
- Verify why other tests might not be hitting this (likely because they use real `WorldState` or configure the mock queues).

### Phase 2: Fix Selection
- Option A: Explicitly initialize `command_queue` and `god_command_queue` as empty `deque` / `Queue` in the `mock_world_state` fixture.
- Option B: Use `hasattr` or better guarding in the orchestrator (though Phase 0/God Commands are supposed to be present).

## 5. Success Criteria
- `pytest tests/integration/test_tick_normalization.py` passes without hanging.
- No regressions in other integration tests.
