# Second Hunt for Money Leaks (2차 사냥)

## 1. Objectives
Plugging the remaining Money Supply leaks after the initial limited merge. The goal is to investigate deeper structural issues and verify specific hypotheses.

## 2. Hypotheses to Verify

### Hypothesis A: The Deficit Trap (Negative Government Assets)
- **Problem**: When the government runs a deficit (assets < 0), how is this handled in the M2 calculation? 
- **Check**: Audit `verify_great_reset_stability.py` and `diagnose_money_leak.py`. If $M2 = \sum Assets$, and government assets are negative, is this correctly subtracting from M2, or is there a floor at zero that hides the deficit?
- **Action**: Fix accounting if a discrepancy exists.

### Hypothesis B: Debt Shadow (Inactive Agent Debt)
- **Problem**: When a firm or household dies/bankrupts, their debt to the bank is "forgiven" or "written off".
- **Check**: Does the bank correctly subtract this written-off debt from its own internal ledger/valuation? If the debt is erased for the borrower but persists as a "nominal asset" for the bank, M2 will drift.
- **Action**: Ensure bank reserves/assets are adjusted when debt is written off in `InheritanceManager` or `LifecycleManager`.

### Hypothesis C: Incomplete Liquidation
- **Problem**: In `AgentLifecycleManager._handle_agent_liquidation`, some assets might be cleared (`inventory.clear()`) without recording them as a loss or transfer.
- **Check**: Even if cash is transferred, do inventory/capital stock valuations vanishing cause a drop in "Total Assets" (M2) that isn't balanced?
- **Action**: Ensure all vanished assets are captured by `RefluxSystem` or accounted for.

## 3. Reporting Requirements
Jules must provide a technical summary of:
1. **Hypothesis Verification**: For each hypothesis (A, B, C), was it confirmed as a leak source?
2. **New Broad Hypotheses**: Any other leak sources found (e.g., rounding errors in interest, uncaptured fees).
3. **Solved Problems**: List of fixes applied during the Second Hunt.
