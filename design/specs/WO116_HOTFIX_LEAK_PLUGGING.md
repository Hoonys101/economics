# WO-116 Phase B Hotfix: Plugging the -750k Money Leak

## 1. Context
During the initial verification of WO-116 Phase B, a massive money supply drift of approx. **-749,990.04** was detected. This indicates structural leaks where money is being withdrawn from one agent but not deposited into another, or vanishing during agent liquidation.

## 2. Identified Bugs (To be fixed by Jules)

### A. Transaction Direction Reversal
Multiple system-generated transactions have `buyer_id` (payer) and `seller_id` (payee) swapped:
- [ ] `simulation/components/finance_department.py`: `process_profit_distribution` (Dividend) - Currently makes Households pay Firms. **Swap them.**
- [X] `simulation/bank.py`: `reflux_capture` - Fixed by Gemini, verify again.
- [X] `simulation/agents/government.py`: `infrastructure_investment` - Fixed by Gemini, verify again.
- [ ] **Scan all other `Transaction(...)` calls** in the codebase to ensure `buyer` is ALWAYS the one losing money.

### B. Liquidation Zero-Sum Integrity
- [ ] `simulation/systems/lifecycle_manager.py`: The `_handle_agent_liquidation` method still uses `_add_assets` and `_sub_assets`. This logic needs to be converted to use the `SettlementSystem` or ensure that its direct mutations are accounted for in M2.
- [ ] Check if `InheritanceManager.process_death` completes all transfers before the agent is removed from the `sim.households` list. If an agent is removed mid-transaction, the money might vanish.

### C. Settlement Integrity check
- [ ] Audit `TransactionProcessor` (usually in `simulation/action_processor.py` or `simulation/systems/transaction_processor.py`):
    - When a transaction fails (e.g., buyer has no money), does it log a leak?
    - Is there any `try-except` block where `withdraw()` succeeds but `deposit()` is skipped?

## 3. Mission Goal & Reporting
1. Fix all identified direction reversals.
2. Run `python scripts/diagnose_money_leak.py` to verify immediate impact.
3. **Mandatory Report**: Jules must provide a summary in its final report covering:
    - **Rejected Hypotheses**: Which suspected areas were found to be clean and NOT the cause of the leak?
    - **New Hypotheses**: What deeper structural issues were uncovered during the hunt?
    - **Solved Problems**: Detailed list of fixed bugs and their estimated impact on money supply integrity.
