# MISSION: Loop 3 (Credit Creation Integrity)

## 1. STATUS MONITOR
- **Loop 1 (Tick 1 Fixed)**: ✅ Done.
- **Loop 2 (Defaults & Tax)**: ✅ Merged. Static analysis confirms fixes.
- **Current Suspect**: The **-680k Drift** (or hidden Positive Drift masking it) is linked to **Untracked Credit Creation**.

## 2. GOALS (Loop 3)
1. **Patch `Bank.grant_loan`**:
 - Locate the "Fractional Reserve / Credit Creation" logic (where loan amount > bank assets).
 - **Action**: When credit is created, you MUST increment `government.total_money_issued` by the created amount.
 - **Reason**: The M2 tracker definition includes Bank Assets. When you lend newly created money, Total Assets increase. If `Issuance` doesn't increase, it looks like a leak (or anti-leak). We need balance.
2. **Verify Zero-Sum**:
 - After patching, run `diagnose_money_leak.py` for 500+ ticks.
 - Confirm that the cumulative leak stays near 0.0.

## 3. MANDATORY: Insight Reporting
- If you find that adding issuance fixes the drift, report it.
- If the drift persists even after this patch, list the next suspect (e.g. Interest calculation rounding).

## 4. SUCCESS CRITERIA
- `scripts/diagnose_money_leak.py` output shows minimal drift over long ticks.
- PR created with the Credit Creation patch.
