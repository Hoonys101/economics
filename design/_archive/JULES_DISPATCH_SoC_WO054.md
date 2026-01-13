# Jules Dispatch: SoC Refactoring & WO-054 Completion

**Target:** Jules (Implementationist)
**Context:** Phase 23 (The Great Expansion)
**Goal:** Complete the Separation of Concerns (SoC) refactoring and implement the Public Education System (WO-054).

---

## Task 1: Complete SoC Refactoring (Phase 1)

I have already extracted `TransactionProcessor` from `SimulationEngine`. Your job is to:

### 1.1. Refactor `Firm` Class (Componentization)
*   **File:** `simulation/firms.py`
*   **Action:** Extract HR and Finance logic into dedicated components.
*   **Components:**
    *   `HRDepartment`: Manages employees, calculates skill-based wages (including Halo Effect), and handles insolvency firing/severance pay.
    *   `FinanceDepartment`: Manages maintenance fees, corporate taxes, and dividend distribution.
*   **Integration:** Update `Firm.update_needs` to delegate to these components.

### 1.2. Verification
*   Ensure all existing tests pass after refactoring.
*   The system must maintain exact same behavior (Deterministic check).

---

## Task 2: Implement WO-054 (Public Education System)

Follow the Architect Prime's final guidelines:

### 2.1. Household Update
*   **File:** `simulation/core_agents.py`
*   **Action:** Add an immutable `aptitude` attribute (Gaussian: 0.5 mean, 0.15 std, clamped 0-1).

### 2.2. Government Logic
*   **File:** `simulation/agents/government.py`
*   **Action:** Implement `run_education_program(agents, config)`.
    *   **Frequency:** Calculate wealth ranking every 30 ticks.
    *   **Scholarship:** 80% tuition subsidy if `wealth < bottom 20%` AND `aptitude >= 0.8`.
    *   **Basic Edu:** 100% subsidy for Level 0 → 1.
    *   **Execution:** Call at the START of `Simulation.run_tick()`.

### 2.3. Tech Diffusion Feedback
*   **File:** `simulation/systems/technology_manager.py`
*   **Action:** Update `get_diffusion_rate()`.
    *   `current_rate = base_rate * (1 + min(1.5, 0.5 * (avg_edu_level - 1.0)))`.

---

## Task 3: Final Verification
*   Run a 500-tick simulation.
*   Assert that **IGE (Intergenerational Elasticity)** decreases from ~0.96 to **0.6~0.7**.
*   Verify that `avg_education_level` correlates with tech diffusion acceleration.

---

## Reference Documents
*   `reports/2026-01-12_Refactoring_Proposal_SoC.md`
*   `design/work_orders/WO-054-Public-Education-System.md`
*   `design/implementation_plan.md` (Updated with AP Specs)

**Execute.**
