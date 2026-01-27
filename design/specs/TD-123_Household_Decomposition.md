```markdown
# Technical Specification: TD-123 Household Decomposition

## 1. Overview
This specification details the refactoring of the `Household` agent class. The goal is to transition it from a complex "God Class" into a pure **Facade**. All state and business logic will be fully encapsulated within three distinct, stateless components: `BioComponent`, `EconComponent`, and `SocialComponent`.

This refactoring strictly enforces the **Single Responsibility Principle (SRP)** and a **DTO-driven architecture**. Components will no longer hold back-references to the parent `Household` instance. Instead, they will operate on dedicated state DTOs, receiving state as input and returning updated state as output. This eliminates circular dependencies, improves testability, and clarifies data ownership.

## 2. Architectural Changes

### 2.1. Stateless Components & DTO-Driven Design
The core of this refactoring is the removal of the component-to-facade back-reference.

- **Current (Problematic) State:**
  ```python
  # components are initialized with the parent facade
  self.bio_component = BioComponent(self, ...)
  ```
- **New (Target) State:**
  - `Household` will be the single source of truth, holding state in dedicated DTOs:
    ```python
    from modules.household.dtos import BioStateDTO, EconStateDTO, SocialStateDTO

    class Household(BaseAgent):
        def __init__(...):
            self.bio_state: BioStateDTO = BioStateDTO(...)
            self.econ_state: EconStateDTO = EconStateDTO(...)
            self.social_state: SocialStateDTO = SocialStateDTO(...)
            # Components are instantiated without state or back-references
            self.bio_component = BioComponent()
            ...
    ```
  - Component methods will be pure functions that accept a state DTO and context, and return an updated state DTO.
  - **Example Method Signature Change:**
    ```python
    # Old
    # class BioComponent:
    #     def run_lifecycle(self, context: LifecycleContext): ...

    # New
    from modules.household.api import IBioComponent
    class BioComponent(IBioComponent):
        def run_lifecycle(self, state: BioStateDTO, context: LifecycleContext) -> BioStateDTO:
            # Modify a copy of the state
            new_state = state.copy(deep=True)
            new_state.age += context.time_delta
            # Return the new state
            return new_state
    ```
- **Facade Responsibility**: The `Household` facade is responsible for orchestrating calls to the components and managing the state DTOs. It will pass the current state to a component and replace its internal state with the returned, updated version.

### 2.2. Strict Logic & State Encapsulation
All business logic and state attributes currently residing in `Household` or `BaseAgent` must be moved to the appropriate component's state DTO.

- **State Migration:**
  - `aptitude`, `skills` -> `EconStateDTO`
  - `credit_frozen_until_tick` -> `EconStateDTO`
  - `personality` -> `SocialStateDTO`
  - All other properties delegated via `@property` will have their underlying private attributes (`_variable`) moved to the corresponding state DTO.
- **Logic Migration:**
  - The `wage_modifier` update logic (`core_agents.py:L811-L817`) **MUST** be extracted from `Household.make_decision` and moved into a new method within `EconComponent`, such as `update_wage_dynamics`.

### 2.3. Decoupling Cloning with a Factory
To resolve the leaky abstraction where `BioComponent.clone` depends on the AI architecture, a **Factory Pattern** will be used.

1.  An `IDecisionEngineFactory` interface will be defined. The `Simulation` will be responsible for creating a concrete factory and injecting it into the `Household` upon initialization.
2.  The `Household.clone()` method will become the orchestrator.
3.  `BioComponent` will have a method `prepare_clone_state(self, parent_state: BioStateDTO, ...) -> BioStateDTO`, which creates the initial biological state for a new child.
4.  The `Household.clone()` method will:
    a. Call `self.bio_component.prepare_clone_state(...)` to get the child's bio state.
    b. Call `self.econ_component.prepare_clone_state(...)` to get the child's econ state.
    c. Call `self.social_component.prepare_clone_state(...)` to get the child's social state.
    d. Call `self.decision_engine_factory.create_for_clone(parent_engine=self.decision_engine)` to create a new decision engine for the child.
    e. Instantiate and return a new `Household` with the prepared state DTOs and the new engine.

This removes any knowledge of AI or decision engines from the `BioComponent`.

## 3. Detailed Design (`api.py`)
The public contract for this refactoring will be defined in `modules/household/api.py`. It will include DTOs, component interfaces, and factory interfaces.

*(See the accompanying `api.py` file for the full contract definition.)*

### Key DTOs (`modules/household/dtos.py`)
- `BioStateDTO(dataclass)`: Contains all biological/demographic state (`age`, `gender`, `generation`, `spouse_id`, etc.).
- `EconStateDTO(dataclass)`: Contains all economic state (`assets`, `inventory`, `is_employed`, `portfolio`, `aptitude`, `skills`, etc.).
- `SocialStateDTO(dataclass)`: Contains all social/psychological state (`social_status`, `discontent`, `personality`, `optimism`, etc.).
- `HouseholdStateDTO(dataclass)`: A container DTO holding instances of the three sub-DTOs.

### Facade Implementation (`simulation/core_agents.py`)
- The `Household` class will preserve its public API (all methods and properties).
- `@property` getters will read directly from the internal state DTOs (e.g., `return self.bio_state.age`).
- `@property` setters will modify the attribute on the internal state DTOs (e.g., `self.bio_state.age = value`).

## 4. Verification Plan
1.  **Preserve Existing Tests**: All existing unit and integration tests for `Household` **MUST** continue to pass without modification. This validates the integrity of the facade pattern.
2.  **New Component Tests**: New, isolated unit tests **MUST** be created for `BioComponent`, `EconComponent`, and `SocialComponent`.
    - These tests will not use the `Household` class.
    - They will instantiate a component directly.
    - They will create a relevant state DTO (e.g., `BioStateDTO`) using data from `golden_households` fixtures.
    - They will call the component's method with the DTO and assert that the returned DTO contains the expected values.
3.  **Code Quality**: All new and modified code must pass `ruff check .`.

## 5. Mocking & Golden Data Strategy
- **Component Tests**: Leverage existing data fixtures (`tests/conftest.py`) to create realistic input DTOs for component tests. This ensures tests are based on valid simulation scenarios.
- **Example**:
  ```python
  def test_bio_component_aging(golden_households):
      bio_component = BioComponent()
      # Create DTO from fixture data
      start_state = BioStateDTO(age=golden_households[0]['initial_age'], ...)
      context = LifecycleContext(time_delta=1)

      new_state = bio_component.run_lifecycle(start_state, context)

      assert new_state.age == start_state.age + 1
  ```
- **Prohibition**: Do not use `MagicMock` to mock the state DTOs. Construct them directly to enforce type safety.

## 6. Risk & Impact Audit (Resolution)
This design directly addresses the findings of the pre-flight audit:
- **Circular Dependencies**: Resolved by removing the `self` back-reference and introducing a DTO-driven, stateless component model.
- **Single Responsibility Principle**: Resolved by migrating all state and logic to the appropriate components and using a factory for `clone` orchestration.
- **Leaky Abstractions**: Resolved. `BioComponent` is no longer aware of the AI architecture.
- **Fragile State**: Resolved by centralizing state management within the `Household` facade, which owns the single-source-of-truth state DTOs.
- **Technical Debt**: The facade's complexity is acknowledged as a necessary trade-off to maintain backward compatibility. The internal architecture is now clean, and future work can be done at the component level.

---
### 🚨 **Jules' Mandatory Reporting**
During implementation, you are required to log any unforeseen complexities, architectural insights, or new technical debt. Create a new markdown file in `communications/insights/` named `TD123-implementation-notes-YYYYMMDD.md` to document your findings.
```

I will now create the `api.py` file.

```python
from __future__ import annotations
from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass, field

from simulation.models import Order, Skill, Talent
from simulation.ai.api import Personality
from simulation.portfolio import Portfolio
from simulation.dtos import LifecycleContext, DecisionContext, MacroFinancialContext
from simulation.decisions.base_decision_engine import BaseDecisionEngine

# --- Data Transfer Objects (DTOs) for State ---

@dataclass
class BioStateDTO:
    """State related to the biological and demographic aspects of a household."""
    id: int
    age: float
    gender: str
    generation: int
    is_active: bool = True
    parent_id: Optional[int] = None
    spouse_id: Optional[int] = None
    children_ids: List[int] = field(default_factory=list)
    
    # Health/Lifecycle
    health: float = 1.0
    is_newly_born: bool = False
    
@dataclass
class EconStateDTO:
    """State related to the economic aspects of a household."""
    assets: float
    inventory: Dict[str, float]
    
    # Labor & Skills
    is_employed: bool
    employer_id: Optional[int]
    current_wage: float
    wage_modifier: float
    labor_skill: float
    education_xp: float
    education_level: int
    expected_wage: float
    talent: Talent
    skills: Dict[str, Skill]
    aptitude: float # Hidden trait

    # Financial
    portfolio: Portfolio
    durable_assets: List[Dict[str, Any]]
    credit_frozen_until_tick: int
    
    # Housing
    owned_properties: List[int]
    residing_property_id: Optional[int]
    is_homeless: bool
    home_quality_score: float

    # Transient Economic State
    labor_income_this_tick: float = 0.0
    capital_income_this_tick: float = 0.0
    
    # Price Expectations
    expected_inflation: Dict[str, float] = field(default_factory=dict)
    perceived_avg_prices: Dict[str, float] = field(default_factory=dict)
    
@dataclass
class SocialStateDTO:
    """State related to the social and psychological aspects of a household."""
    social_status: float
    social_rank: float
    approval_rating: int
    discontent: float
    conformity: float
    
    # Personality & Preferences
    personality: Personality
    value_orientation: str
    preference_asset: float
    preference_social: float
    preference_growth: float
    risk_aversion: float
    
    # Consumer Behavior
    quality_preference: float
    brand_loyalty: Dict[int, float]

    # Psychology
    optimism: float
    ambition: float
    patience: float

@dataclass
class HouseholdStateDTO:
    """A container for all component states, representing a full Household."""
    id: int
    bio: BioStateDTO
    econ: EconStateDTO
    social: SocialStateDTO

# --- Component Interfaces (Protocols) ---

class IBioComponent(Protocol):
    """Interface for the component managing biological and demographic logic."""
    
    def run_lifecycle(self, state: BioStateDTO, context: LifecycleContext) -> BioStateDTO:
        """Processes aging, health changes, and other life events."""
        ...

    def prepare_clone_state(
        self,
        parent_bio_state: BioStateDTO,
        parent_econ_state: EconStateDTO,
        new_id: int,
        initial_assets: float,
        current_tick: int
    ) -> BioStateDTO:
        """Creates the initial biological state for a new child agent."""
        ...

class IEconComponent(Protocol):
    """Interface for the component managing economic logic."""

    def orchestrate_economic_decisions(
        self, 
        state: EconStateDTO, 
        context: Any, # EconContextDTO
        orders: List[Order], 
        stress_scenario: Optional[Any]
    ) -> List[Order]:
        """Refines and executes economic decisions like investments and housing."""
        ...
        
    def update_perceived_prices(self, state: EconStateDTO, market_data: Dict[str, Any]) -> EconStateDTO:
        """Updates the agent's internal model of market prices."""
        ...
        
    def update_wage_dynamics(self, state: EconStateDTO, config: Any) -> EconStateDTO:
        """Updates wage modifier based on employment status."""
        ...

    def prepare_clone_state(
        self,
        parent_econ_state: EconStateDTO,
        initial_assets: float
    ) -> EconStateDTO:
        """Creates the initial economic state for a new child agent."""
        ...


class ISocialComponent(Protocol):
    """Interface for the component managing social and psychological logic."""

    def calculate_social_status(self, bio_state: BioStateDTO, econ_state: EconStateDTO, social_state: SocialStateDTO) -> SocialStateDTO:
        """Calculates and updates the agent's social status based on wealth, age, etc."""
        ...

    def prepare_clone_state(
        self,
        parent_social_state: SocialStateDTO,
        config: Any
    ) -> SocialStateDTO:
        """Creates the initial social state for a new child agent."""
        ...

# --- Factory Interface ---

class IDecisionEngineFactory(Protocol):
    """Interface for a factory that creates decision engines."""

    def create_for_clone(self, parent_engine: BaseDecisionEngine, new_id: int) -> BaseDecisionEngine:
        """Creates a new decision engine for a cloned (child) agent."""
        ...

```
