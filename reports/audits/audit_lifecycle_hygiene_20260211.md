# Audit Report: Core Lifecycle Events

## Executive Summary
The agent death and liquidation process appears robust and aligned with documented standards. However, the agent birth process introduces significant direct coupling between new agents and global systems. More critically, tick-level financial counters for `Household` agents are never reset, a direct violation of the "Late-Reset Principle" that will lead to corrupted economic data over time.

## Detailed Analysis

### 1. Birth (New Agent Registration)
- **Status**: ⚠️ Partial
- **Evidence**: `simulation/systems/lifecycle_manager.py:L284-306`
- **Notes**: The `_register_new_agents` function correctly adds new agents to the simulation state but creates undocumented, tight coupling. It directly injects references to global, mutable state objects and systems into the newborn agent.
  - `agent.decision_engine.markets = state.markets`
  - `agent.decision_engine.goods_data = state.goods_data`
  - `agent.settlement_system = self.settlement_system`
  - `state.ai_training_manager.agents.append(agent)`
- **Impact**: This direct injection makes the `Household` agent difficult to test in isolation and non-portable, as it immediately depends on a wide array of external systems upon instantiation.

### 2. Death (Agent Liquidation)
- **Status**: ✅ Implemented
- **Evidence**: `simulation/systems/lifecycle_manager.py:L352-475`
- **Notes**: The `_handle_agent_liquidation` function correctly processes inactive `Firm` and `Household` agents. The logic adheres to the principle of "Birth/Death Atomicity".
  - **Firms**: Liquidation is delegated to `liquidation_manager.initiate_liquidation` (`L:364`), employees are cleared, shares are removed from portfolios, and the agent is unregistered from the currency system (`L:414`).
  - **Households**: Inheritance is processed via `inheritance_manager.process_death` (`L:424`), assets are recovered by `public_manager` (`L:433`), inventory and portfolios are cleared (`L:445-447`), and the agent is unregistered from the currency system (`L:468`).
  - **Finalization**: The global agent lists (`state.households`, `state.firms`, `state.agents`) are rebuilt using only active agents, preventing "Ghost Agents" (`L:472-475`).

### 3. Tick-Level State Reset
- **Status**: ❌ Missing
- **Evidence**: `simulation/core_agents.py` (lack of reset logic), `design/1_governance/architecture/standards/LIFECYCLE_HYGIENE.md:L7-13`
- **Notes**: A critical violation of the "Late-Reset Principle" was found.
  - **Firms (Correct)**: The `Firm` class has a `reset()` method (`simulation/firms.py:L1218`) that correctly clears tick-level financial counters like `revenue_this_turn` and `expenses_this_tick`.
  - **Households (Incorrect)**: The `Household` class has no corresponding reset logic. Tick-level metrics such as `labor_income_this_tick` (`core_agents.py:L558`), `capital_income_this_tick` (`core_agents.py:L566`), and `current_consumption` (`core_agents.py:L218`) are only ever incremented. They are never reset to zero at the end of a tick.

## Risk Assessment
- **High**: The failure to reset `Household` financial counters means all analytics, logging, and learning systems that consume this data will be operating on corrupt, ever-increasing values instead of tick-specific data. This completely undermines the validity of long-running simulations and violates a "Hard Rule" of the architecture.
- **Medium**: The tight coupling during agent birth increases technical debt and system fragility. Changes to global systems like `markets` or the `ai_training_manager` are more likely to have unintended side-effects on agent creation.

## Conclusion
While the death/liquidation pathway is sound, the `Household` agent's lifecycle is critically incomplete due to the missing state reset. This is a high-priority bug that must be fixed to ensure data integrity. The coupling introduced at birth should also be noted for future refactoring efforts to improve modularity.
