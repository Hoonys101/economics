# Work Order: - Settlement Purity (Phase A: Component Logic)

## 1. Strategy: Divide and Conquer
- **Phase A (Current)**: Refactor internal logic of Managers/Components to use `SettlementSystem`. **DO NOT TOUCH** the `TickScheduler` or execution sequence yet.
- **Phase B (Next)**: Once components are compliant, move their execution to the 'Transactions' phase in `TickScheduler`.

## 2. Phase A Tasks (Component Cleaning)

### Target: Remove "Shadow Logic" (Direct Mutations)
The goal is to replace `agent.assets += value` with `settlement.transfer(source, target, value, description)`.

1. **InheritanceManager (`simulation/systems/inheritance_manager.py`)**:
 - Locate `process_death`.
 - Replace any direct asset modification (e.g., `heir._add_assets`) with `settlement.transfer`.
 - If `settlement` is missing, **LOG ERROR and SKIP** (or use strict failure if stable). Do not keep fallbacks.

2. **MAManager (`simulation/systems/ma_manager.py`)**:
 - Locate `_execute_merger`.
 - Replace `predator.assets -= price` and `founder.assets += price` with `settlement.transfer`.
 - Ensure the transaction type is logged correctly.

3. **FinanceDepartment (`simulation/components/finance_department.py`)**:
 - **Crucial**: Do not change *when* these methods are called, only *how* they transfer money.
 - Refactor `process_profit_distribution` (Dividends & Bailout Repayment).
 - Refactor `distribute_profit_private`.
 - Refactor `pay_severance`.

4. **Bank (`simulation/bank.py`)**:
 - Refactor `check_solvency`. Instead of `self._assets += amount`, use `finance_system.issue_bailout` or verify if `settlement.transfer` can be used from Central Bank.

## 3. Strict Constraints
- **NO SEQ CHANGES**: Do NOT modify `simulation/tick_scheduler.py` in this phase.
- **NO HEADER CHANGES**: Do not change method signatures if possible.

## 4. Verification
- Run `verify_great_reset_stability.py`.
- The "Money Supply Delta" might still be non-zero because of Sequence issues (Phase B), but the *Component* logic must be clean.
