# WO-109: Phase 23 "The Great Harvest" Verification Report

**Date**: 2026-01-22
**Priority**: HIGH
**Status**: FAILED

---

## 1. Executive Summary

**Verdict**: **FAIL**

The simulation failed to meet the "Malthusian Escape" criteria. Instead of a population boom and price drop, the economy suffered a complete collapse characterized by zero production, mass starvation, and firm inactivity.

| Metric | Initial | Final | Result | Pass Criteria | Pass |
|---|---|---|---|---|---|
| **Food Price** | 3.50 | 3.50 | 0% Drop | >= 50% Drop | ❌ FAIL |
| **Population** | 54 | 19 | -65% (Collapse) | >= 2.0x Growth | ❌ FAIL |
| **Engel Coeff** | 1.00 | 1.00 | 1.00 | < 0.50 | ❌ FAIL |

---

## 2. Detailed Analysis

### 2.1. Symptom: The Silent Factory
Analysis of `harvest_data.csv` reveals a critical sequence of events:
1.  **Tick 0-20**: Firms produce once, sell their initial inventory, and then production drops to **0**.
2.  **Tick 20-40**: Inventory depletes to 0.
3.  **Tick 40+**: Firms remain "Active" (technically) but produce nothing and sell nothing.
4.  **Tick 40-500**: Households, unable to buy food (due to 0 supply), starve to death. Population crashes from 54 to 19.

### 2.2. Root Cause: Mutually Exclusive Logic in Decision Engine
The root cause is a **logic bug** in `simulation/decisions/standalone_rule_based_firm_engine.py`.

The `make_decisions` method treats "Adjusting Production Target" and "Hiring Labor" as mutually exclusive tactics:

```python
# simulation/decisions/standalone_rule_based_firm_engine.py

# 1. Decide to change target (Triggered when inventory is low/high)
if current_inventory < target_quantity * UNDERSTOCK_THRESHOLD:
    chosen_tactic = Tactic.ADJUST_PRODUCTION
    # ... modifies firm.production_target ...

# 2. Decide to hire (ONLY if tactic is NOT ADJUST_PRODUCTION)
if chosen_tactic != Tactic.ADJUST_PRODUCTION:  # <--- BUG
    if employees < needed_labor:
        # ... generates BUY labor orders ...
```

**Mechanism of Failure:**
1.  Firms sell out their inventory (Inventory -> 0).
2.  The "Understocked" condition triggers (0 < Target).
3.  Engine selects `Tactic.ADJUST_PRODUCTION` and increases the production target.
4.  Because `chosen_tactic` is now `ADJUST_PRODUCTION`, the engine **skips** the `ADJUST_WAGES` block.
5.  No "BUY labor" orders are generated.
6.  Firms have 0 employees (or lose them over time) and never hire new ones.
7.  Production remains 0 despite the high target.
8.  The cycle repeats infinitely: Firm sees low inventory -> Increases Target -> Forgets to Hire -> Produces Nothing -> Inventory stays low.

### 2.3. Secondary Issue: Price Stagnation
Because no production occurred, supply was zero. The market logic simply reported the last known price or the `MIN_SELL_PRICE` (3.50). No competitive pressure existed to drive prices down, as there were no sellers.

---

## 3. Recommendations

### 3.1. Immediate Fix
Refactor `StandaloneRuleBasedFirmDecisionEngine` to allow sequential execution of logic:
1.  **Step 1: Target Adjustment**: Adjust production targets based on inventory.
2.  **Step 2: Resource Acquisition**: Calculate needed labor for the *current* (potentially updated) target and issue "BUY labor" orders if necessary.
3.  **Step 3: Sales**: Issue "SELL goods" orders if inventory exists.

**Proposed Code Structure:**
```python
# 1. Production Target Logic
if overstocked: decrease_target()
elif understocked: increase_target()

# 2. Hiring Logic (Run ALWAYS)
if employees < needed_for_target:
    issue_buy_labor_order()

# 3. Selling Logic (Run ALWAYS)
if inventory > 0:
    issue_sell_goods_order()
```

### 3.2. Verification
After applying the fix, re-run `scripts/verify_phase23_harvest.py`. We expect:
-   Firms to hire labor to meet their high production targets.
-   Production to surge.
-   Supply glut to drive prices down.
-   Population to grow due to cheap food.

---

**Signed**,
*Jules (AI Architect)*
