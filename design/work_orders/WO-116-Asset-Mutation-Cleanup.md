# Work Order: WO-116 - Plugging Money Leaks (Settlement Purity)

## 1. Context
- **Objective**: STOP the "Money Escape" by ensuring 100% compliance with the `SettlementSystem`.
- **Primary Issue**: Managed systems (Inheritance, M&A, FinanceDept) are bypassing the accounting system via direct `_assets` mutations, causing zero-sum violations.

## 2. Tasks for Jules (STRICT PRIORITY: LEAK PREVENTION)

### A. Managed System Refactor (Stop the Leak)
1. **InheritanceManager (`simulation/systems/inheritance_manager.py`)**: 
   - Refactor `process_death` to use `SettlementSystem.transfer` for EVERYTHING.
   - Remove ALL legacy `_add_assets` / `_sub_assets` fallbacks.
   - **Pattern**: `deceased._sub_assets(amount)` -> `settlement.transfer(deceased, heir, amount, "inheritance")`.
2. **MAManager (`simulation/systems/ma_manager.py`)**: 
   - Refactor merger payments and bankruptcy liquidations to use `SettlementSystem.transfer`.
   - **Pattern**: `predator.assets -= price` -> `settlement.transfer(predator, target_shares_proxy, price, "merger")`.
3. **FinanceDepartment (`simulation/components/finance_department.py`)**: 
   - Replace direct mutations in `process_profit_distribution`, `distribute_profit_private`, and `pay_severance` with `SettlementSystem.transfer`.

### B. Tick Sequence Normalization (Ensure Accountability)
1. **TickScheduler (`simulation/tick_scheduler.py`)**:
   - The audit shows that **Profit/Tax/Welfare** transfers happen outside the transaction phase, causing statistical leakage.
   - Fix the sequence so ANY asset movement uses `SettlementSystem` and is captured during or registered for the Transactions phase.
2. **Bank (`simulation/bank.py`)**:
   - Fix `check_solvency` to use the government's `FinanceSystem` (which uses Settlement) instead of direct `_assets` increment.

### C. Decision Engine Purity
1. **AIDrivenHouseholdDecisionEngine**: Review and remove any direct asset modifications during decision making.
   - **Note**: Look for `household.assets -= repay_amount` patterns even if they are temporary.

### D. Structural Debt (TODO / PHASE 2)
1. **God Class Splitting**: 
   - (Lower Priority) Split `Household` from `core_agents.py` once leaks are plugged.
   - (Lower Priority) Remove Leaky Abstractions in `HRDepartment`.

## 3. Verification (CRITICAL)
- **Zero-Sum Check**: Run `verify_great_reset_stability.py`. The `MONEY_SUPPLY_CHECK` delta MUST be near zero.
- **Fail Policy**: If `SettlementSystem` is missing, log a CRITICAL error and halt. DO NOT use fallbacks.

## 4. Reporting Requirement
- List every file where "Shadow Logic" (direct mutation) was removed.
- Confirm total money supply delta after fixes.
