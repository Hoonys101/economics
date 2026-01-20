# 🦅 PROJECT APEX: MASTER DIRECTIVE (Phase 14)

**To:** Jules (Implementation Lead)
**From:** Antigravity (Chief Architect)
**Date:** 2026-01-08 (Simulation Time)
**Subject:** CRITICAL UPDATE - Codebase Hardening & Human Capital Activation

---

## 🛑 STOP & READ: Status Reset

Legacy instructions are hereby superseded. We have deployed major architectural fixes to the `main` branch.
You are to abandon the previous wait-and-see validation approach and **proceed immediately** with development on the new codebase.

---

## 1. Architectural Changes (DEPLOYED)

We have resolved two critical technical debts that were blocking the "Industrial Revolution" logic.

### A. Refactoring: Data-Driven Manufacture (WO-023-A)
*   **Old Behavior:** Hardcoded `if sector == "GOODS"` checks in `firms.py` and `engine.py`.
*   **New Behavior:**
    *   `config.py`: Added `"sector": "GOODS"` (or FOOD, SERVICE) to all items in `GOODS` dictionary.
    *   `engine.py`: `spawn_firm` now dynamically reads sector from config.
    *   `firms.py`: `produce` method now produces `self.specialization` directly.
*   **Impact:** New industries can be added solely via `config.py`.

### B. Human Capital Protocol (WO-023-B)
*   **Problem:** Education consumption increased `education_xp` but had NO effect on productivity or wages.
*   **Fix Implemented:**
    1.  **The Lottery of Birth**: `Household` agents now spawn with randomized `Talent` (Gaussian distribution).
    2.  **Growth Formula**: `Household._update_skill()` now converts XP to Skill:
        $$ \text{Labor Skill} = 1.0 + \ln(\text{XP} + 1) \times \text{Talent} $$
    3.  **Meritocratic Pay**: `Firm.pay_wages()` now multiplies the base wage by `labor_skill`.
*   **Impact:** High innovation requires high-skill labor. The "Education" sector is now economically viable.

---

## 2. Completed: Banking System (WO-024)

The Fractional Reserve Banking System is successfully merged into `main`. 
-   **Features**: Deposit/Withdraw, Loan Requests, M2 Money Creation, Interest Churn.
-   **Correction**: `_manage_liquidity` is now implemented in the `AIDrivenHouseholdDecisionEngine`.

---

## 3. Immediate Action Plan (WO-025: Materiality & Durables)

Banking is stable. Now we transition from "Instant Consumption" to "Durables & Assets".

### Step 1: Materiality Implementation
*   **Reference**: `design/work_orders/WO-025-Materiality-Durables.md`
*   **Key Concept**: Goods are now `Consumables` (instant) or `Durables` (persistent assets with lifespan).
*   **Requirements**:
    *   **Household Brain Upgrade**: Implement the **Utility Saturation Logic** from `design/specs/utility_maximization_spec.md`. Agents must not hoard multiple fridges/assets if utility is saturated.
    *   **Depreciation**: Durables in agent inventory must lose `remaining_life` each tick and trigger disposal/replacement logic when spent.

### Step 2: Quality Ladder
*   **Firm Quality**: Production quality is now tied to the average labor skill of the firm's workforce.
*   **Impact**: High-skill firms produce high-quality durables that satisfy utility longer.

### Step 3: Business Cycle Verification (The Cliff & Echo)
Create `scripts/verify_durables.py` to confirm "The Sine Wave":
1.  **Sales Volatility**: Sales should spike at start (filling demand), drop to near zero (saturation), and echo back up when items break (replacement).
2.  **Wealth Storage**: Household assets should form a sawtooth pattern (Buy -> Depreciate -> Buy), not flatline like Food.
3.  **Quality Segmentation**: Confirm that Rich households own higher quality items than Poor households.

---

## 4. New Phase: Portfolio Optimization (WO-026)

Phase 15 (Durables) is verified. We now introduce the **"Rational Investor"**.

### Step 1: Personality Injection
*   **Module**: `simulation/core_agents.py`
*   **Task**: Add `risk_aversion` (float, 0.1~10.0) to `Household.__init__`.

### Step 2: The Portfolio Manager
*   **Reference**: `design/work_orders/WO-026-Portfolio-Manager.md`
*   **Task**: Implement `PortfolioManager.optimize_portfolio()`.
    *   **Logic**: Maximize Utility $U = E(R) - \lambda \sigma^2$.
    *   **Safety**: Ensure 3 months of living expenses are kept in Cash/Risk-Free.

### Step 3: Integration
*   **Module**: `simulation/decisions/ai_driven_household_engine.py`
*   **Trigger**: Run rebalancing logic monthly (`tick % 30 == 0`).
*   **Output**: Generate `DEPOSIT`, `WITHDRAW`, or `INVEST` (Startup) orders based on the optimizer's target.

### Step 4: Verification (The Friedman Effect)
Create `scripts/verify_portfolio.py` to confirm interest rate sensitivity:
1.  **Scenario**: Run simulation, then at T=50 raise Central Bank Base Rate significantly (e.g., to 10%).
2.  **Expectation**:
    *   **Deposits**: Should spike immediately after T=50.
    *   **Consumption/Startup**: Should cool down as money moves to banks.

---

## 5. New Phase: Corporate Intelligence (WO-027)

Firms are currently "too dumb". We must upgrade them with a **CEO Brain** module.

### Step 1: 3-Layer Architecture Implementation
*   **Layer 1 (Personality)**: Assign `BALANCED`, `GROWTH_HACKER`, or `CASH_COW` at `__init__`. This defines the reward weights for RL.
*   **Layer 2 (RL Intent)**: Implement 5-channel Q-learning aggressiveness in `FirmAI` (R&D, CAPEX, Dividend, Employment, Debt).
*   **Layer 3 (Logic Realization)**: Create `CorporateManager` to translate these 5 channels into concrete actions.

### Step 2: The Innovation Physics (R&D)
*   **Product R&D**: Increases `inventory_quality`.
*   **Process R&D**: Increases `productivity_factor`.
*   **Success**: Probability based on investment relative to revenue.

### Step 3: Employment Strategy
*   **Talent War**: Use high `q_hiring_agg` to offer higher wages and steal high-skill workers.
*   **Layoffs**: Use low `q_hiring_agg` + poor liquidity to trigger layoffs of low-skill workers.

### Step 4: Verification (The Innovation War)
Create `scripts/verify_innovation.py`:
1.  **Scenario**: Compare a `GROWTH_HACKER` firm (aggressive R&D) vs a `BALANCED` firm.
2.  **Expectation**: The aggressive firm should eventually win market share through higher quality or lower costs.


---

## 4. Command Checklist

- [ ] `git pull origin main` (Ensure you have Commit `bdac3b1` or later)
- [ ] Review `design/specs/utility_maximization_spec.md` (Crucial for AI brain upgrade)
- [ ] Implement `DurableAsset` logic in `simulation/core_agents.py`.
- [ ] Update `Household.update_needs()` to handle asset depreciation.
- [ ] Update `Firm.produce()` to calculate and tag product `quality`.

---

## 5. ⚠️ Governance Rules (Read Carefully)

### A. Scope of Responsibility
| Responsibility | Owner |
|---|---|
| **Implementation Success** (No crashes, no `None` values, no `ZeroDivision`) | **Jules** |
| **Logic Correctness** (Does the economy behave as expected?) | **Architect/User** |

### B. Verification Criteria for Jules
Your task is **COMPLETE** when:
1.  ✅ Code runs without errors.
2.  ✅ No `NaN`, `None`, or obviously corrupted data in outputs.
3.  ✅ Unit tests pass (`pytest tests/`).

Your task is **NOT** to verify:
-   ❌ Whether M2 > M0 (Money Multiplier).
-   ❌ Whether agents "make sense" economically.

**Rationale**: If economic behavior is unexpected, it may be a **design flaw (Architect's fault)**, not an implementation bug. Debugging logic without Architect input leads to infinite loops.


---

## 6. Planning Protocol: Parallel Execution Strategy

**To:** All Agents (Architect & Jules)
**Directive:** When converting a High-Level Spec (Plan) into Actionable Steps:

1.  **Decompose for Parallelism**: Break down the Work Order into granular tasks that can be executed in parallel (e.g., Track A, Track B, Track C).
2.  **Verify Independence**: Ensure parallel tracks have minimal dependencies on each other.
3.  **Atomic Verification**: Each parallel track must have its own verifiable output (e.g., a specific unit test or a distinct UI component).
4.  **Exception**: If a task requires an overnight run or deep serialization (e.g., training a model), mark it as a "Long-Running Serial Task".

**Goal**: Maximize throughput by allowing multiple streams of work to proceed simultaneously where possible.
