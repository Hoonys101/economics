# TD-162: Household Agent Decomposition Specification

## 1. Overview
This document outlines the refactoring plan to complete the decomposition of the `Household` agent (`core_agents.py`) into a pure Facade. The primary goal is to move all state initialization and behavioral logic into their respective stateless domain components: `BioComponent`, `EconComponent`, and `SocialComponent`.

This plan directly addresses the "God Class" and "SRP Violation" risks identified in the `TD-162` pre-flight audit by drastically simplifying the `Household.__init__` method and clarifying the responsibilities between the Facade and its components.

## 2. Architectural Principles & Constraints
- **Facade-Component Pattern**: `Household` will act solely as a state container and orchestrator (Facade). All logic will reside in stateless components.
- **API Preservation**: The existing public property-based API of the `Household` class will be maintained as an anti-corruption layer to ensure backward compatibility with existing tests and modules.
- **Purity & Immutability**: Components will receive state DTOs and return new, modified state DTOs. They will not mutate state directly.

## 3. Proposed Refactoring

### 3.1 `Household` (Facade) Refactoring
The `Household` class will be simplified as follows:
- **`__init__` Method**: The constructor will no longer contain complex setup logic. It will delegate the creation of the initial state DTOs to each respective component using a new `InitialHouseholdParamsDTO` to pass the required parameters.
- **State Management**: It will continue to hold the `_bio_state`, `_econ_state`, and `_social_state` DTOs.
- **Method Delegation**: All public methods (`make_decision`, `update_needs`, `clone`, etc.) will be pure orchestrators, passing the relevant state DTOs to the components and updating their internal state with the returned DTOs.

### 3.2 New DTO: `InitialHouseholdParamsDTO`
To simplify the `Household` constructor and component interfaces, a new DTO will be introduced to encapsulate all initial parameters.

```python
# In modules/household/dtos.py
from typing import TypedDict, List, Dict, Any, Optional
from simulation.ai.api import Personality
from simulation.models import Talent
from simulation.dtos.config_dtos import HouseholdConfigDTO

class InitialHouseholdParamsDTO(TypedDict):
    id: int
    talent: Talent
    goods_data: List[Dict[str, Any]]
    initial_assets: float
    initial_needs: Dict[str, float]
    value_orientation: str
    personality: Personality
    config_dto: HouseholdConfigDTO
    risk_aversion: float
    initial_age: Optional[float]
    gender: Optional[str]
    parent_id: Optional[int]
    generation: Optional[int]
    initial_assets_record: Optional[float]
```

### 3.3 Component Interface Definitions
Each component will be responsible for creating its own initial state from the shared parameter DTO.

#### `BioComponent`
- `create_initial_state(params: InitialHouseholdParamsDTO) -> BioStateDTO`: Creates the initial biological and demographic state.
- (Existing methods remain): `age_one_tick`, `create_offspring_demographics`.

#### `EconComponent`
- `create_initial_state(params: InitialHouseholdParamsDTO) -> EconStateDTO`: Creates the initial economic state, including assets, inventory, skills, and price perceptions. This absorbs the majority of the logic from the current `Household.__init__`.
- (Existing methods remain): `update_wage_dynamics`, `orchestrate_economic_decisions`, `decide_and_consume`, `work`, `update_perceived_prices`, etc.

#### `SocialComponent`
- `create_initial_state(params: InitialHouseholdParamsDTO) -> SocialStateDTO`: Creates the initial social state, including personality-derived attributes like conformity, quality preference, and desire weights.
- (Existing methods remain): `calculate_social_status`, `update_psychology`, `update_political_opinion`, `apply_leisure_effect`.

## 4. Implementation Plan (Pseudo-code)

**1. Define `InitialHouseholdParamsDTO` in `modules/household/dtos.py`** as specified above.

**2. Implement `create_initial_state` in each component:**

   - **`modules/household/bio_component.py`:**
     ```python
     def create_initial_state(self, params: InitialHouseholdParamsDTO) -> BioStateDTO:
         return BioStateDTO(
             id=params['id'],
             age=params['initial_age'] if params['initial_age'] is not None else random.uniform(20.0, 60.0),
             gender=params['gender'] if params['gender'] is not None else random.choice(["M", "F"]),
             generation=params['generation'] if params['generation'] is not None else 0,
             is_active=True,
             needs=params['initial_needs'].copy(),
             parent_id=params['parent_id']
         )
     ```

   - **`modules/household/econ_component.py`:**
     ```python
     def create_initial_state(self, params: InitialHouseholdParamsDTO) -> EconStateDTO:
         # ... extensive logic moved from Household.__init__ ...
         # (e.g., price_memory_len, perceived_prices, adaptation_rate, aptitude setup)
         return EconStateDTO(
             assets=params['initial_assets'],
             # ... all other fields initialized based on params and config ...
         )
     ```
   
   - **`modules/household/social_component.py`:**
     ```python
     def create_initial_state(self, params: InitialHouseholdParamsDTO) -> SocialStateDTO:
         # ... logic for conformity, quality_preference, desire_weights moved from Household.__init__ ...
         return SocialStateDTO(
             personality=params['personality'],
             # ... all other fields initialized based on params and config ...
         )
     ```

**3. Refactor `Household.__init__` in `core_agents.py`:**

   ```python
   # In simulation/core_agents.py
   from modules.household.dtos import InitialHouseholdParamsDTO

   class Household(BaseAgent, ILearningAgent):
       def __init__(
           self,
           # ... all previous parameters ...
       ) -> None:
           # 1. Bundle parameters into the new DTO
           params = InitialHouseholdParamsDTO(
               id=id, talent=talent, goods_data=goods_data, initial_assets=initial_assets,
               initial_needs=initial_needs, value_orientation=value_orientation,
               personality=personality, config_dto=config_dto, risk_aversion=risk_aversion,
               initial_age=initial_age, gender=gender, parent_id=parent_id,
               generation=generation, initial_assets_record=initial_assets_record
           )

           # Initialize Logger and Components (as before)
           self.logger = ...
           self.bio_component = BioComponent()
           self.econ_component = EconComponent()
           self.social_component = SocialComponent()

           # 2. Delegate state creation to components
           self._bio_state = self.bio_component.create_initial_state(params)
           self._econ_state = self.econ_component.create_initial_state(params)
           self._social_state = self.social_component.create_initial_state(params)
           
           # ... (Value orientation prefs can be set here or moved to a component)
           
           # 3. Call super().__init__ and other final setup
           super().__init__(...)
           
           self.logger.debug(f"Household {self.id} initialized (Decomposed).")
   ```

**4. Refactor `clone` method:**
The `clone` method will also be simplified. Instead of manually setting properties, it will construct a new `InitialHouseholdParamsDTO` for the offspring and initialize the new `Household` instance through the refactored constructor.


## 5. Risk Mitigation & Verification Plan

### Risk Mitigation
- **God Class Facade**: This refactoring moves the most complex logic (`__init__`) out of the facade, significantly reducing its "God Class" nature. The large property API is a deliberate architectural choice (Anti-Corruption Layer) and is maintained as required.
- **Brittle Tests**:
    1.  New, isolated unit tests will be created for each component's `create_initial_state` method.
    2.  Testing stateless components with DTOs is inherently more robust and easier than testing the fully-hydrated `Household` agent.

### Verification Plan
1.  **Component Unit Tests**: Write and pass new tests for each `create_initial_state` method in isolation.
2.  **Existing Test Suite**: Run the full existing test suite. All tests must pass, verifying that the public API and overall behavior of the `Household` agent remain unchanged.
3.  **Simulation Dry Run**: Execute a short simulation run to ensure there are no runtime integration errors.
4.  **Schema Change Audit**: As DTOs are central, `Schema Change Notice` from `spec.md` will be applied: any change will require updating golden data fixtures.

---
# `api.py` for Household Components

```python
# modules/household/api.py

from __future__ import annotations
from typing import Protocol, List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from abc import abstractmethod

# Import the primary state DTOs and the new params DTO
from .dtos import (
    BioStateDTO,
    EconStateDTO,
    SocialStateDTO,
    InitialHouseholdParamsDTO,
    EconContextDTO,
    CloningRequestDTO,
)

from simulation.models import Order
from simulation.dtos import LeisureEffectDTO, ConsumptionResult
from simulation.ai.api import Tactic, Aggressiveness

if TYPE_CHECKING:
    from simulation.dtos.scenario import StressScenarioConfig

# --- Component Interfaces (Protocols) ---

class IBioComponent(Protocol):
    """Interface for biological and demographic logic."""

    @abstractmethod
    def create_initial_state(self, params: InitialHouseholdParamsDTO) -> BioStateDTO:
        """Creates the initial biological and demographic state for a new household."""
        ...

    @abstractmethod
    def age_one_tick(
        self, state: BioStateDTO, config: Any, current_tick: int
    ) -> BioStateDTO:
        """Ages the agent by one tick and checks for natural death."""
        ...

    @abstractmethod
    def create_offspring_demographics(
        self, parent_state: BioStateDTO, new_id: int, current_tick: int, config: Any
    ) -> Dict[str, Any]:
        """Generates the demographic data for a new offspring."""
        ...


class IEconComponent(Protocol):
    """Interface for economic decision-making and state management."""

    @abstractmethod
    def create_initial_state(self, params: InitialHouseholdParamsDTO) -> EconStateDTO:
        """Creates the initial economic state for a new household."""
        ...

    @abstractmethod
    def orchestrate_economic_decisions(
        self,
        state: EconStateDTO,
        context: EconContextDTO,
        orders: List[Order],
        stress_scenario_config: Optional[StressScenarioConfig],
        config: Any,
    ) -> Tuple[EconStateDTO, List[Order]]:
        """Refines and executes economic decisions based on high-level orders."""
        ...

    @abstractmethod
    def decide_and_consume(
        self,
        econ_state: EconStateDTO,
        needs: Dict[str, float],
        current_time: int,
        goods_info_map: Dict[str, Any],
        config: Any,
    ) -> Tuple[EconStateDTO, Dict[str, float], Dict[str, float]]:
        """Performs System 1 consumption from inventory to satisfy needs."""
        ...

    @abstractmethod
    def consume(
        self,
        econ_state: EconStateDTO,
        needs: Dict[str, float],
        item_id: str,
        quantity: float,
        current_time: int,
        goods_info: Dict[str, Any],
        config: Any,
    ) -> Tuple[EconStateDTO, Dict[str, float], ConsumptionResult]:
        """Consumes a specific item and applies its effects."""
        ...

    @abstractmethod
    def update_perceived_prices(
        self,
        state: EconStateDTO,
        market_data: Dict[str, Any],
        goods_info_map: Dict[str, Any],
        stress_scenario_config: Optional[StressScenarioConfig],
        config: Any,
    ) -> EconStateDTO:
        """Updates the agent's perception of average market prices."""
        ...

    @abstractmethod
    def update_wage_dynamics(
        self, state: EconStateDTO, config: Any, is_employed: bool
    ) -> EconStateDTO:
        """Updates reservation wage and job search patience."""
        ...

    @abstractmethod
    def work(
        self, state: EconStateDTO, hours: float, config: Any
    ) -> Tuple[EconStateDTO, float]:
        """Simulates a work cycle, returning updated state and income earned."""
        ...

    @abstractmethod
    def update_skills(self, state: EconStateDTO, config: Any) -> EconStateDTO:
        """Updates agent skills through experience and decay."""
        ...
        
    @abstractmethod
    def prepare_clone_state(
        self, parent_state: EconStateDTO, parent_skills: Dict[str, Any], config: Any
    ) -> Dict[str, Any]:
        """Prepares the economic attributes for a new offspring."""
        ...


class ISocialComponent(Protocol):
    """Interface for social status, psychology, and relationship logic."""

    @abstractmethod
    def create_initial_state(self, params: InitialHouseholdParamsDTO) -> SocialStateDTO:
        """Creates the initial social and psychological state for a new household."""
        ...

    @abstractmethod
    def calculate_social_status(
        self,
        state: SocialStateDTO,
        assets: float,
        inventory: Dict[str, float],
        config: Any,
    ) -> SocialStateDTO:
        """Calculates and updates the agent's social status."""
        ...

    @abstractmethod
    def update_psychology(
        self,
        social_state: SocialStateDTO,
        needs: Dict[str, float],
        assets: float,
        durable_assets: List[Dict[str, Any]],
        goods_info_map: Dict[str, Any],
        config: Any,
        current_tick: int,
        market_data: Optional[Dict[str, Any]],
    ) -> Tuple[SocialStateDTO, Dict[str, float], List[Dict[str, Any]], bool]:
        """Updates needs, discontent, and checks for survival."""
        ...

    @abstractmethod
    def update_political_opinion(
        self, state: SocialStateDTO, survival_need: float
    ) -> SocialStateDTO:
        """Updates the agent's approval rating of the government."""
        ...

    @abstractmethod
    def apply_leisure_effect(
        self,
        social_state: SocialStateDTO,
        labor_skill: float,
        children_count: int,
        leisure_hours: float,
        consumed_items: Dict[str, float],
        config: Any,
    ) -> Tuple[SocialStateDTO, float, LeisureEffectDTO]:
        """Applies the effects of leisure activities on needs and skills."""
        ...

```