# Technical Insight Report: Household Agent Decomposition (TD-260)

## 1. Problem Phenomenon
The `Household` agent was a monolithic "God Object" inheriting from multiple Mixins (`HouseholdLifecycleMixin`, `HouseholdFinancialsMixin`, etc.) and `BaseAgent`. This led to:
- **Tight Coupling:** Mixins directly accessed `self` attributes, making it impossible to test components in isolation.
- **State Pollution:** `BaseAgent` introduced attributes (like `inventory`, `wallet`) that conflicted with or duplicated the `EconStateDTO`.
- **Testing Fragility:** Unit tests required mocking the entire `Household` object and its mixins, leading to brittle tests.
- **Maintenance Nightmare:** Logic for biological aging, economic decisions, and social status was intertwined.

## 2. Root Cause Analysis
The architecture relied on **inheritance-based composition** (Mixins) rather than **aggregation/composition**. Mixins are essentially "abstract classes" that expect a specific host interface, leading to implicit dependencies. `BaseAgent` further complicated this by forcing a specific state shape that didn't align with the new DTO-driven design.

## 3. Solution Implementation Details
We refactored `Household` into an **Orchestrator-Engine** architecture:

### 3.1. Stateless Engines
We decomposed logic into 5 pure, stateless engines:
1.  **`LifecycleEngine`**: Manages aging and death. Returns `CloningRequestDTO` for reproduction.
2.  **`NeedsEngine`**: Calculates need decay and prioritizes needs based on personality.
3.  **`SocialEngine`**: Updates social status and political opinion.
4.  **`BudgetEngine`**: Allocates financial resources, prioritizing survival needs (Survival Instinct) over abstract AI plans.
5.  **`ConsumptionEngine`**: Executes consumption from inventory and generates concrete market orders.

### 3.2. DTO-Driven Communication
- **State DTOs**: `BioStateDTO`, `EconStateDTO`, `SocialStateDTO` hold all state.
- **Input/Output DTOs**: Each engine accepts a specific `InputDTO` (e.g., `NeedsInputDTO`) and returns an `OutputDTO` (e.g., `NeedsOutputDTO`).
- **No Side Effects**: Engines do not modify the `Household` instance directly; they return new state copies or update instructions.

### 3.3. Orchestrator (`Household` Class)
- The `Household` class now owns the state DTOs and instances of the engines.
- `make_decision` coordinates the flow: `Lifecycle` -> `Needs` -> `Social` -> `AI` -> `Budget` -> `Consumption`.
- Legacy Mixins were removed.

### 3.4. Verification
- **Unit Tests**: Created isolated unit tests for each engine in `tests/unit/household/engines/`, mocking inputs and verifying outputs without full Agent instantiation.
- **Integration Test**: Fixed `tests/integration/scenarios/verification/verify_mitosis.py` to support the new `Household` signature and DTO structure. Specifically fixed stock inheritance logic to use the new `Portfolio.add/remove` API and ensured `education_xp` property availability.
- **Survival Instinct**: Verified that `BudgetEngine` prioritizes food when funds are low, preventing starvation loops.

## 4. Lessons Learned & Technical Debt
- **Portfolio API Confusion**: The `Portfolio` class uses `add` and `remove` but older tests/logic expected `add_share` or similar. We standardized on `add` in the tests.
- **Mocking DTOs**: Mocking data classes (like `EconStateDTO`) in tests can be tricky if they use `__slots__` or complex copy logic. We had to ensure mocks supported `copy()` returning another mock with correct attributes.
- **Legacy Property Access**: Some systems (like `AITrainingManager`) expect direct attribute access (e.g., `agent.education_xp`) which are now encapsulated in DTOs. We added property getters to `Household` facade to maintain compatibility.
- **Refactoring Scope**: This was a massive refactor. Breaking it down into Engine creation -> Class refactor -> Test fix steps was crucial. Using `verify_mitosis.py` as a canary test was very effective.

## 5. Conclusion
The `Household` agent is now modular, testable, and compliant with the architectural guardrails (DTO purity, Protocol purity). Future changes to "Needs" logic, for example, can be done safely within `NeedsEngine` without risking regressions in `Budgeting` or `Consumption`.
