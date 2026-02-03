# Plan: Operation Leviathan Phase 4 - Verification and Decoupling

**Objective**: This document outlines the technical plan to refactor and verify the "Operation Leviathan" module, addressing critical architectural risks identified in the pre-flight audit. The focus is on decoupling components, ensuring financial integrity, and establishing robust testing scenarios.

---

## 1. Decoupling Strategy: Household & Government

To break the "God Class" dependency, we will introduce a formal API layer between `Household` and `Government`, enforcing a strict separation of concerns.

### 1.1. New DTOs for Political Communication

The following Data Transfer Objects will be created in a new file `modules/household/dtos/political.py`.

```python
# modules/household/dtos/political.py

from typing import TypedDict, Optional

class PoliticalProfileDTO(TypedDict):
    """
    Represents the internal political state of a household, used for decision-making.
    """
    economic_vision: float  # 0.0 (Collectivist) to 1.0 (Individualist)
    trust_score: float      # 0.0 (No Trust) to 1.0 (Full Trust)

class PoliticalOpinionDTO(TypedDict):
    """
    The public-facing political opinion of a household, safe to be consumed by external modules like Government.
    """
    agent_id: int
    # Consolidated approval rating (0.0 to 1.0), abstracting the internal calculation.
    approval_rating: float
    # The agent's ideological leaning, derived from their economic_vision.
    ideological_leaning: float
```

### 1.2. Household Public API (`modules/household/api.py`)

The `Household` agent will expose its political stance through a new public interface.

```python
# modules/household/api.py (additions)

from abc import ABC, abstractmethod
from .dtos.political import PoliticalOpinionDTO

# ... other DTOs and interfaces

class IPoliticalActor(ABC):
    """An interface for any agent with a political opinion."""

    @abstractmethod
    def get_political_opinion(self) -> PoliticalOpinionDTO:
        """
        Returns the agent's current political opinion in a standardized format.
        This is the SOLE entry point for the Government to gauge public sentiment.
        """
        ...
```

### 1.3. Responsibility Realignment

-   **`modules.household.PoliticalComponent` (Owner)**:
    -   **Responsibility**: This component becomes the **sole owner** of all political calculations for a `Household`.
    -   It will manage the `PoliticalProfileDTO` state.
    -   It will contain the logic from `fiscal_policy_spec.md` to calculate `approval_rating` based on economic satisfaction and ideological distance.
    -   **Method**: `calculate_opinion(econ_state: EconStateDTO, social_state: SocialStateDTO) -> PoliticalOpinionDTO`

-   **`simulation.core_agents.Household` (Facade)**:
    -   Implements the `IPoliticalActor` interface.
    -   The `get_political_opinion` method will delegate the call to its `political_component`.
    -   The direct access to `_social_state.approval_rating` will be removed.

-   **`simulation.agents.government.Government` (Consumer)**:
    -   The `update_public_opinion` method will be refactored to iterate over a list of `IPoliticalActor`.
    -   It will call `agent.get_political_opinion()` on each, consuming the returned `PoliticalOpinionDTO`.
    -   This removes all knowledge of `Household`'s internal `_social_state` or `_political_state`.

---

## 2. Architectural Implementation Plan

### 2.1. `PolicyLockoutManager` Implementation

A new component will be created to manage policy cooldowns.

-   **File**: `modules/government/components/policy_lockout_manager.py`
-   **Class**: `PolicyLockoutManager`
-   **State**: `_locked_policies: Dict[str, int]` (Maps policy tags to their unlock tick).
-   **API**:
    -   `lock_policy(tag: str, duration: int, current_tick: int)`: Adds a policy tag to the locked dictionary with its expiry tick.
    -   `is_locked(tag: str, current_tick: int) -> bool`: Checks if a policy is currently locked.
    -   `filter_actions(actions: List[GovernmentActionDTO], current_tick: int) -> List[GovernmentActionDTO]`: Returns a new list containing only the actions whose tags are not locked.

### 2.2. `AdaptiveGovBrain` Action & Settlement

To ensure monetary integrity, the AI's decisions must be translated into accountable transactions.

1.  **Action DTO Definition**:
    -   A new DTO will be defined in `modules/government/dtos.py`:
        ```python
        class AIActionDTO(TypedDict):
            action_type: Literal["FIRE_ADVISOR", "FISCAL_STIMULUS", "AUSTERITY", "NO_ACTION"]
            cost: float  # Positive for spending, negative for cuts/savings.
            policy_tag: str  # e.g., "KEYNESIAN_FISCAL"
            justification: str # AI's reasoning for the action.
            target_firm_id: Optional[int] # For targeted bailouts/subsidies
            target_household_criteria: Optional[Dict] # For welfare payments
        ```

2.  **`AdaptiveGovBrain` (`SmartLeviathanPolicy`) Refactoring**:
    -   The `decide` method will first call `policy_lockout_manager.filter_actions()` to get a list of valid moves.
    -   It will then perform its utility calculation on the valid moves.
    -   Its final output **must** be an `AIActionDTO`.

3.  **`Government` Agent Settlement Logic**:
    -   In `make_policy_decision`, the `Government` agent receives the `AIActionDTO` from the policy engine.
    -   It will use a `match/case` block on `action_type`:
        -   **`FIRE_ADVISOR`**: Call `policy_lockout_manager.lock_policy()`.
        -   **`FISCAL_STIMULUS`**:
            -   Check if `self.assets >= action.cost`.
            -   **Crucially**, call `self.settlement_system.transfer()` or an equivalent method in `self.finance_system` to move funds from the government to the target (e.g., all households, specific firms). This creates an auditable transaction.
            -   Log the expenditure.
        -   **`AUSTERITY`**: Update internal budget multipliers.
    -   This flow guarantees that no AI action can bypass the simulation's core financial settlement layer.

---

## 3. Verification Scenarios

### 3.1. The Scapegoat Test

-   **Objective**: Verify that the government correctly fires an advisor in response to a crisis and that the `PolicyLockoutManager` enforces the subsequent policy cooldown.
-   **Setup**:
    1.  Configure a simulation scenario where a significant portion of households have their income drastically reduced for several ticks, or a major firm fails.
    2.  Set the `Government`'s ruling party to have a specific advisor (e.g., Keynesian).
-   **Execution Steps**:
    1.  Run the simulation.
    2.  Monitor the `PoliticalOpinionDTO.approval_rating` from the affected households.
-   **Verification Criteria**:
    1.  **Log Check**: Observe a log message from the `Government` agent: `CRISIS_ACTION: Firing advisor [AdvisorName]. Trust reset triggered.` when average approval drops below the threshold (e.g., 0.2).
    2.  **State Check**: Immediately after the firing, inspect the `Government.policy_lockout_manager._locked_policies` dictionary. It must contain the tag associated with the fired advisor (e.g., `{'KEYNESIAN_FISCAL': <current_tick + 20>}`).
    3.  **Action Check**: For the next 20 ticks, verify that the `AdaptiveGovBrain`'s log of considered actions does not include actions with the locked tag.

### 3.2. The Paradox Support Test

-   **Objective**: Verify that the political alignment logic is working correctly, specifically that poor households with a "growth" mindset will support the conservative (BLUE) party.
-   **Setup**:
    1.  Create a testing fixture or starting scenario with a cohort of `Household` agents having:
        -   `initial_assets` below the simulation average.
        -   `personality` set to `Personality.GROWTH_ORIENTED`. This will translate to a high `economic_vision` score in the `PoliticalComponent`.
-   **Execution Steps**:
    1.  Run the simulation for a sufficient number of ticks for political opinions to stabilize.
    2.  Pause the simulation.
-   **Verification Criteria**:
    1.  **Data Query**: For each agent in the test cohort, call `get_political_opinion()`.
    2.  **Calculation**: Manually calculate the agent's expected approval for both RED and BLUE parties using the formula from the spec.
        -   `Approval_BLUE = (0.4 * Econ_Satisfaction) + (0.6 * (1.0 - |Ideological_Distance_To_BLUE|))`
        -   `Approval_RED = (0.4 * Econ_Satisfaction) + (0.6 * (1.0 - |Ideological_Distance_To_RED|))`
    3.  **Assertion**: Assert that `Approval_BLUE` is significantly higher than `Approval_RED` for these agents, demonstrating the ideological preference outweighs their immediate low economic satisfaction.

### 3.3. The Political Business Cycle Test

-   **Objective**: Observe and verify that the advisor-firing-and-lockout mechanism creates emergent cycles in fiscal policy.
-   **Setup**:
    1.  Run a long simulation (1000+ ticks) with periodic economic shocks enabled to create crises.
-   **Execution Steps**:
    1.  Let the simulation run to completion.
-   **Verification Criteria**:
    1.  **Data Analysis**: Plot the following time-series data from the simulation results:
        -   Government spending (e.g., stimulus, welfare).
        -   The active ruling party's `policy_tag` (e.g., KEYNESIAN vs AUSTERITY).
        -   The timing of "Advisor Fired" events.
    2.  **Pattern Recognition**: The plot should visually confirm a recurring pattern:
        -   An economic downturn occurs.
        -   A specific policy (e.g., Keynesian stimulus) is used heavily.
        -   The policy fails to avert the crisis, and approval drops.
        -   The Keynesian advisor is fired, and the `KEYNESIAN_FISCAL` tag is locked.
        -   The government is forced to switch to the only available policies (e.g., Austerity), even if suboptimal, until the lockout expires.
        -   This forced switch in policy, driven by political constraints rather than pure economic optimization, is the Political Business Cycle we aim to verify.
