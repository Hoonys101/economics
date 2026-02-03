# Specification: `AdaptiveGovBrain` - Utility-Driven Government AI

## 1. Overview

This document specifies the design for the `AdaptiveGovBrain`, a utility-driven decision engine that replaces the current government policy logic. It will be implemented as a new `IGovernmentPolicy` strategy, plugging into the existing `Government` agent (`simulation/agents/government.py:L104`).

The core principle is that the government agent, under a specific ruling party, makes decisions by selecting actions that maximize a party-specific utility function. This introduces more realistic, goal-oriented political behavior and allows for emergent phenomena like scapegoating and policy cycles.

This design directly addresses the findings of the **Pre-flight Audit**, ensuring a safe and testable integration within the existing "God Class" architecture.

---

## 2. Core Components & Data Flow

### 2.1. `AdaptiveGovBrain` (The Engine)
- **Location**: `modules/government/policies/adaptive_gov_brain.py`
- **Purpose**: Implements the `IGovernmentPolicy` interface. Its primary method, `decide()`, orchestrates the perception-evaluation-action loop. It is stateless and relies entirely on the input DTO provided by the `Government` agent each tick.

### 2.2. `PolicyLockoutManager` (The Constraint System)
- **Location**: `modules/government/components/policy_lockout_manager.py`
- **Purpose**: A new stateful component, owned by the `Government` agent. It tracks which policy "schools" (e.g., `KEYNESIAN`, `AUSTERITY`) are locked and for how long. The `AdaptiveGovBrain` uses this information to filter its possible actions.

### 2.3. Data Flow
The process is initiated by the main simulation loop calling `Government.make_policy_decision()`.

```
[Simulation Engine]
      |
      v
[1. Government Agent] -- (Gathers state: Gini, Approval, GDP) --> [2. AdaptiveGovBrainInputDTO]
      |                                                                     |
      | <---- [5. PolicyDecisionDTO (e.g., 'FIRE_ADVISOR')] -----------------|
      |                                                                     |
      v                                                                     v
[6. Execute Action] -> [7. PolicyLockoutManager.activate_lockout()]    [3. AdaptiveGovBrain.decide()] -- (Softmax) --> [4. Action Selected]
```

---

## 3. DTO & Interface Modifications

To address the "Missing Data Pipelines" risk, the following DTOs and interfaces are required. They will be defined in `modules/government/api.py`.

### 3.1. `PolicyAction` Enum (New)
Defines the discrete set of actions the brain can choose from. Each action is tagged with a policy school.

```python
class PolicySchool(Enum):
    KEYNESIAN = "KEYNESIAN"
    AUSTERITY = "AUSTERITY"
    MONETARIST = "MONETARIST"
    SUPPLY_SIDE = "SUPPLY_SIDE"
    GOVERNANCE = "GOVERNANCE" # For actions like firing advisors

class PolicyAction(Enum):
    # Fiscal Actions
    INCREASE_INCOME_TAX = ("INCREASE_INCOME_TAX", PolicySchool.AUSTERITY)
    DECREASE_INCOME_TAX = ("DECREASE_INCOME_TAX", PolicySchool.KEYNESIAN)
    INCREASE_CORPORATE_TAX = ("INCREASE_CORPORATE_TAX", PolicySchool.AUSTERITY)
    DECREASE_CORPORATE_TAX = ("DECREASE_CORPORATE_TAX", PolicySchool.SUPPLY_SIDE)
    INCREASE_WELFARE = ("INCREASE_WELFARE", PolicySchool.KEYNESIAN)
    DECREASE_WELFARE = ("DECREASE_WELFARE", PolicySchool.AUSTERITY)

    # Governance Actions
    FIRE_KEYNESIAN_ADVISOR = ("FIRE_KEYNESIAN_ADVISOR", PolicySchool.GOVERNANCE)
    FIRE_AUSTERITY_ADVISOR = ("FIRE_AUSTERITY_ADVISOR", PolicySchool.GOVERNANCE)

    # No-Op
    DO_NOTHING = ("DO_NOTHING", None)
```

### 3.2. `AdaptiveGovBrainInputDTO` (New)
A dedicated DTO to feed the brain, decoupling it from the monolithic `GovernmentStateDTO`.

```python
@dataclass
class AdaptiveGovBrainInputDTO:
    tick: int
    ruling_party: PoliticalParty
    # Utility Metrics
    gini_coefficient: float
    gdp_growth_rate: float
    approval_rating_low_asset: float
    approval_rating_high_asset: float
    # Action Space
    locked_action_schools: List[PolicySchool]
```

### 3.3. `PolicyDecisionDTO` (New)
The output of the brain's decision process.

```python
@dataclass
class PolicyDecisionDTO:
    action_taken: PolicyAction
    utility_scores: Dict[PolicyAction, float] # For analysis
    status: str # "EXECUTED" | "NO_OP"
```

---

## 4. The Decision-Making Process (Pseudo-code)

The `AdaptiveGovBrain.decide()` method will follow these steps:

```python
def decide(self, inputs: AdaptiveGovBrainInputDTO) -> PolicyDecisionDTO:
    # 1. Perceive State (Input DTO is the state)
    
    # 2. Filter available actions based on lockout
    available_actions = [
        action for action in PolicyAction
        if action.school not in inputs.locked_action_schools
    ]

    # 3. Evaluate Utility for each action
    utility_scores = {}
    for action in available_actions:
        # 3a. Project the outcome of the action (heuristic-based)
        # This is the most complex part. It estimates the delta on key metrics.
        # Example for one action:
        # if action == PolicyAction.DECREASE_INCOME_TAX:
        #    projected_gdp_growth = +0.001
        #    projected_gini_change = +0.02 # More inequality
        #    projected_approval_low_asset = +0.01
        #    projected_approval_high_asset = +0.03
        
        projected_state = self.project_outcome(action, inputs)

        # 3b. Add special rewards (e.g., Trust Reset for firing advisor)
        special_reward = self.get_special_reward(action)

        # 3c. Calculate final utility based on party
        utility = self.calculate_utility(
            inputs.ruling_party, 
            projected_state
        ) + special_reward
        
        utility_scores[action] = utility

    # 4. Softmax Selection
    # T (temperature) is a configurable parameter from simulation.yaml
    # T -> 0: becomes deterministic (picks max utility)
    # T -> inf: becomes uniform random
    temperature = self.config.GOV_AI_TEMPERATURE
    
    probabilities = softmax(list(utility_scores.values()), temperature)
    
    chosen_action = choose_randomly(
        actions=list(utility_scores.keys()),
        probabilities=probabilities
    )

    return PolicyDecisionDTO(
        action_taken=chosen_action, 
        utility_scores=utility_scores,
        status="EXECUTED"
    )

def calculate_utility(self, party, state):
    if party == PoliticalParty.RED:
        return (0.7 * state.approval_low_asset_change) + \
               (0.3 * state.gini_improvement) - state.penalty
    
    if party == PoliticalParty.BLUE:
        return (0.6 * state.approval_high_asset_change) + \
               (0.4 * state.gdp_growth) - state.penalty
```

---

## 5. Key Actions & Mechanics

### `fire_advisor(advisor_school: PolicySchool)` Action

This is a strategic action with a trade-off.

- **Mechanism**: The brain selects an action like `FIRE_KEYNESIAN_ADVISOR`. The `Government` agent receives this `PolicyDecisionDTO` and executes the logic.
- **Immediate Reward (Utility Bonus)**: To incentivize this as a valid "escape hatch" during crises, the `project_outcome` or `get_special_reward` function will associate a large, fixed utility bonus with this action (e.g., `TRUST_RESET_BONUS = 0.5`). This represents the immediate (but temporary) boost in public approval from "taking action."
- **Penalty (Lockout)**: Upon executing this action, the `Government` agent immediately calls `self.policy_lockout_manager.activate_lockout(fired_school, duration=20)`. This prevents the brain from selecting any actions associated with that school for the specified duration.

---

## 6. Implementation & Integration Plan

1.  **New DTOs**: Add `PolicyAction`, `AdaptiveGovBrainInputDTO`, and `PolicyDecisionDTO` to `modules/government/api.py` or a new `modules/government/dtos/ai_dtos.py`.
2.  **New Component (`PolicyLockoutManager`)**: Create `modules/government/components/policy_lockout_manager.py`. The `Government` agent will instantiate it in its `__init__`. Its `step()` method must be called every tick to manage cooldowns.
3.  **New Brain (`AdaptiveGovBrain`)**: Create `modules/government/policies/adaptive_gov_brain.py`. It will implement `IGovernmentPolicy`.
4.  **Modify `Government` Agent**:
    - Instantiate `PolicyLockoutManager`.
    - In `make_policy_decision()`, create the `AdaptiveGovBrainInputDTO` by:
        - **Modifying `update_public_opinion`**: It must now iterate through households, check their asset levels against a threshold (e.g., median wealth), and calculate two separate average approval ratings (`low_asset`, `high_asset`).
        - **Adding a Gini Coefficient source**: The simulation engine must be updated to calculate the Gini coefficient for all households each tick and pass it down into the `Government` agent's `sensory_data`.
        - Getting `locked_action_schools` from its `policy_lockout_manager` instance.
    - Update the `policy_engine` instantiation logic in `__init__` to select `AdaptiveGovBrain` based on the config.
    - Add logic to execute the `action_taken` from the `PolicyDecisionDTO`, including calling the lockout manager.

---

## 7. Verification & Test Plan

This plan explicitly addresses the risk of non-determinism.

1.  **Unit Tests (`PolicyLockoutManager`)**:
    - Test that `activate_lockout` correctly adds a school to the locked set.
    - Test that after `step()` is called `duration` times, the school is no longer locked.

2.  **Unit Tests (`AdaptiveGovBrain`)**:
    - **Utility Functions**: Test `calculate_utility` for RED and BLUE parties with fixed projected states to ensure the math is correct.
    - **Projection Heuristics**: Test the `project_outcome` function for each `PolicyAction` to ensure it returns sane, directionally correct estimates.
    - **Softmax Selection (Controlled)**:
        - Use `@patch('random.choices')` or set a fixed `random.seed()` at the start of the test.
        - **Test 1 (Low Temp)**: Set temperature to `0.01`. Verify that the action with the highest calculated utility is always chosen.
        - **Test 2 (High Temp)**: Set temperature to `1000`. Verify that the action distribution is nearly uniform.

3.  **Integration Tests (`Government` + `AdaptiveGovBrain`)**:
    - **Scenario: The Scapegoat**: Create a fixture where the economy is poor and approval ratings are plummeting for 10 straight ticks. With a fixed seed, assert that the probability of `FIRE...ADVISOR` being chosen becomes > 50%.
    - **Scenario: Policy Lockout**: In a test, manually call the `fire_advisor` logic. Then, for the next 19 ticks, assert that the brain *never* chooses an action from the locked school, even if it has the highest utility.

---

## 8. Risk & Impact Audit (Mitigation)

This design incorporates mitigations for all risks identified in the pre-flight check.

- **Constraint: The `Government` God Class**
  - **Mitigation**: This design fully embraces the constraint. The `AdaptiveGovBrain` is a stateless policy engine that plugs into the existing `policy_engine` slot. The `Government` agent remains the sole owner of state (including the new `PolicyLockoutManager`), feeding the brain a clean DTO.

- **Risk: Missing Data Pipelines for Utility Function**
  - **Mitigation**: Section 3 (`DTO & Interface Modifications`) and Section 6 (`Implementation & Integration Plan`) explicitly define the creation of `AdaptiveGovBrainInputDTO` and detail the necessary modifications to `Government.update_public_opinion` and the engine's data feed to provide differentiated approval ratings and the Gini coefficient.

- **Constraint: Creation of New Components**
  - **Mitigation**: The spec provides a clear plan for the creation of `PolicyLockoutManager` as a new component owned by the `Government` agent and defines the `fire_advisor` action as a choice within a `PolicyAction` enum, to be executed by the `Government` agent.

- **Risk: Non-Deterministic Behavior and Testability**
  - **Mitigation**: Section 7 (`Verification & Test Plan`) provides a comprehensive strategy to manage non-determinism. It includes using fixed random seeds, testing at extreme temperatures to force deterministic or random behavior, and using `@patch` to test selection logic independently of randomness. This ensures tests are repeatable and reliable.

---
# API Definition: `modules.government.api`

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

# ===================================================================
# DTOs & Enums for Adaptive Government AI
# ===================================================================

class PoliticalParty(Enum):
    """Defines the political parties for the government agent."""
    RED = "RED"    # Progressive
    BLUE = "BLUE"  # Conservative

class PolicySchool(Enum):
    """Defines ideological schools of thought for policy actions."""
    KEYNESIAN = "KEYNESIAN"
    AUSTERITY = "AUSTERITY"
    MONETARIST = "MONETARIST"
    SUPPLY_SIDE = "SUPPLY_SIDE"
    GOVERNANCE = "GOVERNANCE"
    NONE = "NONE"

@dataclass(frozen=True)
class PolicyAction:
    """Represents a discrete policy action the government can take."""
    name: str
    school: PolicySchool

# --- Pre-defined Policy Actions ---
# This could be a separate constants file, but is here for clarity.
class GovernmentActions:
    INCREASE_INCOME_TAX = PolicyAction("INCREASE_INCOME_TAX", PolicySchool.AUSTERITY)
    DECREASE_INCOME_TAX = PolicyAction("DECREASE_INCOME_TAX", PolicySchool.KEYNESIAN)
    INCREASE_CORPORATE_TAX = PolicyAction("INCREASE_CORPORATE_TAX", PolicySchool.AUSTERITY)
    DECREASE_CORPORATE_TAX = PolicyAction("DECREASE_CORPORATE_TAX", PolicySchool.SUPPLY_SIDE)
    INCREASE_WELFARE = PolicyAction("INCREASE_WELFARE", PolicySchool.KEYNESIAN)
    DECREASE_WELFARE = PolicyAction("DECREASE_WELFARE", PolicySchool.AUSTERITY)
    FIRE_KEYNESIAN_ADVISOR = PolicyAction("FIRE_KEYNESIAN_ADVISOR", PolicySchool.GOVERNANCE)
    FIRE_AUSTERITY_ADVISOR = PolicyAction("FIRE_AUSTERITY_ADVISOR", PolicySchool.GOVERNANCE)
    DO_NOTHING = PolicyAction("DO_NOTHING", PolicySchool.NONE)
    
    @classmethod
    def all(cls) -> List[PolicyAction]:
        return [
            cls.INCREASE_INCOME_TAX, cls.DECREASE_INCOME_TAX,
            cls.INCREASE_CORPORATE_TAX, cls.DECREASE_CORPORATE_TAX,
            cls.INCREASE_WELFARE, cls.DECREASE_WELFARE,
            cls.FIRE_KEYNESIAN_ADVISOR, cls.FIRE_AUSTERITY_ADVISOR,
            cls.DO_NOTHING
        ]

@dataclass
class AdaptiveGovBrainInputDTO:
    """
    Input data bundle for the AdaptiveGovBrain, provided by the Government agent.
    """
    tick: int
    ruling_party: PoliticalParty
    # Core metrics for utility calculation
    gini_coefficient: float
    gdp_growth_rate: float
    approval_rating_low_asset: float
    approval_rating_high_asset: float
    # Constraint for action filtering
    locked_action_schools: List[PolicySchool]

@dataclass
class PolicyDecisionDTO:
    """
    Output from the AdaptiveGovBrain's decision process.
    """
    action_taken: PolicyAction
    utility_scores: Dict[str, float]  # Keyed by action name for serialization
    status: str  # e.g., "EXECUTED", "NO_OP", "ERROR"
    reason: Optional[str] = None


# ===================================================================
# Component Interfaces
# ===================================================================

class IPolicyLockoutManager(ABC):
    """
    Manages the cooldown period for policy schools after a major event,
    like firing an advisor.
    """
    @abstractmethod
    def step(self) -> None:
        """Advance time by one tick, decrementing all active lockout timers."""
        ...

    @abstractmethod
    def activate_lockout(self, school: PolicySchool, duration: int) -> None:
        """
        Start a new lockout for a specific policy school.
        If a lockout for that school is already active, it will be overridden.
        """
        ...

    @abstractmethod
    def get_locked_schools(self) -> List[PolicySchool]:
        """Return a list of all currently locked policy schools."""
        ...


class IAdaptiveGovBrain(ABC):
    """
    Interface for the utility-driven government decision engine.
    This will be implemented as an IGovernmentPolicy.
    """
    @abstractmethod
    def decide(self, inputs: AdaptiveGovBrainInputDTO) -> PolicyDecisionDTO:
        """
        The core decision loop: perceives state via DTO, filters actions,
        evaluates utility, and selects an action via Softmax.
        """
        ...
```
