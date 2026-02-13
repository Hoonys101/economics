# Insights and Technical Debt - Household Engine Refactor

## Insights
1.  **Orchestrator-Engine Pattern**: Decomposing `Household` into stateless engines (`Lifecycle`, `Needs`, `Budget`, `Consumption`) significantly improved modularity. The `Household` class is now a pure orchestrator, managing state DTOs and delegating logic.
2.  **Factory Pattern**: Introducing `HouseholdFactory` centralized the creation logic, which was previously scattered across `DemographicManager` and `Household.clone`. This allows for better encapsulation of initialization rules and dependency injection.
3.  **Zero-Sum Integrity**: By ensuring `HouseholdFactory.create_newborn` initializes agents with 0.0 assets and relying on `DemographicManager` (and `SettlementSystem`) to transfer the initial gift, we enforce strict zero-sum financial integrity. No money is created "out of thin air" during birth.
4.  **Order Generation**: Moving the responsibility of generating orders for basic needs (like food) from `ConsumptionEngine` to `BudgetEngine` (as part of the `BudgetPlan`) clarifies the roles. `BudgetEngine` plans (allocates and decides what to buy), and `ConsumptionEngine` executes (places orders and consumes).

## Technical Debt / Future Work
1.  **Housing Logic in BudgetEngine**: The `BudgetEngine` implementation includes `_plan_housing` which delegates to `HousingPlanner`. However, the integration with `HousingSystem` via `Household` orchestrator is still somewhat coupled. Future refactoring could further decouple this by having `HousingSystem` act on the `HousingActionDTO` directly without `Household` mediation if possible, or standardizing the interface.
2.  **Mocking Challenges**: Tests mocking `EconStateDTO` faced issues with `spec=` not automatically mocking interface-typed fields like `wallet`. We had to explicitly assign mocks. A robust `MockFactory` that handles this automatically for all DTOs would be beneficial.
3.  **Configuration DTO Mismatch**: `HouseholdConfigDTO` lacked `initial_needs` which was required by `AgentCoreConfigDTO`. We worked around this by accessing the raw config module. Ideally, `HouseholdConfigDTO` should be the single source of truth for all household-related config, or `AgentCoreConfigDTO` should be decoupled from specific agent config classes.
4.  **Legacy `clone` Method**: `Household.clone` is deprecated but still exists for legacy test compatibility. It should be removed once all tests are migrated to use `HouseholdFactory`.

## Guardrail Compliance
-   **Zero-Sum Integrity**: Verified. New agents start with 0 assets.
-   **Engine Purity**: Verified. Engines are stateless classes/functions.
-   **Orchestrator Pattern**: Verified. `Household` delegates to engines.
-   **Protocol over Class**: Verified. Engines implement Protocols.
-   **DTO Purity**: Verified. Input/Output DTOs used.