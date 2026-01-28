# 🏗️ Structural Audit Report v2 (AUDIT-STRUCTURAL-V2)

## 1. God Class Risks
Analysis identified files exceeding 800 lines and classes with excessive complexity (methods > 20).

### 🚨 Critical Risk: Household Agent
- **File:** `simulation/core_agents.py`
- **Line Count:** **952** (Threshold: 800)
- **Class:** `Household`
- **Complexity:** **105 Methods**
- **Analysis:** The `Household` class is a massive God Class. While it delegates some logic to `BioComponent`, `EconComponent`, etc., the facade itself remains bloated with getter/setter sprawl, legacy compatibility methods, and direct state manipulation.
- **Inheritance:** `BaseAgent` -> `ILearningAgent` -> `Household` (Depth: 2, Acceptable).

### ⚠️ Moderate Risk: Firm Agent
- **File:** `simulation/firms.py`
- **Class:** `Firm`
- **Complexity:** 39 Methods
- **Analysis:** `Firm` is accumulating responsibilities (Production, Finance, HR, Sales, Brand, R&D). It is approaching God Class status.

### Other Complexity Notables
- `FinanceDepartment` (29 methods): becoming a "God Component".
- `Bank` (26 methods).

---

## 2. Leaky Abstraction & Purity Audit

### `make_decision` & `DecisionContext`
The core agents (`Household`, `Firm`) correctly utilize the `DecisionContext` pattern with DTOs.
- `Household.make_decision`: Instantiates `DecisionContext` with `state_dto` and `config_dto`. **COMPLIANT**.
- `Firm.make_decision`: Instantiates `DecisionContext` with `state_dto` and `config_dto`. **COMPLIANT**.

### ❌ Violation: Government Agent
- **File:** `simulation/agents/government.py`
- **Method:** `make_policy_decision`
- **Violation:** Passes `self` directly to the policy engine:
  ```python
  decision = self.policy_engine.decide(self, self.sensory_data, current_tick, central_bank)
  ```
- **Impact:** The `IGovernmentPolicy` implementations (e.g., `TaylorRulePolicy`) have direct write access to the `Government` instance, violating the "Read-Only Decision Context" principle.

---

## 3. Sequence & Scheduler Analysis

- **File:** `simulation/orchestration/tick_orchestrator.py`
- **Status:** **PASS**
- **Observed Sequence:**
  1. `Phase_Production` (Pre-step)
  2. `Phase1_Decision`
  3. `Phase2_Matching`
  4. `Phase3_Transaction`
  5. `Phase4_Lifecycle`
- **Verification:** The strictly required order (Decisions -> Matching -> Transactions -> Lifecycle) is preserved. The existence of `tick_scheduler.py` was ruled out (removed/renamed).

---

## 4. Prioritized Architecture Debt Repayment

| Priority | Component | Action | Rationale |
| :--- | :--- | :--- | :--- |
| **P0** | **Household** | **Extract Facade Logic** | The file size (952 lines) and method count (105) make this unmaintainable. Move property getters/setters into the DTOs or stateless helpers where possible. Remove legacy compatibility layers. |
| **P1** | **Government** | **DTO Enforcement** | Update `IGovernmentPolicy.decide` to accept `GovernmentStateDTO` instead of `Government` instance. Prevent side effects in policy logic. |
| **P2** | **FinanceDept** | **Decompose** | Split `FinanceDepartment` into `Treasury` (Cash/Bond mgmt) and `Accounting` (Reporting). |
| **P3** | **Firm** | **Component Encapsulation** | Ensure `HR`, `Sales`, `Production` are strictly decoupled and do not rely on `firm` parent properties implicitly. |

**Summary:** The codebase has successfully adopted DTOs for the main agents (`Household`, `Firm`), but the `Household` class itself has become a container for excessive boilerplate. The `Government` agent lags behind in architectural purity.
