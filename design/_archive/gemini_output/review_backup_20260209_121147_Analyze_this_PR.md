# 🔍 Summary
This Pull Request introduces a significant architectural refactoring of the `Household` agent. It successfully decomposes the monolithic, mixin-based class into a modern Orchestrator-Engine pattern. Logic is now encapsulated in stateless, DTO-driven engines (`Lifecycle`, `Needs`, `Budget`, `Social`, `Consumption`), which greatly enhances modularity, testability, and adherence to project architecture principles. The change includes a comprehensive insight report and new unit tests for the engines.

# 🚨 Critical Issues
No critical security vulnerabilities, zero-sum violations, or hardcoding of secrets were found.

# ⚠️ Logic & Spec Gaps
The refactoring is extensive and well-executed, but some significant logic gaps and incomplete implementations require attention.

1.  **Shared AI Engine State in `clone()`**:
    - **File**: `simulation/core_agents.py`
    - **Location**: `Household.clone` method
    - **Issue**: The `clone` method passes the parent's decision engine instance directly to the child: `engine=self.decision_engine, # Warning: Shared engine reference!`. As the developer correctly noted, this is a critical issue. Since the `AIDrivenHouseholdDecisionEngine` contains a stateful AI model (Q-tables), both parent and child will share the same "brain." Learning updates from one agent will incorrectly affect the other, corrupting the learning process for both. This is a hard-fail bug.

2.  **Incomplete Housing Purchase Logic (Data Loss)**:
    - **File**: `simulation/core_agents.py`
    - **Location**: `_execute_housing_action` method
    - **Issue**: When initiating a property purchase, the `down_payment_amount` is hardcoded to `0.0`. The developer's comment, `# TODO: BudgetEngine didn't calculate down payment? ... This is a loss of data`, confirms that the new `HousingActionDTO` is less informative than the `HousingPurchaseDecisionDTO` the system expects. This is a functional regression that will likely break the housing market mechanism.

3.  **Misplaced Skill Update Logic**:
    - **File**: `simulation/core_agents.py`
    - **Location**: `add_education_xp` method
    - **Issue**: The logic to update `labor_skill` based on `education_xp` is implemented directly within this method. The developer's comment notes that this logic was missed during the engine decomposition (`# I missed \`update_skills\` logic in my Engines implementation step.`). While functional, this violates the new architecture, where such logic should reside within a dedicated engine (e.g., a new `SkillEngine` or as part of the `SocialEngine`).

# 💡 Suggestions
1.  **Eliminate Ad-hoc `StateWrapper`**:
    - **File**: `modules/household/engines/budget.py`
    - **Location**: `_plan_housing` method
    - **Suggestion**: The local `StateWrapper` class is an architectural smell. The `HousingPlanner.evaluate_housing_options` method should be updated to accept the `EconStateDTO` directly, removing the need for this temporary wrapper and improving architectural consistency.

2.  **Centralize Default Parameters**:
    - **Files**: `modules/household/engines/budget.py`, `modules/household/engines/consumption.py`
    - **Suggestion**: Hardcoded fallback values like `food_price = 10.0` and consumption utility (`utility = 20.0`) should be moved to the `HouseholdConfigDTO`. This centralizes all tunable parameters and avoids magic numbers in the code.

# 🧠 Implementation Insight Evaluation
- **Original Insight**: 
```
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
```
- **Reviewer Evaluation**: The insight report is of **excellent quality**. It is thorough, well-structured, and accurately documents the rationale and implementation of this complex refactoring. The "Lessons Learned" section is particularly valuable, as it captures nuanced technical challenges (API inconsistencies, mocking DTOs, legacy compatibility) that provide actionable knowledge for future development and prevent institutional knowledge loss.

# 📚 Manual Update Proposal
The insights from this refactoring are valuable and should be recorded in the project's central knowledge base.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
```markdown
---
### TD-260: Post-Refactoring Interface Mismatches

*   **Phenomenon**: During the decomposition of the `Household` agent, friction was encountered with pre-existing APIs and attribute access patterns.
    1.  The `Portfolio` API was inconsistent (`add`/`remove` vs. expected `add_share`).
    2.  External systems like `AITrainingManager` and `HousingPlanner` expected direct attribute access (`agent.education_xp`) or legacy object structures, which were now encapsulated in DTOs.
*   **Impact**: Required creating backward-compatibility facades (property getters) on the new `Household` orchestrator class and ad-hoc wrappers (`StateWrapper`) in engines, slightly compromising the purity of the new architecture. Increased test-fixing time.
*   **Lesson**: When refactoring a core component, a full audit of its call sites across the codebase is necessary. Interfaces of interacting systems should be refactored simultaneously to prevent the creation of anti-patterns like compatibility facades and wrappers.
```

# ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

**Reasoning**: While this is a commendable and necessary architectural improvement, the `REQUEST CHANGES` verdict is issued due to the critical logic bugs identified. The shared AI engine state in `clone()` will corrupt agent learning, and the incomplete housing purchase logic is a functional regression. These issues must be addressed before this change can be merged. The presence and quality of the insight report are excellent, but they do not outweigh the severity of the implementation flaws.
