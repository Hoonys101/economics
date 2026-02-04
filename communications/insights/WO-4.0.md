# WO-4.0: Household Decomposition Insights

## Technical Debt & Observations

1.  **Implicit Dependencies in Mixins**:
    The created mixins (`HouseholdPropertiesMixin`, `HouseholdFinancialsMixin`, etc.) implicitly rely on the existence of specific attributes on `self` (e.g., `_econ_state`, `_bio_state`, `config`, `logger`). While this is standard for mixins, it creates hidden coupling. Future refactoring should consider defining a `HouseholdProtocol` that these mixins can type-hint against to make requirements explicit.

2.  **Circular Import Challenges**:
    The `HouseholdReproductionMixin.clone` method requires instantiating a new `Household`. Since `Household` inherits from this mixin, a circular dependency exists. This was resolved using a local import inside the method, but it points to a tight coupling between the mixin and the class it enhances.

3.  **Dual Asset State**:
    `Household` overrides `BaseAgent.assets` to redirect to `_econ_state.assets`. However, `BaseAgent` still maintains its own `_assets` attribute, and the setter in `HouseholdPropertiesMixin` tries to keep them in sync (`self._assets = value`). This dual source of truth is a potential bug source if `_assets` is accessed directly by base class methods (though `BaseAgent` methods use `_internal_add_assets` which we overrode).

4.  **Orchestration Complexity**:
    While method implementations were moved to mixins, `Household.__init__` and `Household.make_decision` remain complex. `make_decision` acts as a high-level orchestrator calling various components. This suggests that `Household` is still acting as a Facade/Controller. Moving `make_decision` logic to a dedicated `AgentBrain` or `DecisionOrchestrator` could be a future step.

5.  **Legacy DTO Usage**:
    `HouseholdStateDTO` is deprecated but still instantiated in `make_decision` for backward compatibility with `DecisionContext`. Migration to `HouseholdSnapshotDTO` across all systems (DecisionEngine, etc.) is incomplete.

## Refactoring Impact
The decomposition successfully reduced the lines of code in `simulation/core_agents.py` by offloading property accessors and domain-specific logic to mixins. The public API remains unchanged, ensuring compatibility with existing tests and systems.
