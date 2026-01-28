# W-2 Implementation Spec: Systemic Stabilization

Jules, you are assigned to fix critical system failures. Follow the instructions below precisely.

## 1. Stabilization Tasks

### Task 1: Fix Money Leak (WO-056)
**Target:** `simulation/systems/housing_system.py`, `simulation/systems/reflux_system.py`
**Logic:**
- In `housing_system.py`: Within `process_transaction`, check if `isinstance(seller, Government)`.
- If true, call `seller.collect_tax(trade_value, "housing_sale", buyer.id, simulation.time)`. This ensures money leaving M1 is recorded as "withdrawn" in the Government's ledger.
- In `reflux_system.py`: Change `self.balance = 0.0` at the end of `distribute` to `self.balance -= (amount_per_household * len(active_households))` to preserve the remainder.

### Task 2: Inventory Glut Safeguard (WO-058.1)
**Target:** `simulation/firms.py`, `simulation/decisions/ai_driven_firm_engine.py`
**Logic:**
- In `firms.py`:
  - Implement `get_optimal_inventory_level()`: returns `max(10.0, self.finance.last_sales_volume * 10.0)`.
  - In `produce()`, if `planned_quantity + current_stock > 2.0 * optimal_level`, cap `planned_quantity` to the allowed space.
- In `ai_driven_firm_engine.py`: 
  - In `make_decisions`, calculate `inventory_pressure = current_stock / optimal_level`.
  - If `pressure > 3.0`, force `production_target = 0` (Heuristic Override).

### Task 3: Test Stability
**Target:** `scripts/iron_test.py`
**Logic:**
- Cache `initial_hh_count` and `initial_firm_count` after simulation initialization.
- Use these variables as denominators in the final report to prevent `ZeroDivisionError` on extinction.

## 2. Verification Requirements
- Create `tests/test_money_integrity.py` simulating a housing sale.
- Run `pytest` on all modified modules.
- Run `python scripts/iron_test.py --ticks 100` and confirm **PASS** (or non-crash failure due to economic reasons).

## 3. Data Promotion
- Save the `reports/iron_test_phase21_result.md` as a Golden Sample.
