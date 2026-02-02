# Specification: TD-192 - Transient State Synchronization Protocol

## 1. Problem Definition

- **ID**: TD-192
- **Description**: State modifications made within a tick via the transient `SimulationState` DTO may be lost and not persist back to the primary `WorldState`.
- **Root Cause**: The architecture lacks a formal, enforced protocol for synchronizing state from the transient DTO back to the persistent state object at the end of a processing phase. Synchronization relies on developers remembering to modify collection objects *in-place* or manually adding sync logic to `TickOrchestrator`, which is error-prone. The `TD-192` comment in `action_processor.py` highlights this regression risk for transient queues (`effects_queue`, `inter_tick_queue`).
- **Impact**:
    - **State Desynchronization & Lost Data**: Critical events, agent creations, or transactions queued in one phase may never be processed if the queue object is re-assigned instead of modified in-place, leading to subtle and severe simulation bugs.
    - **High Regression Risk**: Any refactoring within a phase could accidentally break the implicit sync-back contract, leading to silent failures that are difficult to trace.
    - **Architectural Brittleness**: The system's correctness depends on an unwritten convention rather than an explicit mechanism.

## 2. Detailed Implementation Plan

This plan establishes a formal, two-part protocol to guarantee state synchronization: **1. The In-Place Modification Rule** for collections, and **2. A Hub-and-Spoke Draining Mechanism** for transient queues managed by the `TickOrchestrator`.

### Step 1: Formalize the "In-Place Modification" Rule

This rule will be documented in the project's development guide (`PROTOCOL_ENGINEERING.md`).

- **Rule**: Any phase or system operating on the `SimulationState` DTO **MUST NOT** re-assign collection attributes (lists, dicts). It must only modify them in-place.
    - **Allowed**: `sim_state.households.append(...)`, `sim_state.agents.update(...)`, `sim_state.firms[:] = ...`
    - **Forbidden**: `sim_state.households = new_list_of_households`
- **Enforcement**: This is primarily a code review and developer discipline issue. A custom `ruff` lint rule could be written in the future to detect direct assignment to state DTO collections.

### Step 2: Implement a "State Drain" in `TickOrchestrator`

The `TickOrchestrator` will be the sole authority for managing the lifecycle of transient data. Instead of phases passing state to each other, they will all report back to the orchestrator's central state.

- **Modify `simulation/orchestration/tick_orchestrator.py`**:
    - The main loop in `run_tick` will be modified. After each phase executes, a new private method `_drain_and_sync_state` will be called.

```python
# In TickOrchestrator.run_tick
# ...
sim_state = self._create_simulation_state_dto(...)

for phase in self.phases:
    # 1. Execute the phase
    sim_state = phase.execute(sim_state)

    # 2. Immediately drain and sync state back to WorldState
    self._drain_and_sync_state(sim_state)

# ...
```

### Step 3: Implement the `_drain_and_sync_state` Method

This method centralizes all synchronization logic, making it explicit and reliable.

- **Create `_drain_and_sync_state(self, sim_state: SimulationState)` in `TickOrchestrator`**:

```python
# In TickOrchestrator
def _drain_and_sync_state(self, sim_state: SimulationState):
    """
    Drains transient queues from SimulationState into WorldState and syncs scalars.
    This ensures changes from a phase are immediately persisted before the next phase runs.
    """
    ws = self.world_state

    # --- Sync Scalars ---
    ws.next_agent_id = sim_state.next_agent_id

    # --- Drain Transient Queues ---
    # The core of the solution: move items from the DTO's queue to the WorldState's
    # master queue for the tick, then clear the DTO's queue so it's fresh for the next phase.

    if sim_state.effects_queue:
        ws.effects_queue.extend(sim_state.effects_queue)
        sim_state.effects_queue.clear() # Prevent double-processing

    if sim_state.inter_tick_queue:
        ws.inter_tick_queue.extend(sim_state.inter_tick_queue)
        sim_state.inter_tick_queue.clear() # Prevent double-processing

    if sim_state.transactions:
        ws.transactions.extend(sim_state.transactions)
        sim_state.transactions.clear() # Prevent double-processing

    # --- Sync mutable collections by reference (ensure no re-assignment) ---
    # This acts as a safety check. If a phase violates the rule, this will raise an error.
    if ws.agents is not sim_state.agents:
        raise RuntimeError("CRITICAL: 'agents' collection was re-assigned in a phase. Use in-place modification.")
    
    # Update the inactive agents dictionary
    ws.inactive_agents.update(sim_state.inactive_agents)
```

### Step 4: Refactor `ActionProcessor` and other systems

- The manual synchronization logic in `action_processor.py` (marked with `TD-192`) will be **removed**. The `TickOrchestrator`'s new draining mechanism makes it redundant. The `TransactionProcessor` will append to the `SimulationState`'s queues, and the orchestrator will handle the sync-back immediately after `Phase3_Transaction` completes.

## 3. Verification Criteria

1.  **New Integration Test for State Synchronization**:
    - Create a test `tests/orchestration/test_state_synchronization.py`.
    - **Test Case**:
        1.  Create a dummy `IPhaseStrategy` ("Phase A") that adds an item to `sim_state.effects_queue`.
        2.  Create another dummy `IPhaseStrategy` ("Phase B") that also adds an item to `sim_state.effects_queue`.
        3.  Run a `TickOrchestrator` with `[Phase A, Phase B]`.
        4.  **Assert**: After the tick runs, `world_state.effects_queue` must contain **both** items, demonstrating that the drain logic correctly accumulated items from both phases without loss.

2.  **New Failure Test for Re-assignment**:
    - **Test Case**:
        1.  Create a dummy phase that violates the "In-Place" rule (e.g., `sim_state.agents = []`).
        2.  Run the `TickOrchestrator` with this phase.
        3.  **Assert**: The `RuntimeError` defined in `_drain_and_sync_state` must be raised, proving the guardrail works.

3.  **Refactoring Verification**:
    - The explicit sync logic in `action_processor.py` must be removed.
    - A full simulation run with the same seed must produce identical results before and after the change, confirming that the new explicit sync mechanism correctly replicates the behavior of the old implicit one.
