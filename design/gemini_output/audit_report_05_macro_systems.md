# Report: Macro-Scheduling & Global Systems Audit (WO-101-5)

## Executive Summary
The audit reveals that the simulation's execution order is highly centralized within the (unseen) `Simulation.run_tick()` method, creating significant architectural risks. The sequence of transaction processing relative to agent lifecycle events (bankruptcy/death) is the most critical constraint; an incorrect order could lead to catastrophic economic inconsistencies, such as firms being liquidated before their sales to households are processed.

## Detailed Analysis

### 1. Tick Sequencing & Scheduling
- **Status**: ⚠️ Partial
- **Evidence**:
  - The main loop in `main.py:L489` consists solely of `sim.run_tick()`, indicating all tick logic is encapsulated within the `Simulation` class.
  - `simulation/systems/lifecycle_manager.py:L26` defines `process_lifecycle_events`, which handles aging, birth, immigration, and critically, `_handle_agent_liquidation` (death/bankruptcy).
  - `simulation/systems/transaction_processor.py:L23` defines `process`, which handles the financial settlement of transactions (asset transfers, inventory changes, taxation).
- **Notes**: The precise order of operations is not visible but can be inferred. A logical but unverified sequence is: 1. Agent Decisions, 2. Market Clearing, 3. Transaction Processing, 4. Lifecycle Events. Reversing steps 3 and 4 would be catastrophic, as agents could be removed before their final transactions are settled. **This sequence is the single most important architectural constraint.**

### 2. Hidden Dependencies & God Classes
- **Status**: ❌ Missing (High Risk)
- **Evidence**:
  - **`Simulation` Class**: The `Simulation` object, constructed by `SimulationInitializer` in `main.py:L458`, acts as a "God Object." It holds all agents, markets, and systems. System components like `AgentLifecycleManager` require the `sim` object to be passed to them (`lifecycle_manager.py:L26`), creating a direct dependency on the central orchestrator.
  - **`main.py`**: The `create_simulation` function (`main.py:L74-L462`) is over 380 lines long, violating SRP by mixing AI setup, agent instantiation, dependency injection, and initial economic conditions.
- **Notes**: While refactoring has begun by extracting `TransactionProcessor` and `AgentLifecycleManager`, the core `run_tick` loop remains a black-box nexus of dependencies. Any modification requires understanding this central, unseen method.

### 3. Hardcoded Configuration Influence
- **Status**: ✅ Implemented
- **Evidence**:
  - **Taxation**: `TransactionProcessor` directly calculates taxes based on hardcoded rates from `config.py` (e.g., `SALES_TAX_RATE`, `INCOME_TAX_PAYER`).
  - **Lifecycle**: `AgentLifecycleManager` implicitly relies on `FIRM_CLOSURE_TURNS_THRESHOLD` and `HOUSEHOLD_DEATH_TURNS_THRESHOLD` from `config.py` to determine which agents are inactive and thus subject to liquidation.
  - **System Intervals**: Global systems operate on fixed schedules defined in `config.py`, such as `GOV_ACTION_INTERVAL = 30` and `CB_UPDATE_INTERVAL = 10`, creating a rigid operational hierarchy.
- **Notes**: The simulation is highly sensitive to these configuration values. They are not emergent properties but are externally imposed rules that dictate the simulation's rhythm and economic laws.

## Risk Assessment
- **Critical Risk**: The primary risk is the unverified execution order within `Simulation.run_tick()`. A bug causing the `AgentLifecycleManager` to run before the `TransactionProcessor` would invalidate market outcomes for any agent that goes bankrupt in that tick, leading to cascading failures and untraceable simulation errors.
- **Test Fragility**: Any tests for economic consistency (e.g., conservation of money) are brittle. They depend entirely on the correct, implicit scheduling within `run_tick`. A minor change to this sequence could break all such tests.
- **Circular Dependencies**: The use of `if TYPE_CHECKING:` in `simulation/systems/api.py` confirms that circular import risks are present and being actively managed. The `Simulation` object is the hub that connects all systems, and this pattern is used to break what would otherwise be direct import cycles.

## Conclusion & Architectural Constraints for Spec
The macro-level architecture is a centralized, sequential process orchestrated by a single, untyped `Simulation` object. When writing the spec for any new feature or refactor, the following constraints MUST be respected:

1.  **Acknowledge Central Orchestration**: All system-level processes are initiated from `Simulation.run_tick()`. New systems must be integrated into this central method.
2.  **Respect The Sacred Sequence**: The core logic flow **MUST** be assumed as: **(1) Decisions → (2) Market Clearing → (3) Transaction Processing → (4) Lifecycle Management**. State-modifying logic (e.g., calculating revenue, updating inventory) must occur *before* agents are potentially removed from the simulation via liquidation.
3.  **State is Passed, Not Held**: New "System" components (like `TransactionProcessor`) should be stateless services. They receive the current simulation state (agent lists, markets) from the `run_tick` method, process it, and mutate it directly. They should not hold their own persistent state across ticks.
4.  **Configuration is King**: All fundamental economic rules (tax rates, lifecycle thresholds, system action intervals) are defined in `config.py` and should be treated as immutable within a single tick. Do not override these values at runtime unless it is part of a specific, managed scenario.
