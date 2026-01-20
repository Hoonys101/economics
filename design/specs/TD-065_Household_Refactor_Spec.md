# Work Order: TD-065 - Refactoring `Household` God Class

**Phase:** 29 (Refinement)
**Priority:** HIGH
**Prerequisite:** None

## 1. Problem Statement
The `Household` class in `simulation/core_agents.py` has become a "God Class" exceeding 1,000 lines of code (LoC). It violates the Single Responsibility Principle (SRP) by mixing biological/demographic concerns (reproduction, aging), economic logic (consumption, labor), and social behaviors (status-seeking, political opinion). This tight coupling makes the class difficult to maintain, test, and extend, as identified in technical debt item `TD-065`.

## 2. Objective
Decompose the `Household` class into a set of cohesive, modular components organized around the Bio-Econ-Social model. The `Household` class will be refactored into a **Facade**, orchestrating these components while preserving its public API to maintain backward compatibility with existing tests, particularly golden fixtures.

## 3. Target Architecture
The `Household` class will delegate its responsibilities to three primary internal components. Existing sub-components will be re-homed under this new structure.

*   **`Household` (The Facade)**:
    *   Maintains the public API (`.assets`, `.age`, `clone()`, `make_decision()`).
    *   Owns and initializes `BioComponent`, `EconComponent`, `SocialComponent`.
    *   Orchestrates calls between components and the `DecisionEngine`.
*   **`BioComponent` (Biological & Demographic State)**:
    *   Owns: `DemographicsComponent`, `AgentLifecycleComponent`.
    *   Responsibilities: Aging, death, reproduction (`clone`), and inheritance of biological traits.
*   **`EconComponent` (Economic Activity & State)**:
    *   Owns: `ConsumptionBehavior`, `LaborManager`, `EconomyManager`, `MarketComponent`, `Portfolio`.
    *   Responsibilities: Asset/inventory management, consumption, labor decisions, housing decisions, market interactions.
*   **`SocialComponent` (Social & Psychological State)**:
    *   Owns: `PsychologyComponent`, `LeisureManager`.
    *   Responsibilities: Social status calculation, political opinion, need updates, leisure effects.

  <!-- Placeholder for diagram -->

---

## 4. Implementation Plan

### Track A: DTO & Interface Definition (`api.py`)

1.  **Create `modules/household/dtos.py`**:
    *   Define `HouseholdStateDTO`: A comprehensive, read-only Pydantic model containing all primitive state from `Household` required by the `DecisionEngine` and other systems. This breaks the hard dependency.
    *   Define `CloningRequestDTO`: Contains `new_id`, `initial_assets_from_parent`, `current_tick`.
    *   Define `EconContextDTO`: Contains `markets`, `market_data`, `current_time`.
    *   Define `SocialContextDTO`: Contains `current_time`.

2.  **Create `modules/household/api.py`**:
    *   Define `IBioComponent`, `IEconComponent`, `ISocialComponent` abstract base classes with method signatures for all public-facing actions.

### Track B: Component Implementation

1.  **Create `modules/household/bio_component.py`**:
    *   Implement `BioComponent`.
    *   Move the `clone()` method logic from `Household` here. It will only be responsible for creating a new `Household` instance with copied biological/demographic state. **It MUST NOT handle AI/Q-table inheritance.**
    *   Move aging and death logic from `AgentLifecycleComponent`.

2.  **Create `modules/household/econ_component.py`**:
    *   Implement `EconComponent`.
    *   This component will have methods like `get_assets()`, `adjust_assets()`, `get_inventory()`, etc.
    *   Move the orchestration logic from `Household.make_decision()` (e.g., `decide_housing`, panic selling, targeted order refinement) into a new `orchestrate_economic_decisions` method.

3.  **Create `modules/household/social_component.py`**:
    *   Implement `SocialComponent`.
    *   Move `calculate_social_status()`, `update_political_opinion()`, and `update_needs()` logic into this component.

### Track C: `Household` Facade Refactoring

1.  **Modify `simulation/core_agents.py` (`Household`)**:
    *   In `__init__`, instantiate the new components.
    *   Replace direct attribute access (e.g., `self.age`) with `@property` getters that delegate to the appropriate component (e.g., `return self.bio_component.age`).
    *   Create setters (`@age.setter`) where necessary, which also delegate.
    *   Refactor `make_decision()`: It will now first create the `HouseholdStateDTO`, then call the `DecisionEngine`, and finally call `self.econ_component.orchestrate_economic_decisions()` to apply results.
    *   Refactor `clone()` to call `self.bio_component.clone()`.

### Track D: Decouple `DecisionEngine`

1.  **Modify `simulation/dtos.py` (`DecisionContext`)**:
    *   Change the `household: "Household"` attribute to `state: HouseholdStateDTO`.
2.  **Modify `simulation/decisions/ai_driven_household_engine.py`**:
    *   Update `make_decisions` to read from the `context.state` DTO instead of the `context.household` object.

---

## 5. Verification Plan

1.  **Component Unit Tests**: Create new test files for each component (`tests/modules/household/test_bio_component.py`, etc.) to test their logic in isolation using mocked DTOs.
2.  **Preserve Existing Tests**: The Facade pattern ensures that `tests/verification/verify_mitosis.py` and other tests that rely on `golden_households` will continue to pass without modification. No changes to `conftest.py` are required.
3.  **Integration Test**: The existing `make_decision` tests will now serve as integration tests for the `Household` facade and its underlying components.

---

## 6. 🚨 Risk & Impact Audit (Mitigation Plan)

*   **Risk: Golden Fixture and Test Incompatibility**
    *   **Mitigation**: The `Household` class will be maintained as a **Facade**, preserving its public constructor and property API. Properties like `.age` and `.assets` will become getters/setters that delegate to the new internal components. This ensures 100% backward compatibility with `tests/conftest.py` and `verify_mitosis.py`.

*   **Risk: Violation of AI/Biology Separation in `clone()`**
    *   **Mitigation**: The new `BioComponent.clone()` method will be strictly responsible only for creating the new `Household` instance and copying biological/demographic attributes. It will have no knowledge of the AI engine. The external `AITrainingManager.inherit_brain()` process, as validated in `test_mitosis_brain_inheritance`, will remain responsible for all AI-related inheritance.

*   **Risk: Misplacing Orchestration Logic**
    *   **Mitigation**: The complex orchestration logic within `Household.make_decision()` will be explicitly preserved. The `Household` facade will remain the orchestrator, coordinating calls in a well-defined sequence:
        1.  Create `HouseholdStateDTO`.
        2.  Call `DecisionEngine` to get orders.
        3.  Call `EconComponent` to refine and apply economic rules (e.g., panic selling).
        4.  Call `SocialComponent` to update status based on outcomes.

*   **Risk: Conflicting Component Hierarchies**
    *   **Mitigation**: This specification establishes a clear ownership hierarchy. The new `Bio/Econ/Social` components will act as containers for the existing components (`DemographicsComponent`, `PsychologyComponent`, etc.), as outlined in the "Target Architecture" section. This avoids conflicts and clarifies responsibility.

*   **Constraint: Strict Decoupling via DTOs**
    *   **Mitigation**: This plan mandates the creation of a `HouseholdStateDTO`. The `DecisionContext` will be refactored to use this DTO, completely removing the direct dependency on the `Household` object and satisfying the decoupling requirement. Communication between the new components will also utilize DTOs where appropriate.

---
## 7. Mandatory Reporting (Jules's Guideline)
During implementation, any unforeseen challenges, architectural friction, or potential improvements discovered must be logged as a new entry in `communications/insights/`. Any identified technical debt must be proposed for inclusion in `design/TECH_DEBT_LEDGER.md`.
