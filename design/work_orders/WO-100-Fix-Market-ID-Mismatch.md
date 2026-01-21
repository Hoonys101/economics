# Work Order: WO-100-Fix-Market-ID-Mismatch

## 1. Objective
Resolve the "Zero Transaction" fail state in Phase 23 by ensuring that Households and Firms trade on the exact same Market ID.

## 2. Diagnosis (From WO-099 Analysis)
- **Symptom**: Total Sales Volume is 0.00 despite ample Inventory (~1462) and Cash.
- **Root Cause**: Market ID Mismatch. 
  - Firms typically produce `basic_food`.
  - Households need `survival`.
  - **Hypothesis**: The Household Engine converts `survival` need into a Bid for `food` (generic) or some other ID, while Firms are selling on `basic_food` (specific).

## 3. Tasks

### Task 1: Audit & Fix Household Engine
**Target File**: `simulation/decisions/rule_based_household_engine.py`

**Instructions**:
1. Inspect the logic where `survival` need is converted into a purchase tactic.
2. Check the `item_id` used in `Order` generation.
3. If it is hardcoded as "food" or derived incorrectly, **CHANGE IT TO `basic_food`**.
   - *Note*: Ensure this matches `goods_data` keys used in `EconomyManager`.

### Task 2: Audit Firm Engine (Quick Check)
**Target File**: `simulation/decisions/rule_based_firm_engine.py` (or `ProductionDepartment`)

**Instructions**:
1. Confirm Firms are indeed producing and selling `basic_food`.
2. If they are using a different ID, standardize it to `basic_food`.

### Task 3: Verify Alignment
**Instructions**:
1. Run the refined verification script: `python scripts/verify_phase23_harvest.py`
2. Check `reports/phase23_metrics.csv` (or the console output).
3. **Success Criteria**:
   - `Total Sales` > 0
   - `Food Price` drops below 5.00
   - `Population` grows (no mass starvation)

## 4. Deliverable
- A PR fixing the ID mismatch in `simulation/decisions/rule_based_household_engine.py` (and potentially others).
- Updated verification log proving "ESCAPE VELOCITY ACHIEVED".
