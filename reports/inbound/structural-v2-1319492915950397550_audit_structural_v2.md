# Audit Report: Structural & Abstraction Analysis

## [God Class 위험군 리스트]

### 1. High Risk (Size > 800 lines)
*   **`simulation/tick_scheduler.py` (945 lines)**
    *   **Reason:** Orchestrates the entire simulation loop. Contains logic for all phases (`Decisions`, `Matching`, `Transactions`, `Lifecycle`), market data preparation, and system transaction generation.
    *   **Violation:** Violates Single Responsibility Principle (SRP). It knows too much about the internals of every phase.
*   **`simulation/core_agents.py` (908 lines)**
    *   **Reason:** Contains the `Household` class, which acts as a Facade for multiple components (`Bio`, `Econ`, `Social`, `Psychology`). While it delegates logic, the sheer number of property delegates and passthrough methods bloats the file.
    *   **Violation:** "Large Class" smell. High cognitive load to maintain.

### 2. Inheritance Depth Analysis
*   **Result:** No classes with inheritance depth > 4 were found in the core `simulation/` directory.
    *   `Household` -> `BaseAgent` -> `ABC` (Depth 2/3)
    *   `Firm` -> `BaseAgent` -> `ABC` (Depth 2/3)
    *   Most complexity comes from Composition (Facade pattern) rather than Inheritance, which is architecturally healthier but still results in large files.

---

## [Leaky Abstraction 위반 지점/라인 전체 목록]

### 1. Government Policy Engine Leaks (Direct State Mutation)
The Government agent passes itself (`self`) to policy engines, which then directly modify the agent's state instead of returning a decision DTO.

*   **`simulation/agents/government.py`**
    *   Line ~300 (in `make_policy_decision`): `decision = self.policy_engine.decide(self, self.sensory_data, current_tick, state.central_bank)`
    *   **Violation:** Passes `self` (Mutable Agent) to a Decision Component.
*   **`simulation/policies/taylor_rule_policy.py`**
    *   Method `decide(self, government, sensory_data, ...)`
    *   **Violation:** Directly modifies `government.potential_gdp`, `government.fiscal_stance`, `government.income_tax_rate`.
*   **`simulation/policies/smart_leviathan_policy.py`**
    *   Method `decide(self, government, sensory_data, ...)`
    *   **Violation:** Directly modifies `central_bank.base_rate` and `government` tax rates/multipliers.

### 2. FinanceDepartment Immediate Execution (Phase Violation)
Firms execute financial transfers *immediately* during the Decision phase, bypassing the Transaction phase and Settlement System queue.

*   **`simulation/firms.py`**
    *   Method `_execute_internal_order` (called inside `make_decision`):
        *   Calls `self.finance.invest_in_automation(...)`
        *   Calls `self.finance.pay_ad_hoc_tax(...)`
        *   Calls `self.finance.pay_severance(...)`
*   **`simulation/components/finance_department.py`**
    *   `invest_in_automation`: Calls `self.firm.settlement_system.transfer(...)` -> **Immediate Effect**
    *   `pay_ad_hoc_tax`: Calls `government.collect_tax(...)` -> **Immediate Effect**
    *   **Violation:** "Decisions" phase should only produce intents (Orders/Transactions). Money movement must happen in "Transactions" phase.

---

## [아키텍처 부채 상환 우선순위 제안]

### Priority 1: Fix Phase Sequence Violations (Finance System)
*   **Issue:** `Firm` decisions cause immediate money transfer (Side Effect) during the Decision phase.
*   **Action:**
    *   Modify `Firm.make_decision` and `FinanceDepartment` to return `Transaction` objects for internal actions (Automation, Tax, Severance) instead of executing them immediately.
    *   Queue these transactions to be executed in `TickScheduler._phase_transactions`.
*   **Benefit:** Restores "Sacred Sequence" integrity. Prevents race conditions or state inconsistencies during parallel decision making.

### Priority 2: Seal Government Abstraction Leaks
*   **Issue:** Policy Engines modify Government/CentralBank state directly.
*   **Action:**
    *   Refactor `IGovernmentPolicy.decide` to return a `PolicyActionDTO` containing target rates, tax changes, and budget adjustments.
    *   Update `Government.make_policy_decision` to apply these changes *after* the decision engine returns.
*   **Benefit:** Decouples Logic (Policy) from State (Agent). Makes policies testable without mocking complex Agents.

### Priority 3: Decompose TickScheduler
*   **Issue:** `TickScheduler` is a God Class (900+ lines).
*   **Action:**
    *   Extract Phase logic into dedicated handlers: `DecisionPhaseHandler`, `MatchingPhaseHandler`, `TransactionPhaseHandler`, `LifecyclePhaseHandler`.
    *   Extract `prepare_market_data` into a `MarketDataProvider` service.
*   **Benefit:** Improves readability and enforces strict separation of concerns between phases.

### Priority 4: Normalize System Agents (Government/CentralBank)
*   **Issue:** Government and Central Bank act *before* the main simulation loop (Phase 0/Pre-Phase 1).
*   **Action:**
    *   Move `Government.make_policy_decision` and `CentralBank.step` into `_phase_decisions` (or a dedicated `_phase_system_decisions` immediately preceding it).
    *   Ensure they generate `Transaction` objects for their actions (e.g., Open Market Operations) rather than direct state modification.
*   **Benefit:** Unified agent lifecycle. Simplifies debugging and logging.