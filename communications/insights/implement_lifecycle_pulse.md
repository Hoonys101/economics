# Insight: Implementing Lifecycle Pulse

## Technical Approach

The implementation of `Household.reset_tick_state` and `HouseholdFactory` aims to resolve data integrity issues (accumulating tick counters) and high coupling in agent creation.

### 1. `Household.reset_tick_state`

- **Purpose**: Reset accumulators (`labor_income_this_tick_pennies`, `capital_income_this_tick_pennies`, `current_consumption`, `current_food_consumption`) to zero at the end of each tick.
- **Implementation**: Added to `Household` class in `simulation/core_agents.py`.
- **Invocation**: Called by `AgentLifecycleManager.reset_agents_tick_state`, which is invoked by `TickOrchestrator._finalize_tick`. This ensures resets happen *after* all phases and persistence.

### 2. `HouseholdFactory`

- **Purpose**: Centralize agent creation logic, enforcing Zero-Sum integrity and reducing coupling.
- **Location**: `modules/household/factory.py`.
- **Dependencies**: `HouseholdFactoryContext` (DTO) injects necessary systems (`SettlementSystem`, `Markets`, `Config`, etc.).
- **Methods**:
    - `create_newborn`: Enforces Zero-Sum by using `SettlementSystem.transfer` for initial assets (gift from parent).
    - `create_immigrant`: Initializes assets via deposit (external capital injection).
    - `create_initial_population`: Initializes assets via deposit (Genesis allocation).

## Critical Risks & Mitigations

### 1. Zero-Sum Integrity (Births)
- **Risk**: Creating a newborn with assets without deducting them from the parent breaks M2 conservation.
- **Mitigation**: `HouseholdFactory.create_newborn` accepts `initial_assets` but instantiates the agent with 0. It then executes a `SettlementSystem.transfer` from parent to child for the specified amount.

### 2. God Class Modification (`Household`)
- **Risk**: Modifying `simulation/core_agents.py` (>800 lines) carries regression risks.
- **Mitigation**: Changes are additive (`reset_tick_state`). Existing initialization logic is moved to Factory but `__init__` remains largely compatible for now (though Factory is preferred).

### 3. Dependency Injection Timing
- **Risk**: `HouseholdFactory` requires `SimulationState` components (Markets, SettlementSystem) which are initialized in `SimulationInitializer`.
- **Mitigation**: `SimulationInitializer` instantiates `HouseholdFactory` *after* creating systems and *before* creating `AgentLifecycleManager`.

## Verification Strategy

1.  **Unit Tests**:
    - `test_household_reset_tick_state`: Verify counters are reset.
    - `test_household_factory_zero_sum`: Verify `create_newborn` calls `transfer` and does not create magic money.

2.  **Integration**:
    - Verify `TickOrchestrator` calls reset at the end of tick.
    - Verify `AgentLifecycleManager` uses Factory for births.

## Refactoring Notes

- `DemographicManager` previously handled birth creation and transfers. This logic is moved to `AgentLifecycleManager` + `HouseholdFactory`.
- `DemographicManager` remains responsible for *deciding* births/deaths (Process Aging), but *execution* of creation is delegated.
