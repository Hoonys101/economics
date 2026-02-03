# W-4 Specification: `PolicyLockoutManager`

**Module**: `modules.government.components.policy_lockout_manager`
**Status**: 🟢 Ready for Implementation
**Author**: Scribe (Gemini)
**Addresses**: `[AUTO-AUDIT FINDINGS] Pre-flight Audit: PolicyLockoutManager Integration`

---

## 1. Introduction

This document specifies the design of the `PolicyLockoutManager`, a critical component for simulating political opportunity cost and accountability within the `Government` agent. When an advisor from a specific `EconomicSchool` is fired, this manager enforces a "cool-down" period, preventing the government from using policies associated with that school.

This design explicitly addresses the architectural risks identified in the pre-flight audit by introducing a formal `PolicyActionDTO` and refactoring the government's decision-making process into a "Propose-Filter-Execute" cycle.

---

## 2. Core Components & Data Structures

### 2.1. `PolicyActionDTO` (Data Transfer Object)

This DTO is the new, fundamental unit of government action. It decouples the *intent* of a policy from its *execution*.

-   **Structure**:
    -   `action_id: str`: A unique identifier for the action (e.g., `ADJUST_CORPORATE_TAX`, `INCREASE_WELFARE_SPENDING`).
    -   `tags: List[PolicyActionTag]`: A list of enum tags describing the action's ideological alignment (e.g., `KEYNESIAN_FISCAL`, `AUSTRIAN_AUSTERITY`).
    -   `parameters: Dict[str, Any]`: The specific details of the action (e.g., `{'new_rate': 0.25}`, `{'multiplier': 1.2}`).
    -   `utility_score: float` (Optional): The policy engine's calculated utility for this action, used for selection.
    -   `description: str` (Optional): A human-readable description.

-   **Example**:

    ```python
    PolicyActionDTO(
        action_id="INCREASE_INFRASTRUCTURE_INVESTMENT",
        tags=[PolicyActionTag.KEYNESIAN_FISCAL],
        parameters={"investment_amount": 50000.0},
        utility_score=0.85,
        description="Inject 50k into infrastructure to boost demand."
    )
    ```

### 2.2. `PolicyLockoutManager`

This component tracks which policy types are "locked" and for how long.

-   **Internal State**:
    -   `_school_to_tags_map: Dict[EconomicSchool, List[PolicyActionTag]]`: A static map linking economic schools to their associated policy tags.
    -   `_locked_until: Dict[PolicyActionTag, int]`: A dictionary where keys are locked tags and values are the tick number until which the lockout is active.

-   **Logic**:
    -   `fire_advisor(school: EconomicSchool, current_tick: int, duration: int = 20)`:
        1.  Looks up the tags associated with the given `school` from `_school_to_tags_map`.
        2.  For each tag, it updates `_locked_until[tag] = current_tick + duration`.
    -   `is_action_allowed(action: PolicyActionDTO, current_tick: int) -> bool`:
        1.  Iterates through the `action.tags`.
        2.  For each `tag`, it checks if `tag` is in `_locked_until`.
        3.  If it is, it checks if `current_tick < _locked_until[tag]`.
        4.  If the condition in (3) is true for *any* tag, the action is locked, and the method returns `False`.
        5.  If all tags are cleared, it returns `True`.

---

## 3. Architectural Refactoring: The "Propose-Filter-Execute" Cycle

To integrate the `PolicyLockoutManager` without exacerbating the God Class anti-pattern, the government's decision-making loop (`make_policy_decision`) will be fundamentally changed.

**Old (Brittle) Flow:**
`Government` -> `policy_engine.decide()` -> `policy_engine` directly mutates `Government` state.

**New (Robust) Flow:**

1.  **Phase 1: Propose**
    -   The `Government` agent gets the list of currently locked tags from `lockout_manager.get_active_locks()`.
    -   It calls the policy engine: `proposed_actions = policy_engine.propose_actions(state, locked_tags)`.
    -   The `IGovernmentPolicy` interface is **refactored**. Instead of one `decide()` method, it now has a `propose_actions()` method that returns a `List[PolicyActionDTO]`. The engine is now a pure "proposer," not a mutator.

2.  **Phase 2: Filter**
    -   The `Government` agent receives the list of `PolicyActionDTO`s.
    -   It filters this list: `allowed_actions = [action for action in proposed_actions if lockout_manager.is_action_allowed(action, current_tick)]`.

3.  **Phase 3: Select & Execute**
    -   From the `allowed_actions`, the `Government` selects the best one (e.g., based on the highest `utility_score`).
    -   The `Government` agent **itself** executes the action by reading the `action_id` and `parameters` from the chosen DTO and calling its own internal methods. This preserves the `Government` as the single source of truth for state changes.

### `government.py:make_policy_decision` (Pseudo-code)

```python
# In Government.make_policy_decision:

# 1. PROPOSE
# The policy engine is now a pure function that returns proposals.
proposed_actions: List[PolicyActionDTO] = self.policy_engine.propose_actions(
    government_state=self.sensory_data,
    current_tick=current_tick,
    # Pass locked tags to prevent engine from wasting cycles on invalid options
    locked_tags=self.lockout_manager.get_active_locks(current_tick)
)

# 2. FILTER
# The government, as the owner of the rule, filters the proposals.
allowed_actions = [
    action for action in proposed_actions
    if self.lockout_manager.is_action_allowed(action, current_tick)
]

if not allowed_actions:
    logger.info("No policy actions are allowed this tick due to lockouts.")
    return

# 3. SELECT & EXECUTE
# The government retains control over state mutation.
best_action = max(allowed_actions, key=lambda a: a.utility_score)

# The government executes the action based on the DTO contract.
self.executor.execute_action(best_action) # Using a hypothetical executor component

# --- Example Executor Logic ---
# def execute_action(self, action: PolicyActionDTO):
#     if action.action_id == "ADJUST_CORPORATE_TAX":
#         self.corporate_tax_rate = action.parameters['new_rate']
#         logger.info(f"Executed tax change to {self.corporate_tax_rate}")
#     elif action.action_id == "INCREASE_WELFARE_SPENDING":
#         self.welfare_manager.budget_multiplier = action.parameters['multiplier']
#         logger.info(f"Executed welfare multiplier change to {self.welfare_manager.budget_multiplier}")
#     # ... and so on
```

---

## 4. API Definition (`api.py`)

The following interfaces and DTOs will be created in `modules/government/api.py`.

```python
from typing import List, Dict, Any, Protocol
from enum import Enum

# These enums are assumed to exist in simulation.ai.enums
class EconomicSchool(Enum): ...
class PolicyActionTag(Enum): ...

# 1. The new core data contract for all government actions
class PolicyActionDTO:
    action_id: str
    tags: List[PolicyActionTag]
    parameters: Dict[str, Any]
    utility_score: float
    description: str

# 2. The interface for the new manager
class IPolicyLockoutManager(Protocol):
    def fire_advisor(self, school: EconomicSchool, current_tick: int, duration: int) -> None:
        """Locks all policy tags associated with a given economic school."""
        ...

    def is_action_allowed(self, action: PolicyActionDTO, current_tick: int) -> bool:
        """Returns False if any of the action's tags are currently locked."""
        ...

    def get_active_locks(self, current_tick: int) -> Dict[PolicyActionTag, int]:
        """Returns a dict of currently locked tags and their expiry tick."""
        ...

# 3. The refactored interface for ALL policy engines (e.g., SmartLeviathanPolicy)
class IGovernmentPolicy(Protocol):
    def propose_actions(
        self,
        government_state: Any, # Should be a specific GovernmentStateDTO
        current_tick: int,
        locked_tags: List[PolicyActionTag]
    ) -> List[PolicyActionDTO]:
        """
        Proposes a list of possible actions with their expected utilities,
        respecting the currently locked-out policy tags.
        """
        ...
```

---

## 5. Verification & Test Plan

1.  **Unit Tests for `PolicyLockoutManager`**:
    -   Test `fire_advisor` correctly sets lockout end-ticks for the correct tags (e.g., `KEYNESIAN` -> `KEYNESIAN_FISCAL`).
    -   Test `is_action_allowed` returns `False` for a locked action before the expiry tick.
    -   Test `is_action_allowed` returns `True` for a locked action at and after the expiry tick.
    -   Test `is_action_allowed` returns `True` for an action whose tags are not locked.

2.  **Integration Tests for `Government`**:
    -   Create a test scenario where an advisor is fired.
    -   Verify that in the subsequent ticks, the `Government` agent does *not* execute actions with the locked tags, even if the policy engine proposes them with high utility.
    -   Verify that after 20 ticks, the `Government` agent *can* once again execute those actions.

3.  **Refactoring `IGovernmentPolicy` Tests**:
    -   All tests for `SmartLeviathanPolicy` and `TaylorRulePolicy` must be updated.
    -   Instead of checking for side effects (state changes in a mock government), tests will now inspect the `List[PolicyActionDTO]` returned by `propose_actions` to ensure the logic is sound.

---

## 6. Risk & Impact Mitigation

This design directly mitigates the risks identified by the pre-flight audit:

-   **God Class / SRP**: By introducing `PolicyActionDTO` and the Propose-Filter-Execute cycle, the `policy_engine` is demoted from a state mutator to a pure "proposer." This clarifies responsibilities:
    -   `Policy Engine`: Proposes what *could* be done.
    -   `PolicyLockoutManager`: Filters what is *allowed* to be done.
    -   `Government`: *Executes* the final decision and manages state.

-   **Circular Imports**: The dependency cycle is broken. The `Government` owns the `PolicyLockoutManager` and passes a simple `List[PolicyActionTag]` into the `propose_actions` method. The policy engine has no knowledge of the manager itself, only of the locked tags.

-   **Testability**: While existing tests will break, the new architecture is significantly more testable. `PolicyLockoutManager` can be tested in isolation. The `policy_engine` can be tested as a pure function (given state -> returns proposals). The `Government`'s execution logic can be tested by feeding it `PolicyActionDTO`s directly.
