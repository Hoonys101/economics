# Spec: Delta-Based `currency_holders` Management

- **Module**: `simulation.orchestration`, `simulation.systems`, `modules.system`
- **Version**: 1.0
- **JIRA**: WO-222

## 1. Overview

The current system rebuilds the `WorldState.currency_holders` list from scratch every tick (`O(N)` operation), which is inefficient and masks underlying issues where components do not explicitly manage an agent's lifecycle within this critical list.

This refactoring replaces the full rebuild with a delta-based approach. Agents will be explicitly added to `currency_holders` upon creation and removed upon liquidation. This improves performance from O(N) to O(1) for list management per tick and enforces stricter lifecycle management protocols.

## 2. API Specification

The public API for managing the `currency_holders` list will be exposed via a new helper module.

### `modules/system/currency_helper.py`

```python
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from modules.system.api import ICurrencyHolder

logger = logging.getLogger(__name__)

def register_currency_holder(state: SimulationState, agent: ICurrencyHolder):
    """
    Safely registers a new agent to the currency_holders list.
    - Ensures the agent is a valid ICurrencyHolder.
    - Prevents duplicate entries.
    """
    if not hasattr(agent, 'get_assets_by_currency'):
        logger.critical(f"REGISTRY_ERROR | Agent {getattr(agent, 'id', 'N/A')} is not ICurrencyHolder!")
        return

    if agent in state.currency_holders:
        logger.warning(f"REGISTRY_WARN | Agent {agent.id} already in currency_holders.")
        return

    state.currency_holders.append(agent)
    logger.debug(f"REGISTRY_ADD | Agent {agent.id} added to currency_holders.")

def unregister_currency_holder(state: SimulationState, agent: ICurrencyHolder):
    """
    Safely unregisters an agent from the currency_holders list.
    """
    try:
        state.currency_holders.remove(agent)
        logger.debug(f"REGISTRY_REMOVE | Agent {agent.id} removed from currency_holders.")
    except ValueError:
        logger.warning(
            f"REGISTRY_WARN | Agent {getattr(agent, 'id', 'N/A')} not found in currency_holders for removal.",
            extra={"agent_id": getattr(agent, 'id', 'N/A')}
        )

```

### `modules/system/api.py`

The following functions will be added to `modules/system/api.py` to be globally accessible.

```python
# ... existing imports
from .currency_helper import register_currency_holder, unregister_currency_holder

# ... existing API exports
__all__ = [
    # ...,
    "register_currency_holder",
    "unregister_currency_holder"
]
```

## 3. Logic & Implementation (Pseudo-code)

### 3.1. `simulation.systems.lifecycle_manager.AgentLifecycleManager`

This manager will be modified to use the new helper functions during agent creation and liquidation.

```python
# simulation/systems/lifecycle_manager.py

# Add new import
from modules.system.api import register_currency_holder, unregister_currency_holder

class AgentLifecycleManager:
    # ...

    def _register_new_agents(self, state: SimulationState, new_agents: List[Household]):
        for agent in new_agents:
            # ... existing registration logic ...
            state.households.append(agent)
            state.agents[agent.id] = agent

            # === MODIFICATION START ===
            # Old Code:
            # if isinstance(agent, ICurrencyHolder):
            #     state.currency_holders.append(agent)

            # New Code:
            register_currency_holder(state, agent)
            # === MODIFICATION END ===

            # ... other setup logic ...

    def _handle_agent_liquidation(self, state: SimulationState) -> List[Transaction]:
        transactions: List[Transaction] = []

        # --- Firm Liquidation ---
        inactive_firms = [f for f in state.firms if not f.is_active]
        for firm in inactive_firms:
            # === MODIFICATION START ===
            # Explicitly unregister before any other cleanup
            unregister_currency_holder(state, firm)
            # === MODIFICATION END ===

            self.logger.info(f"FIRM_LIQUIDATION | Starting for Firm {firm.id}.")
            # ... rest of the firm liquidation logic ...

        # --- Household Liquidation (Inheritance) ---
        inactive_households = [h for h in state.households if not h._bio_state.is_active]
        for household in inactive_households:
            # === MODIFICATION START ===
            # Explicitly unregister before any other cleanup
            unregister_currency_holder(state, household)
            # === MODIFICATION END ===

            if hasattr(state, "inactive_agents"):
                state.inactive_agents[household.id] = household
            # ... rest of the household liquidation logic ...

        # ... final list cleanup ...
        return transactions

```

### 3.2. `simulation.orchestration.tick_orchestrator.TickOrchestrator`

The inefficient `_rebuild_currency_holders` method will be removed entirely. The one-time setup at `t=0` will be preserved with a direct implementation.

```python
# simulation/orchestration/tick_orchestrator.py

# ... imports

class TickOrchestrator:
    # ...

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentStateDTO] = None) -> None:
        state = self.world_state

        # === MODIFICATION START ===
        # Money Supply Verification (Tick 0)
        if state.time == 0:
            # New Code: Direct, one-time population
            state.currency_holders.clear()
            system_agents = [
                state.central_bank, state.government, state.bank,
                getattr(state, "escrow_agent", None), state.settlement_system
            ]
            for agent in system_agents:
                if agent: state.currency_holders.append(agent)
            for agent in state.agents.values():
                if agent not in state.currency_holders:
                    state.currency_holders.append(agent)
            # End New Code

            state.baseline_money_supply = state.calculate_total_money().get(DEFAULT_CURRENCY, 0.0)
            state.logger.info(
                f"MONEY_SUPPLY_BASELINE | Baseline set to: {state.baseline_money_supply:.2f}"
            )
        # === MODIFICATION END ===

        # ...
        state.time += 1
        # ...

    def _finalize_tick(self, sim_state: SimulationState):
        state = self.world_state
        # ...
        # === MODIFICATION START ===
        # Old Code:
        # if state.time >= 1:
        #     self._rebuild_currency_holders(state)
        #     ... money supply check ...

        # New Code: No rebuild needed. The list is now always consistent.
        if state.time >= 1:
            current_money = state.calculate_total_money().get(DEFAULT_CURRENCY, 0.0)
            # ... rest of money supply check logic remains the same ...
        # === MODIFICATION END ===

    # === MODIFICATION START ===
    # The entire _rebuild_currency_holders method is DELETED.
    # def _rebuild_currency_holders(self, state: WorldState): ...
    # === MODIFICATION END ===

```

## 4. Verification Plan

1.  **Unit Test: Agent Lifecycle & `currency_holders` Count**
    - **Scenario**: Initialize a simulation with N households.
    - **Action**: Manually deactivate one household (`_bio_state.is_active = False`). Run `AgentLifecycleManager.execute()`.
    - **Assert**:
        - The length of `state.currency_holders` is `original_count - 1`.
        - The specific deactivated agent is no longer in `state.currency_holders`.

2.  **Unit Test: Agent Creation & `currency_holders` Count**
    - **Scenario**: Initialize a simulation.
    - **Action**: Manually trigger a birth via `DemographicManager.process_births()`, then run `AgentLifecycleManager._register_new_agents()`.
    - **Assert**:
        - The length of `state.currency_holders` is `original_count + 1`.
        - The new child agent is present in `state.currency_holders`.

3.  **Integration Test: Money Supply Integrity**
    - **Scenario**: Run a full simulation for 10 ticks where agent deaths and births are guaranteed to occur.
    - **Action**: Run the simulation using the refactored `TickOrchestrator`.
    - **Assert**:
        - The `MONEY_SUPPLY_CHECK` does not log any warnings (i.e., delta remains near zero). This validates that the list remains accurate throughout the simulation run, correctly reflecting the net effect of monetary changes without the full rebuild.

4.  **Golden Fixture Usage**: All tests will leverage existing `conftest.py` fixtures (`golden_households`, `simulation_state_fixture`) to ensure a realistic and consistent test environment.

## 5. Risk & Impact Audit

This design directly addresses the risks identified in the pre-flight audit:

-   **Risk**: Removal of the "Garbage Collection" safety net.
    -   **Mitigation**: The explicit `unregister_currency_holder` call in `AgentLifecycleManager` serves as the new, reliable mechanism for removal. Responsibility is now clearly defined, not implicit.

-   **Risk**: Asymmetric Lifecycle Management.
    -   **Mitigation**: The design enforces symmetry. `AgentLifecycleManager` now handles both registration (via `_register_new_agents`) and unregistration (via `_handle_agent_liquidation`), consolidating the responsibility for `currency_holders` into a single, appropriate system.

-   **Risk**: SRP Violation in `AgentLifecycleManager`.
    -   **Mitigation**: While a full refactor of `AgentLifecycleManager` is out of scope, this change is surgically precise. The addition of `unregister_currency_holder` is a single, clean line of code that delegates responsibility to the new helper module, minimizing disruption to the existing fragile logic. The underlying SRP violation will be logged as technical debt.

-   **Risk**: Fragility of Money Supply Verification.
    -   **Mitigation**: The comprehensive verification plan, especially the integration test for money supply integrity over multiple ticks, is designed specifically to build confidence in this new, more efficient approach and catch any regressions.

## 6. Mandatory Reporting Verification

-   Insights and technical debt considerations from this refactoring have been documented in `communications/insights/WO-222_CurrencyHolder_Delta_Update.md`. This ensures that learnings about the system's architecture are preserved.

---
`file:communications/insights/WO-222_CurrencyHolder_Delta_Update.md`
```markdown
# Insight Report: WO-222 Currency Holder Delta Update

- **Date**: 2026-02-05
- **Author**: Gemini Scribe
- **Related Module**: `simulation.orchestration`, `simulation.systems`

## 1. Insight: Fragility of Implicit Lifecycle Management

The previous reliance on a full O(N) rebuild of `currency_holders` masked a significant architectural flaw: agent removal was not being handled explicitly by the systems responsible for their lifecycle (e.g., `AgentLifecycleManager`). This created a "garbage collection" dependency that was both inefficient and made the system harder to reason about.

**Lesson**: State-carrying lists that are critical for system invariants (like money supply) must have explicit, symmetrical `add` and `remove` operations managed by the systems that own the lifecycle of the objects in the list. Implicit cleanup should be avoided.

## 2. Technical Debt Incurred

### TD-223: `AgentLifecycleManager` is a God Object

- **Description**: While this change surgically addressed the `currency_holders` logic, it further highlighted that `AgentLifecycleManager` has too many responsibilities: aging, birth, immigration, entrepreneurship checks, and complex liquidation for both firms and households.
- **Consequence**: This makes the module difficult to test and maintain. A bug in one area (e.g., firm liquidation) can have unforeseen consequences on another (e.g., household demographics).
- **Recommendation**: Plan a future refactoring to split `AgentLifecycleManager` into smaller, more focused systems, such as:
    - `DemographicSystem` (aging, birth, immigration)
    - `FirmLifecycleSystem` (entrepreneurship, bankruptcy)
    - `HouseholdLifecycleSystem` (distress, death)
    - `LiquidationSystem` (a more robust and isolated version of the current liquidation logic).

### TD-224: Initial `currency_holders` Population is Manual

- **Description**: The one-time population of `currency_holders` at `t=0` in `TickOrchestrator` is now a manual loop. This was a pragmatic choice to remove the old `_rebuild` method, but it's not ideal.
- **Consequence**: If a new type of top-level agent is added to `WorldState`, developers must remember to add it to this initial loop.
- **Recommendation**: In the future, create a `WorldState.get_all_currency_holders()` method that encapsulates this logic, providing a single, reliable source of truth for initialization.
```

---
`file:modules/system/api.py`
```python
"""
System-level APIs and interfaces.
"""
from __future__ import annotations
from typing import Protocol, List, Dict, Any

# --- Interfaces ---

class ICurrencyHolder(Protocol):
    """Interface for any agent that can hold currency."""
    id: Any
    def get_assets_by_currency(self) -> Dict[str, float]: ...
    def credit(self, amount: float, currency: str = "USD"): ...
    def debit(self, amount: float, currency: str = "USD"): ...

class IAssetRecoverySystem(Protocol):
    """Interface for a system that processes assets from bankrupt/liquidated agents."""
    def process_bankruptcy_event(self, event: Dict[str, Any]) -> None: ...
    def recover_assets(self, tick: int, markets: Dict[str, Any]) -> List[Any]: ...

# --- Constants ---
DEFAULT_CURRENCY = "USD"

# --- New API Functions ---
from .currency_helper import register_currency_holder, unregister_currency_holder

__all__ = [
    "ICurrencyHolder",
    "IAssetRecoverySystem",
    "DEFAULT_CURRENCY",
    "register_currency_holder",
    "unregister_currency_holder",
]
```
