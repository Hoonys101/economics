# Work Order: Phase 8-B (Economic Reflux System)

> **To**: Jules (Implementation Agent)
> **From**: Antigravity (Team Leader)
> **Priority**: Critical
> **Objective**: Eliminate "Money Leakage" by implementing the Economic Reflux System.

## Context
Firms and Banks currently "destroy" money when paying for non-wage expenses (marketing, fixed costs) or retaining earnings. This causes deflation.
You must implement a `RefluxSystem` that captures these outflows and returns them to Households.

---

## Assignments

### 1. Create `simulation/systems/reflux_system.py`
Implement the class `EconomicRefluxSystem` as defined in `design/specs/phase8b_reflux_system_spec.md`.
- Methods: `__init__`, `capture(amount, source, category)`, `distribute(households)`.

### 2. Update `simulation/engine.py` (Orchestration)
You must explicitly update the Engine to manage this system.

**A. Initialization (`__init__`)**
```python
# Import at top
from simulation.systems.reflux_system import EconomicRefluxSystem

# Inside __init__
self.reflux_system = EconomicRefluxSystem()
```

**B. Injection (`run_tick`) - Bank**
Pass the system to the Bank so it can dump profits.
```python
# Inside run_tick(), finding the Bank update section:
if hasattr(self.bank, "run_tick"):
    if "reflux_system" in self.bank.run_tick.__code__.co_varnames:
        self.bank.run_tick(self.agents, self.time, reflux_system=self.reflux_system)
    else:
        # Fallback if you haven't updated Bank signature yet, but you SHOULD.
        self.bank.run_tick(self.agents, self.time)
```

**C. Injection (`Firm`)**
Firms usually access systems via `self.make_decision` or directly if set.
Ensure Firms have access. You can pass it in `make_decision` or set it during init/loop.
*Recommendation*: In `run_tick`, when iterating firms, you might not need to pass it if you update `Firm` to take it in `update_needs` or similar, OR just pass it where needed.
*Better Strategy*: Firms need to capture expenses *when they happen*. If expenses happen inside `firm.produce()` or `firm.make_decision()`, pass it there.
*Instruction*: Update `Firm.produce` or relevant methods to accept `reflux_system`.

**D. Distribution (End of Tick)**
Crucial! Money must go back to households before the tick ends.
```python
# Inside run_tick(), BEFORE _save_state_to_db and BEFORE final cleanup
# Phase 8-B
self.reflux_system.distribute(self.households)
```

### 3. Update `simulation/firms.py`
Find where money leaves `self.cash` (excluding wages and tax).
- `marketing_invest` (if exists) -> `reflux_system.capture(amount, ...)`
- `maintenance_cost` / `fixed_cost` -> `reflux_system.capture(amount, ...)`
- `expansion_cost` (if exists) -> `reflux_system.capture(amount, ...)`

### 4. Update `simulation/agents/bank.py`
- In `run_tick` or `process_profits`:
- Instead of adding to `self.reserves` (or ignoring net profit), do:
  ```python
  if net_profit > 0:
      reflux_system.capture(net_profit, "Bank", "dividend")
  ```

### 5. Verification (CRITICAL)
Rewrite `tests/verify_economic_equilibrium.py` to perform a **Conservation of Money** test.
**Formula**:
$$TotalMoney = \sum Household_{cash} + \sum Firm_{cash} + Bank_{reserves} + RefluxPool_{balance} + Government_{assets}$$

- Run for 100 ticks.
- Valid if: `TotalMoney` is constant (or increases only by configured Central Bank injections).
- **Fail if**: `TotalMoney` decreases.

---
**Output**: 
1. `modules/system/reflux_system.py`
2. Modified `engine.py`, `firms.py`, `bank.py`
3. Check logs for "Conservation Passed".
