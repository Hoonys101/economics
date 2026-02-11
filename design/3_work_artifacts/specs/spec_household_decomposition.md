# modules/household/api.py

```python
from __future__ import annotations
from typing import Protocol, List, Dict, Optional, Any, TypedDict, Tuple
from dataclasses import dataclass, field

from simulation.models import Order
from modules.household.dtos import (
    BioStateDTO,
    EconStateDTO,
    SocialStateDTO,
    CloningRequestDTO,
    HouseholdSnapshotDTO
)
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.system.api import MarketSnapshotDTO
from simulation.dtos import StressScenarioConfig, LaborResult, ConsumptionResult

# --- Engine Helper DTOs ---

@dataclass
class PrioritizedNeed:
    """Represents a single, prioritized need for budget allocation."""
    need_id: str
    urgency: float  # A score from 0.0 to 1.0+ indicating importance
    deficit: float  # How much is needed to reach satisfaction
    target_quantity: float = 0.0

@dataclass
class BudgetPlan:
    """A concrete allocation of funds for the current tick."""
    allocations: Dict[str, float]  # e.g., {"food": 100, "housing": 500, "savings": 50}
    discretionary_spending: float
    orders: List[Order] = field(default_factory=list) # Orders approved by budget

@dataclass
class HousingActionDTO:
    """
    Represents a planned action related to housing (Purchase, Rent, etc.).
    Used to decouple side effects from the engine. It contains all necessary
    data for the orchestrator to execute the action.
    """
    action_type: str  # "INITIATE_PURCHASE", "MAKE_RENTAL_OFFER", "STAY", "SELL_PROPERTY"
    property_id: Optional[str] = None
    offer_price: float = 0.0
    down_payment_amount: float = 0.0 # For purchases
    buyer_id: Optional[int] = None # For systems to track originator

# --- Engine Input DTOs ---

@dataclass
class LifecycleInputDTO:
    bio_state: BioStateDTO
    econ_state: EconStateDTO # Needed for reproduction viability checks
    config: HouseholdConfigDTO
    current_tick: int

@dataclass
class NeedsInputDTO:
    bio_state: BioStateDTO
    econ_state: EconStateDTO
    social_state: SocialStateDTO
    config: HouseholdConfigDTO
    current_tick: int
    goods_data: Dict[str, Any] # For durable asset utility calculation
    market_data: Optional[Dict[str, Any]] = None

@dataclass
class SocialInputDTO:
    social_state: SocialStateDTO
    econ_state: EconStateDTO
    bio_state: BioStateDTO # For children count, age, etc.
    all_items: Dict[str, float]
    config: HouseholdConfigDTO
    current_tick: int
    market_data: Optional[Dict[str, Any]] = None # For political/social trend updates

@dataclass
class BudgetInputDTO:
    econ_state: EconStateDTO
    prioritized_needs: List[PrioritizedNeed]
    abstract_plan: List[Order]  # The AI's initial, high-level order intentions
    market_snapshot: MarketSnapshotDTO # For housing prices/rent
    config: HouseholdConfigDTO
    current_tick: int

@dataclass
class ConsumptionInputDTO:
    econ_state: EconStateDTO
    bio_state: BioStateDTO # To know current needs for satisfaction updates
    budget_plan: BudgetPlan
    market_snapshot: MarketSnapshotDTO
    config: HouseholdConfigDTO
    current_tick: int
    stress_scenario_config: Optional[StressScenarioConfig] = None # For panic selling logic

# --- Engine Output DTOs ---

@dataclass
class LifecycleOutputDTO:
    bio_state: BioStateDTO # Updated age, is_active state
    cloning_requests: List[CloningRequestDTO] # List of reproduction requests

@dataclass
class NeedsOutputDTO:
    bio_state: BioStateDTO  # Needs decay might affect bio state (e.g. survival_need_high_turns)
    prioritized_needs: List[PrioritizedNeed]

@dataclass
class SocialOutputDTO:
    social_state: SocialStateDTO

@dataclass
class BudgetOutputDTO:
    econ_state: EconStateDTO # May be updated with savings goals, housing mode, etc.
    budget_plan: BudgetPlan
    housing_action: Optional[HousingActionDTO] = None

@dataclass
class ConsumptionOutputDTO:
    econ_state: EconStateDTO # Updated inventory and balances (conceptually, to be applied by orchestrator)
    bio_state: BioStateDTO # Updated needs after consumption
    orders: List[Order] # The final, concrete orders to be placed
    social_state: Optional[SocialStateDTO] = None # Updated if leisure consumption affects social state

# --- Stateless Engine Interfaces (Protocols) ---

class ILifecycleEngine(Protocol):
    """Manages aging, death, and reproduction checks."""
    def process_tick(self, input_dto: LifecycleInputDTO) -> LifecycleOutputDTO: ...

class INeedsEngine(Protocol):
    """Calculates need decay, satisfaction, and prioritizes needs."""
    def evaluate_needs(self, input_dto: NeedsInputDTO) -> NeedsOutputDTO: ...

class ISocialEngine(Protocol):
    """Manages social status, discontent, and other social metrics."""
    def update_status(self, input_dto: SocialInputDTO) -> SocialOutputDTO: ...

class IBudgetEngine(Protocol):
    """Allocates financial resources based on needs and strategic goals."""
    def allocate_budget(self, input_dto: BudgetInputDTO) -> BudgetOutputDTO: ...

class IConsumptionEngine(Protocol):
    """Transforms a budget plan into concrete consumption and market orders."""
    def generate_orders(self, input_dto: ConsumptionInputDTO) -> ConsumptionOutputDTO: ...
```

# design/3_work_artifacts/specs/household_engine_refactor_spec.md

```markdown
# Spec: Household Agent Engine-Based Refactoring

## 1. Introduction

This document outlines the specification for refactoring the `Household` agent from a monolithic class into a modern, modular architecture. The current implementation mixes state, orchestration, and business logic, making it difficult to test, maintain, and extend.

The primary goal is to separate concerns by adopting an **Orchestrator-Engine pattern**. The `Household` class will become a stateful **Orchestrator**, delegating all business logic to a suite of **stateless Engines**. This refactoring directly addresses the critical risks identified in the pre-flight audit, paving the way for a more robust and scalable agent model.

## 2. Architectural Overview

The new architecture is composed of two main parts:

1.  **Household Orchestrator**: The `Household` class instance. Its sole responsibilities are:
    *   To own and manage the agent's state via three dedicated DTOs: `_bio_state`, `_econ_state`, and `_social_state`.
    *   To orchestrate the sequence of calls to the stateless engines during its `update_needs` and `make_decision` phases.
    *   To apply the state changes returned by the engines.
    *   To handle interactions with external systems (e.g., `HousingSystem`, `Market`).

2.  **Stateless Engines**: A collection of modules containing pure business logic. They receive state DTOs as input and return new/updated DTOs as output. They **do not** hold any internal state (`self.xxx`) between calls.
    *   `LifecycleEngine`: Manages aging, death, and reproduction.
    *   `NeedsEngine`: Manages need decay and prioritization.
    *   `SocialEngine`: Manages social status, conformity, and discontent.
    *   `BudgetEngine`: Manages financial planning and resource allocation.
    *   `ConsumptionEngine`: Generates concrete market orders from a budget plan.

### New Orchestration Flow

**A. `update_needs()` Flow:**
```
Household.update_needs()
 |
 +--> LifecycleEngine.process_tick(bio_state, econ_state) -> returns updated bio_state, cloning_requests
 |
 +--> NeedsEngine.evaluate_needs(bio_state, econ_state, social_state) -> returns updated bio_state, prioritized_needs
 |
 +--> SocialEngine.update_status(social_state, econ_state, bio_state) -> returns updated social_state
```

**B. `make_decision()` Flow:**
```
Household.make_decision()
 |
 +--> [AI] AIDrivenHouseholdDecisionEngine.make_decisions(snapshot_dto) -> returns abstract_plan
 |      (NOTE: This is the legacy bottleneck. See Audit Section.)
 |
 +--> BudgetEngine.allocate_budget(econ_state, prioritized_needs, abstract_plan) -> returns updated econ_state, budget_plan, housing_action
 |
 +--> (Side-Effect) Household executes housing_action via external HousingSystem
 |
 +--> ConsumptionEngine.generate_orders(econ_state, bio_state, budget_plan) -> returns final_orders, updated state
```

## 3. Engine Specifications

### 3.1. ILifecycleEngine
-   **Responsibility**: Handles aging, mortality, and generating reproduction requests.
-   **Interface**: `process_tick(input_dto: LifecycleInputDTO) -> LifecycleOutputDTO`
-   **Pseudo-code**:
    1.  Receive `LifecycleInputDTO(bio_state, econ_state, config, current_tick)`.
    2.  Create a mutable copy of `bio_state`.
    3.  Increment `bio_state.age`.
    4.  Check for mortality based on age and config rules. If dead, set `bio_state.is_active = False`. Return `LifecycleOutputDTO`.
    5.  Check for reproduction window based on age and config.
    6.  If in window, check economic viability for reproduction (e.g., enough assets in `econ_state`).
    7.  If viable, generate a `CloningRequestDTO`.
    8.  Return `LifecycleOutputDTO(bio_state=updated_bio_state, cloning_requests=[...])`.

### 3.2. INeedsEngine
-   **Responsibility**: Calculates need decay and prioritizes needs for budgeting.
-   **Interface**: `evaluate_needs(input_dto: NeedsInputDTO) -> NeedsOutputDTO`
-   **Pseudo-code**:
    1.  Receive `NeedsInputDTO`.
    2.  Create a mutable copy of `bio_state`.
    3.  For each need in `bio_state.needs`:
        a. Apply decay based on `config.need_decay_rates`.
        b. If need is below a critical threshold (e.g., 'survival'), increment `bio_state.survival_need_high_turns`.
    4.  Calculate the deficit for each need (target - current).
    5.  Calculate the urgency for each need based on deficit, personality (`social_state.desire_weights`), and external factors.
    6.  Create a list of `PrioritizedNeed` objects, sorted by urgency.
    7.  Return `NeedsOutputDTO(bio_state=updated_bio_state, prioritized_needs=list_of_needs)`.

### 3.3. IBudgetEngine
-   **Responsibility**: Creates a concrete financial plan for the tick.
-   **Interface**: `allocate_budget(input_dto: BudgetInputDTO) -> BudgetOutputDTO`
-   **Pseudo-code**:
    1.  Receive `BudgetInputDTO(econ_state, prioritized_needs, abstract_plan, market_snapshot, config, current_tick)`.
    2.  Create a mutable copy of `econ_state` and an empty `BudgetPlan`.
    3.  Determine total available cash from `econ_state.wallet`.
    4.  **Housing Logic**:
        a. Evaluate current housing situation (`is_homeless`, rent vs. own).
        b. Based on `market_snapshot` housing prices/rents, decide on a housing action (buy, rent, stay).
        c. If action is decided, create a `HousingActionDTO` with all required data (e.g., `offer_price`, `down_payment_amount`).
        d. Reserve funds for the housing action in the budget.
    5.  **Needs Fulfillment**:
        a. Iterate through `prioritized_needs`.
        b. Allocate funds from remaining cash to satisfy each need, creating `Order` objects for the `BudgetPlan`.
    6.  **Savings & Investment**: Allocate remaining discretionary funds to savings based on agent personality and goals.
    7.  Return `BudgetOutputDTO(econ_state=updated_econ_state, budget_plan=plan, housing_action=action)`.

### 3.4. IConsumptionEngine
-   **Responsibility**: Executes the budget plan, generating final market orders.
-   **Interface**: `generate_orders(input_dto: ConsumptionInputDTO) -> ConsumptionOutputDTO`
-   **Pseudo-code**:
    1.  Receive `ConsumptionInputDTO(econ_state, bio_state, budget_plan, market_snapshot, config, current_tick, stress_scenario_config)`.
    2.  Create mutable copies of `econ_state` and `bio_state`.
    3.  **Panic Selling (Stress Test)**: If `stress_scenario_config` indicates distress, liquidate assets (portfolio, inventory) by generating SELL orders. Return immediately.
    4.  **Execute Budget**:
        a. The `budget_plan.orders` are the primary consumption orders. Add them to the final list of orders.
    5.  **Consume from Inventory**:
        a. For needs that can be fulfilled by existing inventory (`econ_state.inventory`), "consume" them (reduce inventory quantity).
        b. Update `bio_state.needs` to reflect satisfaction.
    6.  **Leisure Consumption**:
        a. Based on remaining time/funds, decide on leisure activities.
        b. Update social state (optimism, etc.) based on leisure. Generate a `social_state` update if needed.
    7.  Return `ConsumptionOutputDTO(econ_state=..., bio_state=..., orders=final_orders, social_state=...)`.

## 4. 🚨 Risk & Impact Audit: Resolution Plan

This refactoring is governed by the pre-flight audit. The following plan is mandatory.

-   **1. Critical Risk: Legacy DTO Architectural Coupling**
    -   **Action**: The **immediate next step** after this engine refactoring is to upgrade the `AIDrivenHouseholdDecisionEngine` and its sub-managers (`ConsumptionManager`, `LaborManager`, `AssetManager`).
    -   **Requirement**: They **MUST** be refactored to accept the modern `HouseholdSnapshotDTO` as their primary input instead of the deprecated `HouseholdStateDTO`.
    -   **Outcome**: This will break the architectural circular dependency and allow for the removal of the fragile `Household.create_state_dto()` translation method.

-   **2. Critical Risk: Fragile State Management & Duplication**
    -   **Action**: A new test suite, `tests/modules/household/test_dtos.py`, will be created.
    -   **Requirement**: This suite will contain tests specifically for the `.copy()` method of each state DTO (`BioStateDTO`, `EconStateDTO`, `SocialStateDTO`). It will programmatically add a value to a collection in the copied object and assert that the original object is not modified. Using `copy.deepcopy` is recommended, with custom `__deepcopy__` methods implemented for complex types like `IWallet` and `Portfolio` to ensure true isolation.
    -   **Outcome**: Guarantees state isolation and prevents silent, shared-state bugs.

-   **3. Architectural Risk: Implicit Side-Effects (Housing)**
    -   **Action**: The `HousingActionDTO` defined in `modules/household/api.py` will be the sole data contract for housing decisions.
    -   **Requirement**: It must be comprehensive. The `BudgetEngine` is responsible for populating it completely, including `action_type`, `property_id`, `offer_price`, and `down_payment_amount`. The `Household` orchestrator's role is confirmed to be the executor of this DTO, interacting with the `HousingSystem`.
    -   **Outcome**: Maintains clear separation of concerns (planning vs. execution) and prevents data loss between the engine and the orchestrator.

-   **4. Test-Related Risk: Brittle `clone()` Method**
    -   **Action**: A new `HouseholdFactory` will be implemented in `simulation/factories/agent_factory.py`.
    -   **Requirement**: The `Household.clone()` method will be marked as `@deprecated`. All call sites, particularly in `DemographicManager` and the test suite, **MUST** be refactored to use `HouseholdFactory.create(...)` or `HouseholdFactory.create_offspring(...)`.
    -   **Outcome**: Centralizes agent creation logic, eliminates brittle test dependencies on `clone()`, and simplifies the `Household` class.

## 5. Verification & Testing Strategy

-   **Unit Tests**: Each engine (`LifecycleEngine`, `NeedsEngine`, etc.) will have a dedicated test file in `tests/modules/household/engines/`. These tests will validate the engine's logic in complete isolation by feeding it input DTOs and asserting the content of the output DTOs.
-   **Integration Tests**: `tests/simulation/test_household_orchestration.py` will be created to test the `Household` class's role as an orchestrator. It will use mocked engines to verify that they are called in the correct order and that their outputs are correctly applied to the agent's state.
-   **Golden Master Tests**: Existing end-to-end simulation tests will serve as the golden master. The simulation will be run before and after the refactor with a fixed seed, and the final state (e.g., total wealth, population) must be identical. This proves the refactor was purely structural.
-   **Test Impact**:
    -   Tests relying on `Household.clone()` must be updated to use the new `HouseholdFactory`.
    -   Tests that patch methods on the monolithic `Household` class (e.g., `@patch('Household.decide_consumption')`) must be updated to patch the corresponding method on the new engine (e.g., `@patch('modules.household.engines.ConsumptionEngine.generate_orders')`).

## 6. Mandatory Reporting Verification

All insights, unforeseen complexities, or potential technical debt discovered during the implementation of this specification **MUST** be documented in a new file under `communications/insights/`. The filename should be `[HH_Engine_Refactor]_<Topic>.md`. This is a non-negotiable step for mission completion.
```
