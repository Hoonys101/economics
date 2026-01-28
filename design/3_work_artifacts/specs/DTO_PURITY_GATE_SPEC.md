# Work Order: TD-103 - DTO Purity Gate

**Phase:** Refactoring
**Priority:** HIGH
**Prerequisite:** None

## 1. Problem Statement

The current decision-making architecture exhibits a "Leaky Abstraction," where agent instances (`Household`, `Firm`) are directly passed into the `DecisionContext`. This violates the Separation of Concerns (SoC) principle by allowing decision engines to access and potentially modify an agent's internal state and methods directly. This tight coupling creates a high risk of side effects, complicates testing, and hinders future development, such as parallelization. The legacy `RuleBasedHouseholdDecisionEngine` is explicitly dependent on this anti-pattern.

## 2. Objective

Implement a "DTO Purity Gate" to enforce a strict, one-way data flow for all decision-making processes. All decision engines—both legacy and AI-driven—must operate as pure functions that receive state via Data Transfer Objects (DTOs) and return a list of proposed actions (`Orders`).

**Key Goals:**
1.  Eliminate all direct agent instance references from `DecisionContext`.
2.  Refactor legacy engines to be stateless and rely solely on DTOs.
3.  Implement a verification mechanism (Purity Gate) to prevent future violations.
4.  Ensure all necessary data for decision-making is provided through extended DTOs.

## 3. Proposed Architecture Changes

### 3.1. `DecisionContext` Refactoring

The `DecisionContext` DTO will be modified to enforce the purity principle.

**Current (Problematic) Definition:**
```python
@dataclass
class DecisionContext:
    # ...
    household: Optional[Household] = None # Direct instance access
    firm: Optional[Firm] = None          # Direct instance access
    state: Optional[HouseholdStateDTO] = None
    # ...
```

**New Definition:**
```python
# New DTOs to be created in simulation/dtos/api.py
@dataclass
class HouseholdConfigDTO:
    """Static configuration values relevant to household decisions."""
    low_asset_threshold: float
    low_asset_wage: float
    default_wage: float
    # Add other config values needed by engines...
    # TBD: Team Leader to review full config list

@dataclass
class FirmConfigDTO:
    """Static configuration values relevant to firm decisions."""
    # TBD

@dataclass
class DecisionContext:
    # --- Agent State (MUST be a DTO) ---
    state: Union[HouseholdStateDTO, FirmStateDTO] # Type-hinted union of state DTOs

    # --- Static Configuration (NEW) ---
    config: Union[HouseholdConfigDTO, FirmConfigDTO] # Relevant config values

    # --- Environmental Context ---
    markets: Dict[str, Any]
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    government: Optional[Any] = None
    stress_scenario_config: Optional[StressScenarioConfig] = None
    # ... other context fields
```
**Rationale**: By removing `household` and `firm` and adding a mandatory `state` DTO and a new `config` DTO, we make it architecturally impossible for engines to access the agent instance.

### 3.2. Purity Gate Verification

A simple, robust assertion will be added to the `BaseDecisionEngine` to act as the Purity Gate.

**Location:** `simulation/decisions/base_decision_engine.py`

```python
from abc import ABC, abstractmethod

class BaseDecisionEngine(ABC):

    def make_decisions(self, context: DecisionContext, macro_context: Optional[MacroFinancialContext] = None):
        # 🚨 DTO PURITY GATE 🚨
        assert not hasattr(context, 'household'), "Purity Violation: Direct household access is forbidden."
        assert not hasattr(context, 'firm'), "Purity Violation: Direct firm access is forbidden."
        assert hasattr(context, 'state'), "Purity Error: context.state DTO is missing."
        assert hasattr(context, 'config'), "Purity Error: context.config DTO is missing."

        return self._make_decisions_internal(context, macro_context)

    @abstractmethod
    def _make_decisions_internal(self, context: DecisionContext, macro_context: Optional[MacroFinancialContext]):
        ...
```
This gate will immediately fail any execution that attempts to use the old, impure context structure.

## 4. Implementation Plan

### Track A: DTO and Context Refactoring

1.  **Modify `simulation/dtos/api.py`:**
    *   Define `HouseholdConfigDTO` and `FirmConfigDTO`.
    *   Modify `DecisionContext` as specified in section 3.1. Remove the `household` and `firm` fields and add the `config` field. Make the `state` field mandatory and non-optional.
2.  **Modify `simulation/core_agents.py` (`Household.make_decision`):**
    *   Update the context creation logic.
    *   Instantiate `HouseholdConfigDTO` with values from `self.config_module`.
    *   Pass `state=state_dto` and `config=config_dto` to the `DecisionContext`.

    **Example (`Household.make_decision`):**
    ```python
    # Before
    # context = DecisionContext(household=self, ...)
    # context.state = state_dto

    # After
    state_dto = self.create_state_dto()
    config_dto = HouseholdConfigDTO(
        low_asset_threshold=self.config_module.HOUSEHOLD_LOW_ASSET_THRESHOLD,
        low_asset_wage=self.config_module.HOUSEHOLD_LOW_ASSET_WAGE,
        default_wage=self.config_module.HOUSEHOLD_DEFAULT_WAGE
    )
    context = DecisionContext(
        state=state_dto,
        config=config_dto,
        markets=markets,
        # ... other fields
    )
    ```
3.  **Implement Purity Gate:**
    *   Add the assertion logic to `BaseDecisionEngine` as described in section 3.2.

### Track B: Legacy Engine Refactoring (`RuleBasedHouseholdDecisionEngine`)

This engine must be refactored to extra logic from `Household` methods and use only the provided DTOs.

1.  **Identify Agent Method Calls:** Audit the engine to find all calls like `context.household.some_method()`.
2.  **Migrate Logic:** Move the logic from the agent method into a private helper method within the engine itself.
3.  **Update Call Sites:** Replace the old call with a call to the new helper, passing data from `context.state` and `context.config`.

**Example: Refactoring `get_desired_wage` logic**

*   **Legacy Call (in Engine):**
    ```python
    desired_wage = context.household.get_desired_wage()
    ```
*   **Agent Method (in `Household`):**
    ```python
    def get_desired_wage(self) -> float:
        if self.assets < self.config_module.HOUSEHOLD_LOW_ASSET_THRESHOLD:
            return self.config_module.HOUSEHOLD_LOW_ASSET_WAGE
        return self.config_module.HOUSEHOLD_DEFAULT_WAGE
    ```
*   **Refactored (in `RuleBasedHouseholdDecisionEngine`):**
    ```python
    class RuleBasedHouseholdDecisionEngine(BaseDecisionEngine):
        def _make_decisions_internal(self, context: DecisionContext, ...):
            # ...
            desired_wage = self._calculate_desired_wage(context.state, context.config)
            # ...

        def _calculate_desired_wage(self, state: HouseholdStateDTO, config: HouseholdConfigDTO) -> float:
            """Calculates desired wage based on pure data, moved from Household agent."""
            if state.assets < config.low_asset_threshold:
                return config.low_asset_wage
            return config.default_wage
    ```

### Track C: DTO Field Audit & Expansion

1.  **Audit `Household.get_agent_data()`:** The `get_agent_data` method is used for the AI engine's state representation. Every field in this dictionary *must* be present in `HouseholdStateDTO` to ensure parity between AI and Rule-based engines.
2.  **Cross-reference:** Compare the fields in `HouseholdStateDTO` with `get_agent_data` and add any missing fields. The `Pre-flight Audit` confirms this is a critical step.
3.  **Update `create_state_dto`:** Ensure the `Household.create_state_dto` method populates all fields of the newly expanded `HouseholdStateDTO`.

## 5. Interface 명세 (`api.py` 초안)

The following changes and additions will be made to `simulation/dtos/api.py`.

```python
# simulation/dtos/api.py

# ... other imports
from typing import Union, List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from modules.household.dtos import HouseholdStateDTO
    from modules.firm.dtos import FirmStateDTO # Assuming this will be created
# ...

# +++ NEW DTOs +++
@dataclass
class HouseholdConfigDTO:
    """Static configuration values relevant to household decisions."""
    low_asset_threshold: float
    low_asset_wage: float
    default_wage: float
    # TBD: Add other necessary config values after full audit.

@dataclass
class FirmConfigDTO:
    """Static configuration values relevant to firm decisions."""
    # TBD: To be defined when refactoring Firm decision engines.
    pass

# --- MODIFIED DTO ---
@dataclass
class DecisionContext:
    """
    A pure data container for decision-making.
    Direct agent instance access is strictly forbidden (Enforced by Purity Gate).
    """
    # State DTO representing the agent's current condition
    state: Union[HouseholdStateDTO, "FirmStateDTO"]

    # Static configuration values relevant to the agent type
    config: Union[HouseholdConfigDTO, FirmConfigDTO]

    # Environmental market and simulation data
    markets: Dict[str, Any]
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    government: Optional[Any] = None
    stress_scenario_config: Optional["StressScenarioConfig"] = None
    reflux_system: Optional[Any] = None

    # --- DEPRECATED FIELDS (To be removed) ---
    # household: Optional["Household"] = None
    # firm: Optional["Firm"] = None

```

## 6. 검증 계획 (Verification Plan)

1.  **Unit Test Overhaul:** All existing unit tests for decision engines (`RuleBased...`, `AIDriven...`) will fail due to the `DecisionContext` change. These tests must be rewritten to construct and pass `HouseholdStateDTO` and `HouseholdConfigDTO` instead of mocked agent instances.
2.  **Purity Gate Test:** A new test will be created to explicitly check the Purity Gate. It will attempt to initialize a `DecisionContext` with a `household` attribute and assert that `make_decisions` raises an `AssertionError`.
3.  **Integration Test:** The main simulation loop must run successfully for at least 100 ticks with the refactored components to ensure no regressions in behavior.

## 7. 🚨 Risk & Impact Audit (기술적 위험 분석)

-   **테스트 영향도 (High):** This change constitutes a fundamental shift in the decision-making contract. A significant portion of tests related to agent decisions will require a complete rewrite.
-   **순환 참조 위험 (Resolved):** This refactoring will successfully eliminate the circular dependency risk between `core_agents.py` and `dtos/api.py`.
-   **설정 의존성 (Addressed):** The introduction of `HouseholdConfigDTO` explicitly exposes and manages the hidden dependency on `config_module` values, mitigating risks from undiscovered configuration dependencies.
-   **선행 작업 권고:** A full audit of `RuleBasedHouseholdDecisionEngine`'s usage of `context.household` is the most critical prerequisite. Any missed method call will block the refactoring.

---

### [Routine] Mandatory Reporting

**Jules's Implementation Notes:**
- During implementation, you are required to log any newly discovered implicit dependencies or necessary DTO field additions.
- Report any logical discrepancies found while translating agent methods into stateless functions.
- All findings must be documented in a new file under `communications/insights/TD-103_Purity_Gate_Implementation_Log.md`.
- Any new technical debt incurred must be logged in `design/TECH_DEBT_LEDGER.md` with the tag `TD-103-Follow-up`.
