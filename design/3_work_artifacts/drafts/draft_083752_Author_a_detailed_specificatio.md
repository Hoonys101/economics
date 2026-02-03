# Specification: PoliticalComponent

**Module**: `modules.household.political_component`  
**Author**: Gemini (Scribe)
**Status**: Draft
**Related Spec**: `design/3_work_artifacts/specs/fiscal_policy_spec.md`

---

## 1. Overview

This document specifies the design for the `PoliticalComponent`, a stateless component responsible for managing a `Household` agent's political identity and opinions. It replaces the simplistic logic currently in `SocialComponent` with a more nuanced model based on ideology, trust, and economic satisfaction, as outlined in the "Leviathan" specification.

This component will be instantiated and owned by the `Household` facade, operating exclusively on state DTOs passed into its methods.

## 2. Architectural Changes & Integration

To adhere to the Single Responsibility Principle (SRP) and the findings of the pre-flight audit, the following changes are mandated:

1.  **Component Ownership**: `PoliticalComponent` will become the sole owner of all household political logic.
2.  **Facade Refactoring**: The `Household.update_needs` method in `simulation/core_agents.py` must be refactored. The call to `self.social_component.update_political_opinion(...)` will be **removed** and replaced with a call to the new component: `self.political_component.update_opinion(...)`.
3.  **Component Deprecation**: The `update_political_opinion` method within `modules/household/social_component.py` must be **deleted**.
4.  **State Initialization**: A new method, `political_component.initialize_state(...)`, will be called once during `Household.__init__` to set the initial political values (`economic_vision`, `trust_score`).

## 3. Data Model (DTOs)

### 3.1. `SocialStateDTO` Extension

To avoid creating a new state DTO and minimize architectural disruption, the existing `modules.household.dtos.SocialStateDTO` will be extended with the following fields:

```python
# In modules/household/dtos.py

class SocialStateDTO(TypedDict):
    # ... existing fields
    economic_vision: float  # 0.0: Safety/Equity -> 1.0: Growth/Opportunity
    trust_score: float      # 0.0 -> 1.0: Trust in the governing system
```

### 3.2. `PoliticalContextDTO`

A new DTO is required to pass external information into the component. This decouples the component from direct access to global state.

```python
# To be created in modules/household/dtos.py

class GovernmentIdeologyDTO(TypedDict):
    """Represents the political stance of the current government."""
    ruling_party: PoliticalParty # e.g., PoliticalParty.BLUE
    economic_stance: float      # 0.0 (Collectivist) to 1.0 (Individualist)

class PoliticalContextDTO(TypedDict):
    """Context required for a household to form a political opinion."""
    government: GovernmentIdeologyDTO
    gdp_growth_rate: float
    unemployment_rate: float
    inflation_rate: float # For specific goods if possible, else general
```

## 4. Component Interface (`api.py`)

The public interface for the component, to be defined in `modules/household/api.py`.

```python
# In modules/household/api.py

from typing import Protocol, Tuple
from .dtos import SocialStateDTO, PoliticalContextDTO
from simulation.ai.api import Personality

class IPoliticalComponent(Protocol):
    """
    Manages the political identity and opinions of a Household.
    This component is stateless and operates on DTOs.
    """

    def initialize_state(
        self,
        personality: Personality
    ) -> Tuple[float, float]:
        """
        Generates the initial political state based on personality.
        
        Returns:
            A tuple of (economic_vision, trust_score).
        """
        ...

    def update_opinion(
        self,
        social_state: SocialStateDTO,
        econ_state: "EconStateDTO", # Forward ref if needed
        context: PoliticalContextDTO
    ) -> SocialStateDTO:
        """

        Calculates and updates the household's political approval and trust.
        Implements the "Paradox of Support" and "Trust Collapse" mechanics.
        
        Returns:
            An updated copy of the SocialStateDTO.
        """
        ...
```

## 5. Detailed Logic (Pseudo-code)

### 5.1. `initialize_state`

This method sets the foundational, slow-changing political alignment of the household.

```pseudocode
FUNCTION initialize_state(personality):
    // 1. Map Personality to a base vision range
    IF personality is MISER or CONSERVATIVE:
        base_vision = random_float_between(0.1, 0.4) // Prefers safety, stability
    ELSE IF personality is STATUS_SEEKER or IMPULSIVE:
        base_vision = random_float_between(0.5, 0.8) // Ambivalent, follows trends
    ELSE IF personality is GROWTH_ORIENTED:
        base_vision = random_float_between(0.7, 0.95) // Prefers opportunity, growth
    ELSE:
        base_vision = random_float_between(0.4, 0.6) // Balanced default

    // 2. Add noise for diversity
    vision_noise = random_float_between(-0.1, 0.1)
    economic_vision = clamp(base_vision + vision_noise, 0.0, 1.0)

    // 3. Initialize trust score to a neutral-to-positive default
    initial_trust = 0.65

    RETURN (economic_vision, initial_trust)
END FUNCTION
```

### 5.2. `update_opinion`

This method is called each tick to update dynamic political feelings.

```pseudocode
FUNCTION update_opinion(social_state, econ_state, context):
    new_state = social_state.copy()

    // 1. Calculate Economic Satisfaction (0.0 to 1.0)
    // A household's perception of their financial well-being.
    // This is a placeholder; a more robust calculation may be needed.
    asset_growth = (econ_state.assets_this_tick / econ_state.assets_last_tick) - 1.0
    real_income_growth = (econ_state.wage / (1 + context.inflation_rate)) - econ_state.wage_last_tick
    
    // Normalize satisfaction: >1% growth is good, <-2% is bad.
    satisfaction_score = normalize_value(real_income_growth, -0.02, 0.01)
    economic_satisfaction = clamp(satisfaction_score, 0.0, 1.0)
    
    // 2. Calculate Ideological Distance
    gov_stance = context.government.economic_stance
    ideological_distance = abs(new_state.economic_vision - gov_stance)

    // 3. Calculate Base Approval Rating
    // Formula from fiscal_policy_spec.md
    base_approval = (0.4 * economic_satisfaction) + (0.6 * (1.0 - ideological_distance))
    
    // 4. Apply Trust Damper (Critical Mechanic)
    IF new_state.trust_score < 0.2:
        final_approval = 0.0  // Trust Collapse
    ELSE:
        final_approval = base_approval
    
    // Convert float approval to binary for now, matching old system
    new_state.approval_rating = 1 IF final_approval > 0.5 ELSE 0
    new_state.discontent = 1.0 - final_approval // Update discontent as the inverse

    // 5. Update Trust Score (Feedback Loop)
    // Trust slowly erodes with dissatisfaction, and slowly builds with satisfaction.
    IF economic_satisfaction < 0.3:
        new_state.trust_score -= 0.02 // Trust decays
    ELSE IF economic_satisfaction > 0.7:
        new_state.trust_score += 0.01 // Trust rebuilds slowly
    
    new_state.trust_score = clamp(new_state.trust_score, 0.0, 1.0)

    RETURN new_state
END FUNCTION
```

## 6. Verification Plan

### 6.1. Test Invalidation
**CRITICAL**: All existing unit and integration tests asserting `approval_rating` or `discontent` based on the old `survival_need` logic in `SocialComponent` are now **invalid**. They must be removed or rewritten as part of the implementation task.

### 6.2. New Test Cases

The following scenarios must be covered by new unit tests for `PoliticalComponent`:

1.  **Vision Initialization**:
    -   Assert that a `GROWTH_ORIENTED` personality consistently produces an `economic_vision` > 0.6.
    -   Assert that a `MISER` personality consistently produces an `economic_vision` < 0.5.
2.  **Paradox of Support**:
    -   **Scenario**: A household with low assets (`economic_satisfaction` = 0.1) but high growth vision (`economic_vision` = 0.9).
    -   **Condition**: The government is BLUE (`economic_stance` = 0.8).
    -   **Assertion**: The household's `approval_rating` should be 1 (approves), demonstrating ideological alignment over immediate economic dissatisfaction.
3.  **Trust Collapse**:
    -   **Scenario**: A household that is ideologically aligned and economically satisfied.
    -   **Condition**: The household's `trust_score` is set to 0.19.
    -   **Assertion**: The final `approval_rating` must be 0, regardless of other factors.
4.  **Trust Dynamics**:
    -   Assert that `trust_score` decreases over several ticks when `economic_satisfaction` is consistently low.
    -   Assert that `trust_score` increases over several ticks when `economic_satisfaction` is consistently high.

## 7. Risk & Impact Audit

This specification directly addresses the risks identified in the pre-flight audit:

-   **SRP Violation**: Addressed by formally designating `PoliticalComponent` as the logic owner and specifying the refactoring path in `Household`.
-   **Missing DTO Fields**: Addressed by extending `SocialStateDTO` rather than creating a new, more disruptive DTO.
-   **Unresolved Dependencies**: Addressed by defining `PoliticalContextDTO` to explicitly pass required external data, ensuring the component remains decoupled.
-   **Guaranteed Test Failures**: Explicitly acknowledged in the Verification Plan, with a clear directive to rewrite invalid tests.

### Additional Impact:

-   **State Assemblers**: Utilities like `HouseholdSnapshotAssembler` and any methods that create state snapshots (`create_snapshot_dto`, `get_agent_data`) must be updated to include the new `economic_vision` and `trust_score` fields. This is a necessary and anticipated part of the implementation work.
