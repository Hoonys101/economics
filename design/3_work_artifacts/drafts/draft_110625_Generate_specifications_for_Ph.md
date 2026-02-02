# spec_td065_housing_planner.md

# TD-065 & HousingRefactor: Centralized Housing Planner

- **Mission**: Liquidate `HousingRefactor` & `TD-065` technical debt.
- **Objective**: Centralize all housing market decision logic into a new, stateless `HousingPlanner` component. This planner will be called by the `DecisionUnit` to ensure that housing transactions correctly integrate with the mortgage system, fixing the "Orphaned Logic" critical bug.

---

## 1. API Definition (`modules/market/housing_planner_api.py`)

### DTOs

```python
from typing import TypedDict, List, Optional, Literal
from modules.household.dtos import HouseholdStateDTO
from modules.housing.dtos import HousingMarketSnapshotDTO, PropertyDTO

class HousingOfferRequestDTO(TypedDict):
    """
    Input for the HousingPlanner, containing all necessary state for a decision.
    """
    household_state: HouseholdStateDTO
    housing_market_snapshot: HousingMarketSnapshotDTO
    # TBD: Add LoanMarketSnapshot if needed for pre-qualification checks

class LoanApplicationDTO(TypedDict):
    """
    Represents a formal loan application to be sent to the LoanMarket.
    """
    applicant_id: int
    principal: float
    purpose: str # e.g., "MORTGAGE"
    property_id: int
    offer_price: float

class HousingDecisionDTO(TypedDict):
    """
    Output of the HousingPlanner, detailing the agent's next action.
    """
    decision_type: Literal["MAKE_OFFER", "RENT", "STAY", "DO_NOTHING"]
    target_property_id: Optional[int]
    offer_price: Optional[float]
    loan_application: Optional[LoanApplicationDTO]
```

### Interface

```python
from abc import ABC, abstractmethod
from .dtos import HousingOfferRequestDTO, HousingDecisionDTO

class IHousingPlanner(ABC):
    """
    Stateless interface for making housing decisions.
    """

    @abstractmethod
    def evaluate_housing_options(self, request: HousingOfferRequestDTO) -> HousingDecisionDTO:
        """

        Analyzes the housing market and the agent's financial state to recommend
        a housing action (buy, rent, or stay).

        Args:
            request: A DTO containing the agent's state and a market snapshot.

        Returns:
            A DTO representing the chosen action, which may include a loan application.
        """
        ...
```

---

## 2. Logic Specification (Pseudo-code)

The `HousingPlanner.evaluate_housing_options` method will execute the following logic:

```pseudocode
FUNCTION evaluate_housing_options(request: HousingOfferRequestDTO):
    // 1. Unpack DTOs
    household = request.household_state
    market = request.housing_market_snapshot

    // 2. Assess Current Situation
    IF household.is_homeless OR current_rent_is_unaffordable:
        urgency = HIGH
    ELSE:
        urgency = LOW

    // 3. Evaluate "Buy" Option
    affordable_properties = []
    FOR property IN market.properties_for_sale:
        // Use a simple affordability metric (e.g., price <= assets * max_leverage_ratio)
        max_loan = calculate_max_loan(household)
        IF property.price <= household.assets + max_loan:
            // More complex scoring can be added later (quality, location, etc.)
            property.score = calculate_buy_score(property, household)
            affordable_properties.append(property)

    // 4. Evaluate "Rent" Option
    affordable_rentals = []
    FOR rental IN market.properties_for_rent:
        IF rental.rent <= household.expected_income * max_rent_to_income_ratio:
             rental.score = calculate_rent_score(rental, household)
             affordable_rentals.append(rental)

    // 5. Compare and Decide
    best_buy_option = get_best(affordable_properties)
    best_rent_option = get_best(affordable_rentals)

    IF best_buy_option AND (best_buy_option.score > best_rent_option.score OR household.housing_target_mode == "BUY"):
        // DECISION: BUY
        offer_price = determine_offer_price(best_buy_option, household)
        down_payment = min(household.assets, offer_price * down_payment_pct)
        loan_amount = offer_price - down_payment

        loan_app = CREATE LoanApplicationDTO(
            applicant_id=household.id,
            principal=loan_amount,
            purpose="MORTGAGE",
            property_id=best_buy_option.id,
            offer_price=offer_price
        )

        RETURN HousingDecisionDTO(
            decision_type="MAKE_OFFER",
            target_property_id=best_buy_option.id,
            offer_price=offer_price,
            loan_application=loan_app
        )

    ELSE IF best_rent_option:
        // DECISION: RENT (Logic for making a rental offer)
        RETURN HousingDecisionDTO(decision_type="RENT", ...)

    ELSE:
        // DECISION: DO NOTHING
        RETURN HousingDecisionDTO(decision_type="DO_NOTHING")
```

---

## 3. Integration Plan

1.  **`HousingPlanner` Implementation**: A new class `HousingPlanner` will be created in `modules/market/` that implements `IHousingPlanner`.
2.  **`DecisionUnit` Modification**: The `modules.household.decision_unit.DecisionUnit`'s `orchestrate_economic_decisions` method will be modified.
    - It will be responsible for constructing the `HousingOfferRequestDTO`.
    - It will invoke `housing_planner.evaluate_housing_options()`.
    - Based on the returned `HousingDecisionDTO`, it will generate the final `Order` for the housing market and, if present, an `Order` for the loan market encapsulating the `LoanApplicationDTO`. This directly links the housing decision to the loan system.

---

## 4. Verification Plan

A new verification script, `scripts/verify_housing_transaction_integrity.py`, will be created to ensure the "Orphaned Logic" is fixed.

-   **Goal**: Prove that a `Household` agent's decision to buy a house correctly results in a `Mortgage` being created and property ownership being transferred.
-   **Methodology**:
    1.  Initialize a simulation with a small number of households and properties for sale.
    2.  Run the simulation for a fixed number of ticks (e.g., 50).
    3.  During the run, monitor the `LoanMarket` for new `Loan` objects with `purpose == "MORTGAGE"`.
    4.  After the run, query the simulation state.
-   **Success Criteria (Assertions)**:
    1.  **ASSERT `Mortgage Count > 0`**: At least one mortgage must have been created.
    2.  **ASSERT `Ownership Transfer`**: For each created mortgage, verify the `Household`'s `owned_properties` list contains the `property_id` and their `residing_property_id` is updated.
    3.  **ASSERT `Debt Incurred`**: The household's assets should reflect the down payment, and they should have a corresponding liability in the `LoanMarket`.
    4.  **ASSERT `Homeless Rate Reduction`**: The number of homeless agents should not increase and ideally should decrease.

---

## 5. Risk & Impact Audit

-   **Risk**: Transactional Failure. The primary risk is not in the planner's logic itself, but in the chain of events it triggers. A failure in the `Order` creation, `LoanMarket` processing, or `Registry` state update will cause the bug to persist. The verification script is designed to mitigate this by testing the full, end-to-end transaction.
-   **Test Impact**: Existing tests for `Household.make_decision` may need to be updated to account for the new DTO-based flow. Tests that mock housing decisions will need to be adapted to mock the `HousingPlanner`'s output instead.
-   **Dependencies**: This refactor depends on a functional `LoanMarket`. Any bugs in the loan approval or processing logic will block this work.
-   **Configuration**: `SimulationConfig` may need new parameters to tune the planner's behavior (e.g., `max_leverage_ratio`, `max_rent_to_income_ratio`).

# TD-162_Household_Refactor_Spec.md

# TD-162: Household God Class Decomposition (Stage B)

- **Mission**: Liquidate `TD-162` technical debt.
- **Objective**: Complete the decomposition of the `Household` agent by executing **Stage B**: the removal of all property delegates. This will enforce architectural separation by forcing all other modules to interact with the `Household`'s state via its constituent components (`bio`, `econ`, `social`) and their respective state DTOs.

---

## 1. Refactoring Plan: Stage B - Property Delegate Removal

This is a high-impact, "stop-the-world" refactoring. The process must be systematic to manage the widespread, cascading changes.

### Step 1: Full-Scale Call Site Analysis
- **Action**: Use `ripgrep` to find every usage of a `Household` property delegate across the entire project.
- **Command**: `rg "household\.(assets|age|is_employed|personality|...)"` (with the full list of properties from `core_agents.py`).
- **Output**: A comprehensive file (`refactor_call_sites.log`) listing every file and line number that needs modification. This log will serve as our checklist.

### Step 2: Phased Property Group Removal & Code Modification
The removal will be done in three phases, grouped by component. For each phase:
1.  Remove the `@property` definitions from `simulation/core_agents.py`.
2.  Work through the `refactor_call_sites.log` to fix all resulting `AttributeError` exceptions.

**Phase 2A: EconComponent Properties**
- **Properties to Remove**: `assets`, `inventory`, `is_employed`, `employer_id`, `current_wage`, `labor_skill`, `portfolio`, `owned_properties`, `is_homeless`, etc.
- **Replacement Pattern**:
  - `household.assets` -> `household._econ_state.assets`
  - `household.is_employed` -> `household._econ_state.is_employed`
  - `if household.is_homeless:` -> `if household._econ_state.is_homeless:`

**Phase 2B: BioComponent Properties**
- **Properties to Remove**: `age`, `gender`, `parent_id`, `generation`, `is_active`, `needs`, etc.
- **Replacement Pattern**:
  - `household.age` -> `household._bio_state.age`
  - `household.needs` -> `household._bio_state.needs`

**Phase 2C: SocialComponent Properties**
- **Properties to Remove**: `personality`, `social_status`, `discontent`, `conformity`, `optimism`, `ambition`, etc.
- **Replacement Pattern**:
  - `household.personality` -> `household._social_state.personality`
  - `household.social_status` -> `household._social_state.social_status`

*Note: After this refactor, a follow-up task should be considered to make the component state DTOs (`_bio_state`, etc.) public (`bio_state`).*

### Step 3: Script-Assisted Refactoring (Optional but Recommended)
- **Action**: Create a Python script (`scripts/refactor_household_access.py`) that uses file I/O and string replacement to automate the most common substitutions.
- **Example**:
  ```python
  # scripts/refactor_household_access.py
  replacements = {
      "household.assets": "household._econ_state.assets",
      "household.age": "household._bio_state.age",
      # ... and so on
  }
  # ... logic to iterate files and perform replacement ...
  ```
- **Caution**: This script must be used with care and changes reviewed via `git diff` before committing.

---

## 2. API Definition Changes

-   **File**: `simulation/core_agents.py`
-   **Change**: This work does not create a new API, but **destroys an existing implicit one**. All `@property` methods delegating to `_bio_state`, `_econ_state`, and `_social_state` will be **deleted**.
-   **New Contract**: Any external module needing to access `Household` state **MUST** do so through the component state DTOs. For example: `household._econ_state.assets`. The `Household` class itself will no longer expose these fields directly.

---

## 3. Verification Plan

This refactor will cause massive, predictable test failures. The verification plan is focused on managing this fallout efficiently.

-   **New Script**: `scripts/verify_household_decomposition.py`.
-   **Methodology**:
    1.  The script will first run `pytest --collect-only -q`. This is a fast way to catch all `AttributeError` and `SyntaxError` issues at the module level without running any test logic.
    2.  Once collection passes, the script will execute the full `pytest` suite.
    3.  A log of all failing tests (`test_failures_household_refactor.log`) will be generated.
-   **Triage Strategy**:
    1.  **Fix Core Systems First**: Prioritize fixing test failures in core infrastructure, systems, and markets (`tests/simulation/`, `tests/systems/`, `tests/markets/`).
    2.  **Tackle Mock-Related Failures**: A significant number of failures will be due to `unittest.mock.patch` targeting the now-deleted properties (e.g., `@patch('...Household.assets', new_callable=PropertyMock)`). These must be updated to patch the DTO attributes instead (e.g., `@patch.object(EconStateDTO, 'assets', ...)`), or preferably, refactored to use golden data fixtures.
    3.  **Fix Agent-Level Tests**: Finally, fix the higher-level agent decision-making tests.

---

## 4. Risk & Impact Audit

-   **Primary Risk (CRITICAL)**: **Widespread Codebase Breakage**. This is the intended outcome, but the scale requires a meticulous, checklist-driven approach (`refactor_call_sites.log`) to ensure all call sites are updated. Any missed site is a guaranteed runtime bug.
-   **Test Impact (EXTREME)**: A significant percentage (estimated 40-60%) of the test suite will fail. The primary challenge is not the complexity of the fix (most are simple substitutions), but the sheer volume. The risk is that a subtle bug is introduced while fixing a failing test.
-   **Precedent**: This operation is a direct successor to the `Firm` refactor (TD-073). The lessons learned there (e.g., the need for systematic call site analysis, the pain of mock-heavy tests) are directly applicable here.
-   **Recommendation**: This refactoring should be performed on a dedicated branch and should be the only major change in its associated Pull Request to simplify code review. All other feature development should be paused until this debt is liquidated.
