# WO-116: Third Hunt (Final Boss) - Plugging the 700k Hole

## 1. Status Update
Jules' Second Hunt discovered the "Debt Shadow" (Bank write-offs). Excellent. However, even with the expanded M2 formula (including Gov, Bank, Write-offs, CB Cash), a ~700k leak persists starting from Tick 1.

## 2. Target Areas for Third Hunt

### A. Central Bank & Government Deficit Accounting
- **Hypothesis**: The Government/CB assets can go negative. When they do, does the M2 calculation in `WorldState.calculate_total_money` and `verify_great_reset_stability.py` treat negative values correctly?
- **Action**: Check if `max(0, assets)` is being used anywhere, which would hide a 700k deficit, making it look like a leak.

### B. The "Tick 1" Phantom Leak
- **Observation**: The leak jump-starts at Tick 1.
- **Action**: Use a debugger or print statements to check EVERY transaction in Tick 1. Identify which transaction reduces a buyer's assets without a matching increase in any of the M2 buckets (H, F, Gov, Bank, Reflux, Write-offs, CB Cash).

### C. Bond Crowding Out
- **Hypothesis**: When `FinanceSystem.issue_treasury_bonds` is called, money moves. If the buyer is a "Commercial Bank", its reserves drop. If the Government doesn't increase its assets at the exact same time (due to batchিং), money disappears for a tick.
- **Action**: Ensure Bond issuance is atomic and synchronized between Bank and Gov assets.

## 3. Mandatory Reporting
Provide a final report on:
1. **The 700k Culprit**: Exact file and line that caused the massive drift.
2. **Accounting Neutrality**: Confirmation that Bond issuance and Money printing are now 100% zero-sum in the tracker.
3. **Solved Problems**: Final list of patches.
