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

## 2. Immediate Action Plan (WO-024: Banking)

Do NOT wait for the legacy `verify_wo23.py` simulation to finish. It is running on obsolete logic.
Start implementing the **Fractional Reserve Banking System** immediately on top of the current `main` branch.

### Step 1: Banking Implementation
*   **Reference:** `design/work_orders/WO-024-Interest-Banking.md`
*   **Key Components:**
    *   **Bank Agent**: Implement `CommercialBank` (inheriting from `Firm` or `BaseAgent`).
    *   **Money Creation**: Implement `issue_loan()` which creates deposits (M2 expansion).
    *   **Interest**: Implement `process_interest()` for both deposits (expense) and loans (revenue).

### Step 2: Verification
*   Create `scripts/verify_banking.py`.
*   **Success Metrics:**
    *   **Money Multiplier**: M2 (Broad Money) should be > M0 (Base Money) / Reserve Ratio.
    *   **Solvency**: The Bank should be profitable (Spread > Defaults).

---

## 3. Command Checklist

- [ ] `git pull origin main` (Ensure you have Commit `9ea5f0a` or later)
- [ ] Review `simulation/core_agents.py` (Search for `_update_skill`)
- [ ] Review `simulation/firms.py` (Search for `pay_wages` logic)
- [ ] Begin coding `simulation/agents/bank.py` per WO-024.

**Execute.**
