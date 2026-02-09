# Design Document: Household Agent Decomposition (TD-260)

## 1. Introduction

- **Purpose**: This document outlines the design for refactoring the `Household` agent to resolve technical debt **TD-260**.
- **Scope**: The current Mixin-based architecture (`HouseholdLifecycleMixin`, `HouseholdFinancialsMixin`, etc.) will be decomposed into a series of pure, stateless "Engine" components orchestrated by the main `Household` class.
- **Goals**:
    - Reduce the complexity of the `Household` agent.
    - Improve modularity, testability, and maintainability.
    - Enforce architectural purity by adhering to a stateless, DTO-driven design, avoiding the known anti-patterns documented in `ARCH_AGENTS.md`.

## 2. System Architecture (Orchestrator & Stateless Engines)

The `Household` agent will be refactored to follow an **Orchestrator-Engine** model.

- **`Household` (Orchestrator)**: The `Household` class will be the sole stateful entity. It will own the agent's complete state via the `BioStateDTO`, `EconStateDTO`, and `SocialStateDTO`. Its primary responsibility is to coordinate the sequence of operations by calling stateless engines, passing the required state via DTOs, and integrating the results.

- **Stateless Engines**: These are pure, stateless components (implemented as classes with methods) that contain the core business logic.
    - **Critical Constraint**: Engines **MUST NOT** hold a reference to the parent `Household` instance.
    - **Data Flow**: All engine methods will accept DTOs as input and return new or updated DTOs as output. They will have no side effects.

This architecture directly addresses the risks identified in the **Pre-flight Audit** by ensuring a clean separation of state and logic.

 <!-- Placeholder for a diagram -->

## 3. Detailed Design

### 3.1. Component: `Household` (Orchestrator)

The `make_decision` method will be restructured to orchestrate calls to the new engines in a precise sequence.

#### 3.1.1. New `make_decision` Orchestration Flow (Pseudo-code)

```python
def make_decision(self, input_dto: DecisionInputDTO) -> Tuple[List["Order"], Tuple["Tactic", "Aggressiveness"]]:
    # Phase 1: State Update & Perception
    # Update internal state based on world events (e.g., received income). This part remains.
    
    # Phase 2: Internal State Progression (Engine Calls)
    
    # 2.1. Lifecycle & Biology
    lifecycle_input = LifecycleInputDTO(bio_state=self._bio_state, config=self.config)
    lifecycle_output = self.lifecycle_engine.process_tick(lifecycle_input)
    self._bio_state = lifecycle_output.bio_state # Update state
    
    # If agent is no longer active, terminate early.
    if not self.is_active:
        return [], (Tactic.IDLE, Aggressiveness.NORMAL)

    # 2.2. Needs Assessment
    needs_input = NeedsInputDTO(bio_state=self._bio_state, econ_state=self._econ_state, social_state=self._social_state, config=self.config)
    needs_output = self.needs_engine.evaluate_needs(needs_input)
    # needs_output contains prioritized needs, which will be used by the budget engine.

    # 2.3. Social Status Update
    social_input = SocialInputDTO(social_state=self._social_state, econ_state=self._econ_state, all_items=self.get_all_items(), config=self.config)
    self._social_state = self.social_engine.update_status(social_input)

    # Phase 3: Economic Planning (AI + Rule-Based Engines)

    # 3.1. Prepare context for the core AI decision engine
    context = self._build_decision_context(...) # As before

    # 3.2. Run Core AI Decision Engine to get abstract strategy
    # This part remains the same, it returns an abstract plan (e.g., initial orders, tactic).
    initial_orders, chosen_tactic_tuple = self.decision_engine.make_decisions(context, macro_context)

    # 3.3. Budget Finalization (New Engine)
    # The AI's abstract plan is now a key input for concrete budgeting.
    budget_input = BudgetInputDTO(
        econ_state=self._econ_state, 
        prioritized_needs=needs_output.prioritized_needs, 
        abstract_plan=initial_orders,
        config=self.config
    )
    budget_output = self.budget_engine.allocate_budget(budget_input)
    self._econ_state = budget_output.econ_state # Budgeting might update expected savings, etc.

    # 3.4. Consumption & Order Generation
    # The DecisionUnit is refactored into a stateless ConsumptionEngine
    consumption_input = ConsumptionInputDTO(
        econ_state=self._econ_state,
        budget_plan=budget_output.budget_plan,
        market_snapshot=input_dto.market_snapshot,
        config=self.config
    )
    consumption_output = self.consumption_engine.generate_orders(consumption_input)
    self._econ_state = consumption_output.econ_state # Update state with consumption details
    refined_orders = consumption_output.orders
    
    # Return final, concrete orders
    return refined_orders, chosen_tactic_tuple
```

### 3.2. New Stateless Engines

#### 3.2.1. `LifecycleEngine`
- **Responsibility**: Manages aging, death, and reproduction logic, previously in `HouseholdLifecycleMixin` and `HouseholdReproductionMixin`.
- **API**:
  - `process_tick(input: LifecycleInputDTO) -> LifecycleOutputDTO`: Increments age, checks for death based on age and needs, and handles reproduction logic.
- **DTOs**:
  - `LifecycleInputDTO`: `bio_state`, `config`.
  - `LifecycleOutputDTO`: Updated `bio_state`, `cloning_requests` (for newborns).

#### 3.2.2. `NeedsEngine`
- **Responsibility**: Calculates need decay, satisfaction, and prioritizes current needs.
- **API**:
  - `evaluate_needs(input: NeedsInputDTO) -> NeedsOutputDTO`: Calculates current needs urgency and creates a prioritized list for the budgeting phase.
- **DTOs**:
  - `NeedsInputDTO`: `bio_state`, `econ_state`, `social_state`, `config`.
  - `NeedsOutputDTO`: `prioritized_needs` (list of needs with scores), updated `bio_state`.

#### 3.2.3. `SocialEngine`
- **Responsibility**: Manages social status, discontent, and other social metrics. Replaces logic from `social_component`.
- **API**:
  - `update_status(input: SocialInputDTO) -> SocialStateDTO`: Recalculates social status based on wealth, assets, and consumption.
- **DTOs**:
  - `SocialInputDTO`: `social_state`, `econ_state`, `all_items`, `config`.

#### 3.2.4. `BudgetEngine`
- **Responsibility**: Allocates financial resources based on income, prioritized needs, and the AI's abstract strategic goals.
- **API**:
  - `allocate_budget(input: BudgetInputDTO) -> BudgetOutputDTO`: Creates a concrete budget plan, allocating funds for survival, savings, social activities, etc.
- **DTOs**:
  - `BudgetInputDTO`: `econ_state`, `prioritized_needs`, `abstract_plan`, `config`.
  - `BudgetOutputDTO`: `budget_plan` (dict mapping categories to amounts), updated `econ_state`.

#### 3.2.5. `ConsumptionEngine`
- **Responsibility**: Transforms a budget plan into a concrete list of consumption actions and market orders. This replaces the logic in `DecisionUnit`.
- **API**:
  - `generate_orders(input: ConsumptionInputDTO) -> ConsumptionOutputDTO`: Decides which goods to consume from inventory and which to purchase from the market to satisfy needs within the allocated budget.
- **DTOs**:
  - `ConsumptionInputDTO`: `econ_state`, `budget_plan`, `market_snapshot`, `config`.
  - `ConsumptionOutputDTO`: `orders` (list of `Order` objects), updated `econ_state`.


## 4. Data Model (New DTOs)

The new DTOs will be defined in `modules/household/api.py`.

```python
# In modules/household/api.py

from typing import TypedDict, List, Dict
from dataclasses import dataclass

# ... existing DTOs like BioStateDTO, EconStateDTO ...

# --- Engine Input/Output DTOs ---

@dataclass
class LifecycleInputDTO:
    bio_state: BioStateDTO
    config: HouseholdConfigDTO

@dataclass
class LifecycleOutputDTO:
    bio_state: BioStateDTO
    cloning_requests: List[CloningRequestDTO]

# ... other DTOs for Needs, Social, Budget, Consumption engines ...

@dataclass
class PrioritizedNeed:
    need_id: str
    urgency: float
    target_quantity: float

@dataclass
class NeedsOutputDTO:
    bio_state: BioStateDTO
    prioritized_needs: List[PrioritizedNeed]
    
@dataclass
class BudgetPlan:
    allocations: Dict[str, float] # e.g., {"food": 100, "housing": 500, "savings": 50}

@dataclass
class BudgetOutputDTO:
    econ_state: EconStateDTO
    budget_plan: BudgetPlan

# ... etc.
```

## 5. Verification Plan (Test Strategy)

This refactoring requires a parallel test refactoring effort.

1.  **Engine Unit Tests**: For each new stateless engine (`NeedsEngine`, `BudgetEngine`, etc.), create a new dedicated test file. These tests will be simple, pure function tests:
    - Instantiate the engine.
    - Create input DTOs using `golden_households` fixtures or manually crafted data.
    - Call the engine's method.
    - Assert that the output DTO matches the expected result.
    - **This approach avoids all mocking of parent classes or dependencies.**

2.  **Orchestrator Integration Tests**: Existing tests for `Household` will be refactored.
    - Instead of mocking Mixin methods (e.g., `_handle_death`), the tests will now mock the *engines*.
    - Example: `mocker.patch.object(household_instance, 'lifecycle_engine')`.
    - The mocked engine will be configured to return a specific output DTO, allowing tests to control the orchestration flow at each step.

3.  **End-to-End Tests**: Full simulation runs will serve as the final validation that the decomposed agent behaves correctly within the larger system.

## 6. Risk & Impact Audit

This design explicitly addresses the risks identified in the pre-flight audit:

- **Stateless Engine Architecture**: The core principle of this design is the strict separation of state (`Household`) and logic (`Engines`). The "no parent reference" rule will be enforced during code review.
- **DTO-Driven State Management**: The orchestration flow is entirely dependent on passing granular DTOs between the orchestrator and the engines, preventing implicit state dependencies.
- **Orchestration Complexity**: The new `make_decision` pseudo-code provides a clear, sequential plan for engine coordination, reducing the risk of logical errors.
- **High Risk to Existing Tests**: The verification plan acknowledges the significant test breakage and outlines a clear strategy for both writing new isolated tests and refactoring existing integration tests.

## 7. Mandatory Reporting Verification

All insights, challenges, and discovered technical debt during the implementation of this design will be logged in a dedicated report: `communications/insights/TD-260-HouseholdDecomposition.md`. This ensures that all learnings from this major refactoring are captured for future architectural decisions.

---
`file:modules/household/api.py`
```python
"""
Public API for the Household module.

This file defines the interfaces (Protocols) and Data Transfer Objects (DTOs)
that other modules should use to interact with the Household module.
"""
from __future__ import annotations
from typing import Protocol, List, Dict
from dataclasses import dataclass

from simulation.models import Order
from simulation.ai.api import Tactic, Aggressiveness
from modules.household.dtos import (
    BioStateDTO,
    EconStateDTO,
    SocialStateDTO,
    CloningRequestDTO,
    HouseholdSnapshotDTO
)
from modules.simulation.api import AgentCoreConfigDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO
from simulation.dtos.snapshot import MarketSnapshot

# === Existing DTOs (from dtos.py) ===
# Re-export for clarity if needed, or assume they are imported where used.
# from .dtos import HouseholdStateDTO, OrchestrationContextDTO


# === New DTOs for Decomposed Engines ===

@dataclass
class PrioritizedNeed:
    """Represents a single, prioritized need for budget allocation."""
    need_id: str
    urgency: float  # A score from 0.0 to 1.0+ indicating importance
    deficit: float  # How much is needed to reach satisfaction
    
@dataclass
class BudgetPlan:
    """A concrete allocation of funds for the current tick."""
    allocations: Dict[str, float]  # e.g., {"food": 100, "housing": 500, "savings": 50}
    discretionary_spending: float

# --- Engine Input DTOs ---

@dataclass
class LifecycleInputDTO:
    bio_state: BioStateDTO
    econ_state: EconStateDTO # Needed for reproduction viability checks
    config: HouseholdConfigDTO

@dataclass
class NeedsInputDTO:
    bio_state: BioStateDTO
    econ_state: EconStateDTO
    social_state: SocialStateDTO
    config: HouseholdConfigDTO

@dataclass
class SocialInputDTO:
    social_state: SocialStateDTO
    econ_state: EconStateDTO
    all_items: Dict[str, float]
    config: HouseholdConfigDTO

@dataclass
class BudgetInputDTO:
    econ_state: EconStateDTO
    prioritized_needs: List[PrioritizedNeed]
    abstract_plan: List[Order]  # The AI's initial, abstract order intentions
    config: HouseholdConfigDTO

@dataclass
class ConsumptionInputDTO:
    econ_state: EconStateDTO
    budget_plan: BudgetPlan
    market_snapshot: MarketSnapshot
    config: HouseholdConfigDTO


# --- Engine Output DTOs ---

@dataclass
class LifecycleOutputDTO:
    bio_state: BioStateDTO
    cloning_requests: List[CloningRequestDTO]

@dataclass
class NeedsOutputDTO:
    bio_state: BioStateDTO  # Needs decay might affect bio state
    prioritized_needs: List[PrioritizedNeed]

@dataclass
class BudgetOutputDTO:
    econ_state: EconStateDTO # May be updated with savings goals, etc.
    budget_plan: BudgetPlan

@dataclass
class ConsumptionOutputDTO:
    econ_state: EconStateDTO # Updated inventory and balances
    orders: List[Order] # The final, concrete orders to be placed


# === Stateless Engine Interfaces (Protocols) ===

class ILifecycleEngine(Protocol):
    """Manages aging, death, and reproduction."""
    def process_tick(self, input: LifecycleInputDTO) -> LifecycleOutputDTO: ...

class INeedsEngine(Protocol):
    """Calculates need decay, satisfaction, and prioritizes needs."""
    def evaluate_needs(self, input: NeedsInputDTO) -> NeedsOutputDTO: ...

class ISocialEngine(Protocol):
    """Manages social status, discontent, and other social metrics."""
    def update_status(self, input: SocialInputDTO) -> SocialStateDTO: ...

class IBudgetEngine(Protocol):
    """Allocates financial resources based on needs and strategic goals."""
    def allocate_budget(self, input: BudgetInputDTO) -> BudgetOutputDTO: ...

class IConsumptionEngine(Protocol):
    """Transforms a budget plan into concrete consumption and market orders."""
    def generate_orders(self, input: ConsumptionInputDTO) -> ConsumptionOutputDTO: ...

```
