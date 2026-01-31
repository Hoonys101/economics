# Technical Specification: Economic CPR

## 1. Objective
Revive `total_production` > 0 by resolving the "Zero Production" deadlock.
The diagnosis points to **Labor (L=0)** or **Inputs (Supply=0)**.

## 2. Diagnosis Plan (Script: `scripts/diagnose_deadlock.py`)
Jules must implement a specific diagnosis script to confirm the root cause.

```python
# Pseudo-code for diagnosis
def diagnose():
 for firm in firms:
 # Check L (Labor)
 num_employees = len(firm.employees)
 labor_skill = firm.hr.get_total_labor_skill()

 # Check K (Liquidity)
 cash = firm.assets

 # Check Inputs
 inputs_needed = firm.config.BROKEN_DOWN_INPUTS
 input_status = {k: firm.input_inventory.get(k, 0) for k in inputs_needed}

 print(f"Firm {firm.id}: Empl={num_employees}, Skill={labor_skill}, Cash={cash}, Inputs={input_status}")
```

## 3. Fix Design: The Bootstrapping Patch
We cannot rely on "Natural Market Forces" to start a dead engine. We need a **Starter Motor** (Initialization Injection).

### A. Initial Inventory Injection (Supply Side)
Modify `simulation/engine.py` -> `__init__` or `Firm.__init__`.
**Requirement:** All firms must start with enough `input_inventory` to run for at least 30 ticks (1 month) without buying.

```python
# simulation/firms.py (Pseudo-code)
def __init__(...):
 # ...
 # Bootstrap Inputs
 if self.specialization in GOODS_CONFIG:
 required_inputs = GOODS_CONFIG[self.specialization].inputs
 for mat_name, qty in required_inputs.items():
 self.input_inventory[mat_name] = qty * 30.0 * self.production_target
```

### B. Initial Labor Liquidity (Demand Side)
Ensure `INITIAL_FIRM_CAPITAL` is sufficient to pay `MIN_WAGE * 5 Employees * 30 Ticks`.
* Current: 30,000.
* Wage: ~10.0 (reservation).
* Cost: 10 * 5 * 30 = 1,500. (Current capital seems sufficient, so L=0 is likely due to Matching or Low Offer).

## 4. Verification Plan (`tests/test_wo058_production.py`)
1. **Mock Simulation**: Init Engine.
2. **Assert**: `sum(f.current_production for f in engine.firms) > 100`.
3. **Assert**: `engine.tracker.latest_indicators['gdp_growth']` is valid.

## 5. Review Criteria (Zero-Question Test)
- [ ] Does the `Diagnosis` script cover all 3 suspects? Yes.
- [ ] Does the `Fix` cover the deadlock (Input=0)? Yes.
- [ ] Is the code location clear? (`simulation/firms.py`, `simulation/engine.py`).
- [ ] Are parameter values specified? (30 ticks buffer).

READY FOR JULES IMPLEMENTATION.
