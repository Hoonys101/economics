# Technical Specification: TD-123 Household Decomposition (Refined)

## 1. Overview
This specification details the refactoring of the `Household` agent class into a pure **Facade**. All state and business logic will be fully encapsulated within three distinct, stateless components: `BioComponent`, `EconComponent`, and `SocialComponent`.

This refactoring strictly enforces the **Single Responsibility Principle (SRP)**, a **DTO-driven architecture**, and the **Adapter Pattern** to maintain compatibility with legacy AI engines.

## 2. Architectural Changes

### 2.1. Stateless Components & DTO-Driven Design
The core of this refactoring is the removal of the component-to-facade back-reference.

- **Internal State Management**:
  - `Household` will hold state in dedicated, internal DTOs: `self._bio_state`, `self._econ_state`, `self._social_state`.
  - Components are instantiated without state or back-references.
  - Component methods are pure functions: `(StateDTO, Context, Config, Logger) -> StateDTO`.

### 2.2. The Adapter Pattern (Critical for AI Compatibility)
The `Household` facade must maintain backward compatibility with the `AIDrivenHouseholdDecisionEngine` and learning loops which expect a **flat** `HouseholdStateDTO` and a **flat dict**.

1.  **`create_state_dto()`**: This method is now a **translator**. It must read from the internal nested DTOs and construct a flat `simulation.dtos.api.HouseholdStateDTO` on-the-fly.
2.  **`get_agent_data()`**: This method must be updated to read from nested DTOs and return the flat `dict` structure required by `update_learning`.

### 2.3. Dependency Injection Hub
The `Household` facade acts as a DI hub. All component methods requiring configuration or logging must accept them as parameters from the facade.
- **Example**: `run_lifecycle(state, context, config, logger)`

### 2.4. Refined Cloning & inheritance Logic
The legacy `apply_child_inheritance` method is deprecated and its logic moved.

1.  **Full Logic Migration**: All business logic within `core_agents.py::Household.apply_child_inheritance` (skill inheritance, education level, expected wage) **MUST** move to `EconComponent.prepare_clone_state`.
2.  **Factory Orchestration**: `Household.clone()` manages the split:
    a. Call `prepare_clone_state` for Bio, Econ, and Social components.
    b. Call `IDecisionEngineFactory.create_for_clone(parent_engine, config, logger)`.
    c. Instantiate new `Household`.

## 3. Detailed Design

### 3.1. State Encapsulation (Mandatory attributes)
All state currently in `Household` or `BaseAgent` must be moved.
- **`EconStateDTO` MUST include**:
    - `assets`, `inventory`, `is_employed`, `employer_id`, `current_wage`, `wage_modifier`, `labor_skill`, `education_xp`, `education_level`, `expected_wage`, `talent`, `skills`, `aptitude`.
    - `credit_frozen_until_tick: int` (Missing in initial draft)
    - `initial_assets_record: float` (Moved from `BaseAgent`)
    - `portfolio`, `durable_assets`, `owned_properties`, `residing_property_id`, `is_homeless`, `home_quality_score`.
- **`BioStateDTO` MUST include**: `age`, `gender`, `generation`, `is_active`, `health`, etc.
- **`SocialStateDTO` MUST include**: `personality`, `social_status`, `discontent`, etc.

### 3.2. Component APIs (`modules/household/api.py`)
Component methods must return copies of the state to avoid unintended side effects.

### 3.3. Facade Logic (`simulation/core_agents.py`)
- Properties (getters/setters) transparently map to the internal DTOs.
- `Household.make_decision` updates `wage_modifier` by calling `econ_component.update_wage_dynamics`.

## 4. Implementation Guidelines for Jules

1.  **Phase 1: DTOs & API**: Create `modules/household/dtos.py` and `modules/household/api.py` first. Ensure all attributes from Task 3.1 are present.
2.  **Phase 2: Components**: Implement `BioComponent`, `EconComponent`, and `SocialComponent`. Move the `apply_child_inheritance` logic during this phase.
3.  **Phase 3: Facade Refactoring**:
    - Replace all `self.attr` initializations in `Household.__init__` with DTO initializations.
    - Implement the Adapter methods (`create_state_dto`, `get_agent_data`).
    - Use `@property` to maintain the public API.
4.  **Phase 4: Verification**:
    - Run `pytest`. Existing tests MUST NOT be modified.
    - Verify `initial_assets_record` and `credit_frozen_until_tick` are correctly persisted and updated.

## 5. Verification
- **Zero-Regression Policy**: All existing tests in `tests/test_household_decision_engine_new.py` and `tests/test_corporate_manager.py` must pass.
- **Type Safety**: Use `mypy` or `ruff` to ensure DTO usage is consistent.
- **Component isolation**: Verify components can be instantiated and tested without a `Simulation` or `Household` object.

---
### 🚨 **Jules' Mandatory Reporting**
Logging required in `communications/insights/TD123-refined-YYYYMMDD.md`.
Focus on any challenges in the Adapter implementation.
