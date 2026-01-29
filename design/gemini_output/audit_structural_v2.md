# [AUDIT-STRUCTURAL-V2] 구조적 결함 및 누출된 추상화 전수 조사 보고서

## 1. God Class 위험군 리스트

기준: 라인 수 > 800 또는 상속 깊이 > 4.

### 위험군 (Action Required)
*   **`simulation/core_agents.py`**
    *   **Line Count:** 952 lines.
    *   **Class:** `Household`
    *   **Risk:** High. The file encapsulates the entire Household agent logic, including complex initialization, decision delegation, and state management adapters.
    *   **Inheritance:** `Household` -> `BaseAgent` -> `ABC`. (Depth: 2). Inheritance depth is safe, but the class is bloated horizontally with too many responsibilities (Bio, Econ, Social component orchestration).

### 관찰군 (Monitor)
*   **`simulation/agents/government.py`**
    *   **Line Count:** 711 lines.
    *   **Class:** `Government`
    *   **Risk:** Medium. Approaching the limit. Contains logic for Tax, Welfare, Infrastructure, Education, and Policy execution.
*   **`simulation/firms.py`**
    *   **Line Count:** 650 lines.
    *   **Class:** `Firm`
    *   **Risk:** Low/Medium. Seems well-composed with `FinanceDepartment`, `HRDepartment`, etc., but the facade itself is growing.

---

## 2. Leaky Abstraction 위반 지점/라인 전체 목록

기준: `make_decision` 메서드에 `self`(에이전트 인스턴스) 또는 `government` (에이전트 인스턴스)를 직접 전달하는 경우. DTO가 아닌 엔티티 전달.

### A. Phase Execution (Orchestration Layer)
**File:** `simulation/orchestration/phases.py`
*   **Line 309:** `firm_orders, action_vector = firm.make_decision(..., government=state.government, ...)`
    *   **Violation:** Passes raw `Government` agent object instead of `GovernmentStateDTO`.
*   **Line 335:** `household_orders, action_vector = household.make_decision(..., government=state.government, ...)`
    *   **Violation:** Passes raw `Government` agent object instead of `GovernmentStateDTO`.

### B. Agent Definitions (Implementation Layer)
**File:** `simulation/firms.py`
*   **Line 291:** `def make_decision(..., government: Optional[Any] = None, ...)`
    *   **Violation:** Signature accepts `Any` (runtime `Government` agent).
*   **Line 332:** `self._execute_internal_order(order, government, current_time)`
    *   **Violation:** Passes raw agent down to private methods.
*   **Line 344:** `if self.finance.invest_in_automation(spend, government):`
    *   **Violation:** Passes raw agent to `FinanceDepartment`.
*   **Line 350:** `self.finance.pay_ad_hoc_tax(amount, reason, government, current_time)`
    *   **Violation:** Passes raw agent to `FinanceDepartment`.

**File:** `simulation/core_agents.py`
*   **Line 427:** `def make_decision(..., government: Optional[Any] = None, ...)`
    *   **Violation:** Signature accepts `Any` (runtime `Government` agent).
    *   *Note:* While `Household` creates a `DecisionContext`, the `government` argument is available in the scope and potentially passed to sub-components (though `Household` appears to use it less actively than `Firm`).

**File:** `simulation/base_agent.py`
*   **Abstract Method:** `def make_decision(..., markets: Dict[str, Any], ...)`
    *   **Violation:** Enforces the pattern of passing raw `markets` dictionary (containing Market objects) instead of `MarketSnapshotDTO` or similar.

---

## 3. Sequence Check (Tick Scheduler)

기준: Decisions -> Matching -> Transactions -> Lifecycle 순서 준수 여부.

**File:** `simulation/orchestration/tick_orchestrator.py` & `phases.py`

### Main Sequence (Compliant)
The `TickOrchestrator` executes phases in this order:
1.  `Phase0_PreSequence`
2.  `Phase_Production` (Phase 0.5)
3.  `Phase1_Decision` (**Decisions**)
4.  `Phase2_Matching` (**Matching**)
5.  `Phase3_Transaction` (**Transactions**)
6.  `Phase4_Lifecycle` (**Lifecycle**)
7.  `Phase5_PostSequence`

**Compliance Status:** **PASS** (General Structure)

### Exceptions & Technical Deviations
1.  **Phase 0 Policy Decisions:**
    *   `Phase0` executes `state.government.make_policy_decision(...)` and `mp_manager.determine_monetary_stance(...)`.
    *   **Impact:** Government and Central Bank act *before* private agents. This is likely intended (Fiscal/Monetary policy sets the stage), but structurally it puts "Decisions" in Phase 0.
2.  **Phase 3 Implicit Transaction Generation:**
    *   `Phase3` calls `firm.generate_transactions(...)`.
    *   **Impact:** Payroll, Tax, and Dividend transactions are generated *during* the Transaction phase based on state, rather than being explicit "Orders" generated in the Decision phase. This decouples these financial flows from the "Order -> Match" mechanism.
    *   **Verdict:** Acceptable pattern for automatic obligations, but represents a "Hidden Decision" (e.g., to pay dividends or fire people due to lack of funds) that happens outside Phase 1.

---

## 4. 아키텍처 부채 상환 우선순위 제안

### Priority 1: Fix Leaky Abstractions (High Risk)
The passing of the raw `Government` object is the most critical leak because it allows agents to mutate the government state or access privileged methods (like `collect_tax` directly) bypassing the TaxAgency/Settlement flows.

1.  **Refactor `GovernmentStateDTO`**: Ensure it contains all necessary public information (tax rates, public opinion, infrastructure level) needed for agent decisions.
2.  **Update `phases.py`**: Inject `GovernmentStateDTO` (or `sensory_data` from it) into `make_decision` instead of `state.government`.
3.  **Update `Firm`/`Household` logic**: Modify `make_decision` to use the DTO properties. Refactor `FinanceDepartment` methods to consume DTOs or Context objects, removing the dependency on the `Government` instance.

### Priority 2: Decompose God Class (`core_agents.py`)
`Household` is too large.
1.  **Extract `HouseholdState`**: Move the DTO state management (lines 80-200) into a dedicated State Manager or richer DTO handling class.
2.  **Extract `HouseholdLifecycle`**: The `update_needs`, `consume`, and `apply_leisure_effect` logic (lines 500-600) can be moved to a `HouseholdLifecycleManager` component, similar to `FinanceDepartment` in Firms.

### Priority 3: Standardize Market Interaction
Convert the `markets` dictionary passed to `make_decision` into a `MarketInterface` or `MarketAccessDTO` that only exposes `view_price` / `place_order` methods, preventing agents from inspecting deep market state (like `order_book`) directly unless allowed.
