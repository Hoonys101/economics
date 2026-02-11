# Spec: Lifecycle Pulse & Factory

## 1. Introduction

- **Purpose**: This document outlines the design to resolve critical data integrity and coupling issues identified in `audit_lifecycle_hygiene_20260211.md`.
- **Scope**:
    1.  Implement a `reset()` method on the `Household` agent to ensure tick-level financial data is not corrupted over time.
    2.  Introduce a `HouseholdFactory` to decouple agent creation from the `AgentLifecycleManager`, improving modularity and testability.
- **Goals**:
    - Adhere to the "Late-Reset Principle" from `LIFECYCLE_HYGIENE.md`.
    - Reduce tight coupling during agent instantiation.
    - Provide a clear, testable, and centralized pattern for agent creation.

---

## 2. Detailed Design

### 2.1. Component: `Household.reset()` Method

A new public method will be added to the `Household` class in `simulation/core_agents.py`.

- **Description**: This method resets all tick-specific accumulators to zero. It is designed to be called once per agent at the end of a simulation tick.
- **API/Interface**:
    - `reset_tick_state()`: Resets `labor_income_this_tick_pennies`, `capital_income_this_tick_pennies`, `current_consumption`, and `current_food_consumption` to zero.
- **Pseudo-code (`simulation/core_agents.py`)**:

```python
class Household(
    # ... existing base classes
):
    # ... existing __init__ and methods

    def reset_tick_state(self) -> None:
        """
        Resets tick-level financial accumulators to zero.
        Adheres to the "Late-Reset Principle".
        """
        self._econ_state.labor_income_this_tick_pennies = 0
        self._econ_state.capital_income_this_tick_pennies = 0
        self._econ_state.current_consumption = 0.0
        self._econ_state.current_food_consumption = 0.0
        self.logger.debug(
            f"TICK_RESET | Agent {self.id} tick state has been reset.",
            extra={"agent_id": self.id, "tags": ["lifecycle", "reset"]}
        )

    # ... rest of the class
```

### 2.2. Component: `HouseholdFactory`

A new factory will be created to handle the instantiation and configuration of `Household` agents. This centralizes the complex creation logic and decouples other systems from the `Household` constructor's details.

**Location**: `modules/household/factory.py`

- **Description**: The factory will take all necessary dependencies via a context DTO and provide methods to create different types of households (e.g., initial, newborn, immigrant).
- **API/Interface (`modules/household/api.py`)**:

```python
from __future__ import annotations
from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass

# Forward declarations
class Household: ...
class AgentCoreConfigDTO: ...
class HouseholdConfigDTO: ...
class IDecisionEngine: ...
class Personality: ...
class Talent: ...
class LoanMarket: ...
class SimulationState: ... # To be avoided in final implementation, for context only

@dataclass
class HouseholdFactoryContext:
    """DTO to provide all necessary dependencies for household creation."""
    # Configs
    core_config_module: Any
    household_config_dto: HouseholdConfigDTO
    goods_data: List[Dict[str, Any]]
    # Systems & Global State
    loan_market: Optional[LoanMarket]
    # Required for AI engine instantiation
    ai_training_manager: Any
    # Required for dependency injection post-creation
    settlement_system: Any
    markets: Dict[str, Any]
    memory_system: Any # Example: V2 memory interface


class IHouseholdFactory(Protocol):
    """Interface for creating Household agents."""

    def create_newborn(
        self,
        parent: Household,
        new_id: int,
        initial_assets: int,
        current_tick: int
    ) -> Household:
        """Creates a new household as a child of an existing one."""
        ...

    def create_immigrant(
        self,
        new_id: int,
        current_tick: int,
        initial_assets: int
    ) -> Household:
        """Creates a new household representing an immigrant."""
        ...

    def create_initial_population(
        self,
        num_agents: int
    ) -> List[Household]:
        """Creates the initial population of households for the simulation."""
        ...
```

- **Pseudo-code (`modules/household/factory.py`)**:

```python
# Implementation of IHouseholdFactory
class HouseholdFactory:
    def __init__(self, context: HouseholdFactoryContext):
        self.context = context

    def _create_base_household(self, core_config, personality, initial_assets, **kwargs) -> Household:
        # 1. Create the AI/Decision Engine
        # Logic to instantiate AIDrivenHouseholdDecisionEngine, etc.
        # This was previously hidden inside DemographicManager or tests
        engine = self._create_decision_engine(personality)

        # 2. Instantiate the Household
        household = Household(
            core_config=core_config,
            engine=engine,
            talent=Talent(...), # Generate talent
            personality=personality,
            config_dto=self.context.household_config_dto,
            goods_data=self.context.goods_data,
            loan_market=self.context.loan_market,
            initial_assets_record=initial_assets,
            **kwargs
        )
        household.deposit(initial_assets)

        # 3. Inject Dependencies (replaces logic from _register_new_agents)
        household.decision_engine.markets = self.context.markets
        household.decision_engine.goods_data = self.context.goods_data
        if hasattr(household, 'settlement_system'):
            household.settlement_system = self.context.settlement_system

        # 4. Register with other systems
        if self.context.ai_training_manager:
            self.context.ai_training_manager.agents.append(household)

        return household

    def create_newborn(self, parent, new_id, initial_assets, current_tick):
        # ... logic to determine personality, demographics from parent
        # ... call _create_base_household
        return new_household

    # ... other creation methods
```

### 2.3. System: `AgentLifecycleManager` Modifications

The `AgentLifecycleManager` will be updated to use the new `HouseholdFactory` and to orchestrate the end-of-tick state reset.

- **Dependency Injection**: The `AgentLifecycleManager` will receive the `IHouseholdFactory` instance in its constructor.
- **Refactoring `_process_births` & `_register_new_agents`**: The logic for creating new agents will be removed from these methods and replaced with calls to the factory. The `_register_new_agents` function will now only be responsible for adding the factory-built agent to the global state lists (`state.households`, `state.agents`).
- **New Method `reset_agents_tick_state`**: A new method will be added to iterate through all active agents and call their `reset_tick_state` method. This method should be called by the main simulation loop *after* all other systems have executed for the tick.

- **Pseudo-code (`simulation/systems/lifecycle_manager.py`)**:

```python
class AgentLifecycleManager(AgentLifecycleManagerInterface):
    def __init__(self, ..., household_factory: IHouseholdFactory): # Add factory
        # ...
        self.household_factory = household_factory
        # ...

    def execute(self, state: SimulationState) -> List[Transaction]:
        # ... (Aging, Distress Checks)

        # 3. Births
        new_children = self._process_births(state) # Now returns List[Household] from factory
        self._register_new_agents(state, new_children)

        # ... (Immigration, Entrepreneurship, Liquidation) ...

        return self._handle_agent_liquidation(state) # As before

    def reset_agents_tick_state(self, state: SimulationState) -> None:
        """
        Calls the reset method on all active agents at the end of a tick.
        """
        self.logger.info("LIFECYCLE_PULSE | Resetting tick-level state for all agents.")
        for household in state.households:
            if household.is_active:
                household.reset_tick_state()

        for firm in state.firms:
            if firm.is_active:
                firm.reset() # Uses existing Firm.reset() method

    def _process_births(self, state: SimulationState) -> List[Household]:
        # ... (decide_breeding_batch logic) ...
        
        created_children = []
        for parent_agent in birth_requests:
            # ... (logic to determine inheritance, new ID) ...
            child = self.household_factory.create_newborn(
                parent=parent_agent,
                new_id=new_id,
                initial_assets=inherited_assets,
                current_tick=state.time
            )
            created_children.append(child)
        return created_children

    def _register_new_agents(self, state: SimulationState, new_agents: List[Household]):
        for agent in new_agents:
            state.households.append(agent)
            state.agents[agent.id] = agent

            if isinstance(agent, ICurrencyHolder):
                state.register_currency_holder(agent)
            
            # Note: All other dependency injection is now handled by the factory
```

---

## 3. 검증 계획 (Testing & Verification Strategy)

- **New Test Cases**:
    - `test_household_reset_tick_state`: A unit test to verify that calling `Household.reset_tick_state()` correctly zeroes out `labor_income_this_tick_pennies`, `capital_income_this_tick_pennies`, and `current_consumption`.
    - `test_lifecycle_manager_orchestrates_reset`: An integration test to ensure `AgentLifecycleManager.reset_agents_tick_state` correctly calls the `reset` method on all active agents in the simulation state.
    - `test_household_factory_creation`: A unit test for the `HouseholdFactory` to ensure it can create a valid `Household` instance with all dependencies correctly injected.

- **Existing Test Impact**:
    - **High Impact**: Tests that create `Household` instances directly (`Household(...)`) must be refactored to use the new `HouseholdFactory`. This ensures creation logic is consistent and respects the new decoupled architecture. A test-specific factory or mock factory can be used.
    - **Medium Impact**: Integration tests that assert agent financial data (income, consumption) across multiple ticks will fail. These tests must be updated to account for the values being reset at the end of each tick. Assertions should be made *within* a tick, before the reset is called.

- **Integration Check**:
    - A full simulation run of at least 100 ticks must be performed, with logging enabled for the `reset_tick_state` method. The logs must confirm that financial counters are being reset for every active agent at the end of every tick. Analytics data must show tick-by-tick income and consumption, not ever-increasing cumulative values.

---

## 4. 🚨 Risk & Impact Audit (기술적 위험 분석)

- **순환 참조 위험**: This design avoids circular imports. The `AgentLifecycleManager` depends on the `IHouseholdFactory` interface, but the `HouseholdFactory` implementation does not depend on the `AgentLifecycleManager`. Dependencies flow downwards from the orchestrator.
- **테스트 영향도**: The risk is **High**. A significant number of tests that rely on direct `Household` instantiation will break. **Mitigation**: A dedicated effort must be allocated to refactor these tests. The `Household.clone()` method, used in many tests, must be updated to use the factory's logic internally or be replaced entirely.
- **설정 의존성**: The `HouseholdFactory` will need access to a wide range of configuration and global state. The `HouseholdFactoryContext` DTO is designed to manage this, but it still relies on a "god object" (`SimulationState`) to populate it. This is an accepted trade-off to avoid making the factory itself a god object.
- **선행 작업 권고**: The test refactoring is a mandatory prerequisite for merging this change. The team must agree on a strategy for creating agents in a test environment (e.g., using a pre-configured factory instance available via a pytest fixture).

---

## 5. 🚨 Mandatory Reporting Verification

- **Status**: ✅ Verified.
- **Description**: The process of analyzing the audit and designing this specification has generated insights into the project's dependency management and testing strategies. These findings are recorded in a separate report.
- **Reference**: `communications/insights/spec_lifecycle_pulse_insights.md`
