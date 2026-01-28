```markdown
# Technical Specification: Scheduler Decomposition & Lifecycle Refactor
**TICKET**: TD-131, TD-132
**Author**: Gemini (Administrative Assistant)
**Date**: 2026-01-28

## 1. Overview

This document outlines the technical plan to refactor the `TickScheduler`. The current `run_tick` method is a "God Method" that violates the Single Responsibility Principle. This refactoring will decompose the scheduler into a series of distinct, interchangeable `Phase` strategy classes, orchestrated by a new `TickOrchestrator`.

Additionally, this plan addresses the misplacement of firm lifecycle logic (`Firm.update_needs`) by relocating it to the `AgentLifecycleManager`, ensuring correct execution order and preventing race conditions.

This refactoring directly addresses the critical findings of the Pre-flight Audit.

## 2. Goals

1.  **Decompose `TickScheduler`**: Replace the monolithic `run_tick` method with a `TickOrchestrator` that executes a sequence of `IPhaseStrategy` objects.
2.  **Improve State Management**: Enhance the `SimulationState` DTO to act as a self-contained, per-tick data bus, eliminating the use of `WorldState` for storing transient tick data.
3.  **Relocate Firm Lifecycle Logic**: Move the logic from `Firm.update_needs` (aging, bankruptcy checks) into the `AgentLifecycleManager` to consolidate lifecycle events.
4.  **Enforce Execution Order**: Ensure the relocated firm lifecycle logic executes *before* agent liquidation within the same tick.
5.  **Improve Testability & Maintainability**: Create a more modular and testable architecture for the core simulation loop.

## 3. Proposed Changes

### 3.1. New `TickOrchestrator`

A new class, `TickOrchestrator`, will replace `TickScheduler`. It will be responsible for:
1.  Initializing the `SimulationState` DTO at the start of each tick.
2.  Executing each `IPhaseStrategy` in the correct, hard-coded order.
3.  Passing the single `SimulationState` DTO to each phase.
4.  Handling the final post-tick cleanup and persistence calls.

**File Location:** `simulation/orchestration/tick_orchestrator.py`

**Pseudo-code:**
```python
class TickOrchestrator:
    def __init__(self, world_state: WorldState, action_processor: ActionProcessor):
        self.world_state = world_state
        self.phases: List[IPhaseStrategy] = [
            Phase0_PreSequence(world_state),
            Phase1_Decision(world_state),
            Phase2_Matching(world_state),
            Phase3_Transaction(world_state, action_processor),
            Phase4_Lifecycle(world_state),
            Phase5_PostSequence(world_state)
        ]

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentStateDTO] = None):
        # 1. Create the comprehensive state DTO for this tick
        sim_state = self._create_simulation_state_dto(injectable_sensory_dto)

        # 2. Execute all phases in sequence
        for phase in self.phases:
            sim_state = phase.execute(sim_state)

        # 3. Post-execution state synchronization
        self._synchronize_world_state(sim_state)

        # 4. Final persistence and cleanup
        self._finalize_tick(sim_state)

    def _create_simulation_state_dto(...) -> SimulationState:
        # Gathers all necessary data from WorldState to create the DTO
        # ... includes market_data preparation, etc.
        pass

    def _synchronize_world_state(self, sim_state: SimulationState):
        # Syncs back critical scalar values from DTO to WorldState
        # e.g., self.world_state.next_agent_id = sim_state.next_agent_id
        pass

    def _finalize_tick(self, sim_state: SimulationState):
        # Handles persistence buffer flushes, counter resets, etc.
        pass
```

### 3.2. Phase Strategy Classes

Each phase of the tick will be encapsulated in its own class, implementing the `IPhaseStrategy` interface.

**File Location:** `simulation/orchestration/phases.py`

-   **`Phase0_PreSequence`**: Handles `_phase_pre_sequence_stabilization` and event system execution.
-   **`Phase1_Decision`**: Handles `_phase_decisions`. It will return an updated `SimulationState` containing `planned_consumption` and `household_time_allocation`.
-   **`Phase2_Matching`**: Handles `_phase_matching`.
-   **`Phase3_Transaction`**: Handles `_phase_transactions`.
-   **`Phase4_Lifecycle`**: Executes the `LifecycleManager`. This is where the relocated firm logic will run.
-   **`Phase5_PostSequence`**: Handles all post-tick logic, including AI learning updates, M&A, Reflux distribution, and money supply verification.

### 3.3. `AgentLifecycleManager` Refactoring (TD-132)

The `Firm.update_needs` logic will be moved into `AgentLifecycleManager`. A new private method `_process_firm_lifecycle` will be created.

**File Location:** `simulation/systems/lifecycle_manager.py`

**Modification:**
```python
# In AgentLifecycleManager class

def execute(self, state: SimulationState) -> SimulationState:
    """
    Processes lifecycle events for the tick.
    Returns:
        SimulationState: The updated state DTO.
    """
    # 1. Aging (Households)
    self.demographic_manager.process_aging(state.households, state.time, state.market_data)

    # 2. NEW: Firm Lifecycle (Aging & Bankruptcy Checks)
    self._process_firm_lifecycle(state) # <<-- RELOCATED LOGIC HERE

    # 3. Births
    new_children = self._process_births(state)
    state = self._register_new_agents(state, new_children)

    # 4. Immigration
    new_immigrants = self.immigration_manager.process_immigration(state)
    state = self._register_new_agents(state, new_immigrants)

    # 5. Entrepreneurship
    state = self.firm_system.check_entrepreneurship(state)

    # 6. Death & Liquidation (Runs AFTER firm bankruptcy status is updated)
    state = self._handle_agent_liquidation(state)

    return state


def _process_firm_lifecycle(self, state: SimulationState) -> None:
    """
    Handles lifecycle updates for all active firms, formerly in Firm.update_needs.
    """
    for firm in state.firms:
        if not firm.is_active:
            continue

        firm.age += 1

        # Check bankruptcy status (logic from FinanceDepartment)
        firm.finance.check_bankruptcy()

        # Check for closure based on assets or consecutive losses
        if (firm.assets <= state.config_module.ASSETS_CLOSURE_THRESHOLD or
                firm.finance.consecutive_loss_turns >= state.config_module.FIRM_CLOSURE_TURNS_THRESHOLD):
            firm.is_active = False
            self.logger.warning(f"FIRM_INACTIVE | Firm {firm.id} closed down.", ...)

```

### 3.4. Code Removal

-   The file `simulation/tick_scheduler.py` will be **deleted**.
-   The method `Firm.update_needs` will be **deleted**.
-   The loop calling `firm.update_needs` in the post-tick section of the old `run_tick` method will be **deleted**.

## 4. API & DTO Definitions

### 4.1. `simulation/orchestration/api.py`

```python
from __future__ import annotations
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState

class IPhaseStrategy(Protocol):
    """Interface for a single phase of the simulation tick."""

    def execute(self, state: SimulationState) -> SimulationState:
        """
        Executes the logic for this phase.

        Args:
            state: The current simulation state DTO for the tick.

        Returns:
            The potentially modified simulation state DTO.
        """
        ...
```

### 4.2. `simulation/dtos/api.py` (Enhancements)

The `SimulationState` DTO will be expanded to carry transient tick data, preventing pollution of `WorldState`.

```python
# In simulation.dtos.api.py

@dataclass
class SimulationState:
    # ... existing fields ...
    transactions: List[Transaction] = field(default_factory=list)
    inter_tick_queue: List[Transaction] = field(default_factory=list)
    inactive_agents: Dict[int, BaseAgent] = field(default_factory=dict)
    
    # --- NEW TRANSIENT FIELDS ---
    # From Phase 1 (Decisions)
    firm_pre_states: Dict[int, Any] = field(default_factory=dict)
    household_pre_states: Dict[int, Any] = field(default_factory=dict)
    household_time_allocation: Dict[int, float] = field(default_factory=dict)
    
    # From Commerce System (planned in Phase 1, used in PostSequence)
    planned_consumption: Dict[int, Dict[str, float]] = field(default_factory=dict)

    # From Lifecycle (used in PostSequence for Learning)
    household_leisure_effects: Dict[int, float] = field(default_factory=dict)

```

## 5. Addressing Audit Findings

-   **Risk: State & Context Management**: **Mitigated**. The `SimulationState` DTO is explicitly expanded to become the single source of truth for the duration of a tick, carrying all transient data between phases. This avoids writing temporary data to the long-lived `world_state`.
-   **Risk: The Sacred Sequence**: **Mitigated**. The new `TickOrchestrator` hard-codes the execution of the six phases (`PreSequence`, `Decision`, `Matching`, `Transaction`, `Lifecycle`, `PostSequence`), preserving the sacred core sequence and formally structuring the setup/teardown logic.
-   **Risk: Execution Order & Agent Liquidation**: **Mitigated**. The specification explicitly places the new `_process_firm_lifecycle` method *before* `_handle_agent_liquidation` within `AgentLifecycleManager.execute`. This guarantees that firms marked as inactive during the current tick are immediately eligible for liquidation in the same tick.
-   **Risk: Logic Duplication**: **Mitigated**. The specification mandates the deletion of `Firm.update_needs` and the removal of its call from the old scheduler logic, preventing the risk of double execution.

## 6. Verification & Test Plan

1.  **Unit Tests**: New unit tests will be created for `TickOrchestrator` and each `IPhaseStrategy` class.
2.  **`TickOrchestrator` Test**: A test will verify that the orchestrator calls each phase's `execute` method exactly once and in the correct order.
3.  **`Phase4_Lifecycle` Test**: A test will specifically verify that if a `Firm` meets the conditions for bankruptcy (e.g., zero assets) within `_process_firm_lifecycle`, it is correctly marked `is_active=False` and subsequently processed by `_handle_agent_liquidation` in the same call.
4.  **Integration Test**: An existing end-to-end simulation test will be run to ensure the refactored scheduler produces results consistent with the previous implementation (given a fixed seed).

### Golden Data & Mock Strategy
- **Test Data**: Existing `conftest.py` fixtures (`golden_households`, `golden_firms`) will be used to test the phases in isolation.
- **Mocking**: The `IPhaseStrategy` interface allows for easy mocking. For example, to test `Phase4_Lifecycle`, the preceding phases can be mocked to produce a specific `SimulationState` DTO as input. This isolates the component under test.

## 7. Risk & Impact Analysis

-   **Impact**: High. This change affects the core loop of the simulation.
-   **Risk**: Medium. The primary risk lies in incorrectly transferring logic or state from the old `TickScheduler` to the new phase classes.
-   **Mitigation**: The detailed pseudo-code, explicit DTO enhancements, and a clear test plan are designed to minimize this risk. Peer review of the implementation will be critical.

---
## 🚨 Mandatory Reporting (Jules)
During implementation, you are required to log any unforeseen dependencies or architectural friction discovered. Report all findings, especially those related to state dependencies not accounted for in this spec, to `communications/insights/`. Document any newly identified technical debt in a draft for `TECH_DEBT_LEDGER.md`.
```
