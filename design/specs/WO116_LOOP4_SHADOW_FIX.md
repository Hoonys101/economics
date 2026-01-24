# MISSION: WO-116 Loop 4 (Erasing Shadow Mutations)

## 1. SITUATION
- Our forensic tool (Loop 3.5) proves that **massive leaks** occur when Transactions are zero.
- This confirms that "Shadow Mutations" (direct property access) are bypassing the ledger.
- We have identified 5 major suspect files using grep.

## 2. GOAL: Enforce Ledger Purity
You must refactor the following files to ensure **every single asset change** is either a `SettlementSystem.transfer` or is tracked via `total_money_issued/destroyed`.

### Target Files & Tasks:
1. **`simulation/systems/lifecycle_manager.py`**:
   - Locate `_add_assets` and `_sub_assets` calls in `_handle_agent_liquidation`.
   - Ensure liquidation distributions to shareholders use `SettlementSystem.transfer`.
2. **`simulation/systems/inheritance_manager.py`**:
   - Audit all `_add_assets` calls during estate distribution. Replace with `SettlementSystem`.
3. **`simulation/bank.py`**:
   - Review `process_default` and `grant_loan`. Ensure every "creation" or "forgiveness" event is perfectly balanced with Government counters.
4. **`simulation/agents/government.py`**:
   - Ensure the internal `_assets` management doesn't leak during treasury operations.
5. **`simulation/base_agent.py`**:
   - Verify if these methods should be `protected` or if we can add a "Safety Toggle" that throws an error if called outside a system context.

## 3. MANDATORY: Forensic Proof
- After refactoring, run `scripts/diagnose_money_leak.py`.
- **Target**: Tick 1 "Unexplained (Leak)" must be **0.0000**.
- If it's not zero, you haven't found all the ghosts yet. Check the "Standardized Forensic Output" you built in Loop 3.5.

## 4. SUCCESS CRITERIA
- Zero drift in Tick 1-10.
- All 5 files refactored to use the ledger.
