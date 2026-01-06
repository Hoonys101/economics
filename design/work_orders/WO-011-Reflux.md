# Work Order: Phase 8-B (Economic Reflux System)

> **To**: Jules (Implementation Agent)
> **From**: Antigravity (Team Leader)
> **Priority**: High (Critical for system stability)

## Context
We are implementing the **Economic Reflux System** to fix a critical "money leakage" bug where Firm expenses and Bank profits were vanishing from the economy. This caused deflationary spirals.

## Assignments

### 1. Create `simulation/systems/reflux_system.py`
- Implement the `EconomicRefluxSystem` class as defined in `design/specs/phase8b_reflux_system_spec.md`.
- Ensure it has methods `capture(amount, source, category)` and `distribute(households)`.

### 2. Update `simulation/firms.py`
- Modify `Firm` methods to accept `reflux_system` (preferably passed in `update()` or initialized if singleton).
- **CRITICAL**: Locate all lines where `self.cash` is decreased for non-wage reasons (marketing, maintenance, expansion).
- Replace direct deduction with:
  ```python
  self.cash -= cost
  reflux_system.capture(cost, self.id, 'category')
  ```

### 3. Update `simulation/agents/bank.py`
- Modify `Bank` to capture its `net_profit` into the reflux system instead of retaining it.
- Ensure `reflux_system.capture()` is called at the end of the bank's cycle.

### 4. Update `simulation/engine.py` (Orchestration)
- Initialize `EconomicRefluxSystem` in `__init__`.
- Pass it to agents during their `update` loop.
- Call `reflux_system.distribute(self.households)` at the end of the tick (before data recording).

### 5. Verification
- Run `tests/verify_economic_equilibrium.py` (or create a new test `tests/verify_reflux.py`).
- Limit: Ensure Total Money Supply does not decrease over 100 ticks.

## Resources
- `design/specs/phase8b_reflux_system_spec.md` (Detailed Logic)
