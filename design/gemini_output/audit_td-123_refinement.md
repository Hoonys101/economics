# Refinement Report for TD-123: Household Decomposition

## 1. Executive Summary

This report provides a detailed analysis of `design/specs/TD-123_Household_Decomposition.md` based on the findings from the Pre-flight Audit. While the core direction of the specification—transitioning `Household` to a DTO-driven facade—is correct, the audit accurately identified critical gaps in data contracts, state encapsulation, and dependency management.

This refinement plan outlines the necessary modifications to align the specification with the architectural constraints of the existing system, ensuring a successful and non-disruptive refactoring.

---

## 2. Risk 1: Immutable AI Data Contract

### Discrepancy
- **Audit Finding**: The `AIDrivenHouseholdDecisionEngine` and learning loop are tightly coupled to a **flat `HouseholdStateDTO`** and a **flat `dict`** (`get_agent_data`).
- **Specification (`TD-123`)**: Proposes a new, internally **nested `HouseholdStateDTO`** (containing `bio`, `econ`, `social` sub-DTOs) but fails to address how this new structure will interface with the legacy AI engine.

### Required Refinement
The `Household` facade must implement the **Adapter Pattern**.

1.  **Internal State**: The facade will maintain its new, clean, nested DTOs (`self.bio_state`, `self.econ_state`, `self.social_state`) as the single source of truth internally.
2.  **Adapter Method `create_state_dto`**: The existing `create_state_dto` method must be updated. Instead of being a simple data class, it will become a **translator method**. It will read from the internal nested DTOs and construct the legacy **flat `HouseholdStateDTO`** on-the-fly, as expected by `AIDrivenHouseholdDecisionEngine.make_decisions`.
3.  **Adapter Method `get_agent_data`**: This method must also be updated to read from the internal nested DTOs and return the legacy **flat `dict`** structure required by the `update_learning` method.

The specification must be amended to describe this adapter role, explicitly stating that the public contracts of the AI Engine and learning systems are to be treated as immutable.

---

## 3. Risk 2: Incomplete Cloning Logic Migration (SRP Violation)

### Discrepancy
- **Audit Finding**: The legacy `apply_child_inheritance` method, containing essential cloning logic, remains in the facade, violating the Single Responsibility Principle.
- **Specification (`TD-123`)**: Proposes `prepare_clone_state` methods for components but does not explicitly mandate the migration of all logic from `apply_child_inheritance`.

### Required Refinement
The specification must be updated with the following explicit instructions:

1.  **Full Logic Migration**: All business logic within `core_agents.py::Household.apply_child_inheritance` (specifically skill inheritance, `education_level` setting, and `expected_wage` calculation) **MUST** be moved into the `EconComponent.prepare_clone_state` method.
2.  **Facade Orchestration**: The `Household.clone` method's sole responsibilities are:
    a. Orchestrating calls to `bio_component.prepare_clone_state`, `econ_component.prepare_clone_state`, etc.
    b. Creating a new decision engine via the `IDecisionEngineFactory`.
    c. Instantiating the new `Household` with the resulting state DTOs and engine.
3.  **Method Deprecation**: The `apply_child_inheritance` method on the `Household` facade **MUST** be deleted after its logic is migrated.

---

## 4. Risk 3: Incomplete State Encapsulation in DTOs

### Discrepancy
- **Audit Finding**: Several state attributes (`initial_assets_record`, `credit_frozen_until_tick`, `aptitude`) still reside on the `Household` class and are not accounted for in the spec's DTOs.
- **Specification (`TD-123`) & `api.py`**: While `aptitude` was correctly planned for migration, the provided `api.py` is missing `credit_frozen_until_tick` and the spec is silent on `initial_assets_record`.

### Required Refinement
The `modules/household/dtos.py` and associated `api.py` files must be updated to ensure complete state migration.

1.  **`EconStateDTO` must be updated to include:**
    - `credit_frozen_until_tick: int`
    - `initial_assets_record: float` (To preserve the initial state for analysis or other logic).
2.  **Verification**: The specification should add a final verification step requiring developers to scan the `Household.__init__` method and ensure **no non-transient state variables** remain, other than the primary state DTOs (`bio_state`, `econ_state`, `social_state`).

---

## 5. Risk 4: Hidden Dependency Injection Requirements

### Discrepancy
- **Audit Finding**: The proposed stateless components and factories will require context (like `config_module` and `logger`) that is not included in the method signatures defined in the spec.
- **Specification (`TD-123`)**: Defines pure method signatures (e.g., `run_lifecycle(state, context)`) that do not account for passing these critical dependencies.

### Required Refinement
The `Household` facade must act as a **Dependency Injection Hub**.

1.  **Update Component Interfaces**: The interfaces in `api.py` and the corresponding method signatures in the specification must be updated. Any component method that requires configuration or logging must accept them as parameters.
    - **Example (Old)**: `run_lifecycle(self, state: BioStateDTO, context: LifecycleContext) -> BioStateDTO`
    - **Example (New)**: `run_lifecycle(self, state: BioStateDTO, context: LifecycleContext, config: Any, logger: Logger) -> BioStateDTO`
2.  **Update Factory Interface**: The `IDecisionEngineFactory.create_for_clone` method must also be updated to accept the `config_module` and a `logger` instance to correctly initialize the new engine.
3.  **Facade Responsibility**: The specification must clarify that the `Household` facade is responsible for passing `self.config_module` and `self.logger` into the component and factory methods during invocation.
