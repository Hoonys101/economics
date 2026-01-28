# MISSION: WO-116 Loop 2 (Hunting the 680k Late-Stage Leak)

## 1. STATUS MONITOR
- **Loop 1 SUCCESSFUL**: Tick 1 is now clean (0.000 leak). Education budget and Firm spawning fixes are merged into `main`.
- **Remaining Boss**: **-680,000 M2 Drift** by Tick 1000.

## 2. GOALS (Loop 2)
1. **Investigate TD-114 (Bank Defaults)**: Audit `Bank.process_default`. When a loan is written off, the bank loses assets.
   - **Problem**: This asset loss must be recorded as `total_money_destroyed` in Government stats to keep the M2 tracker neutral.
   - **Action**: Patch the Bank default logic so every write-off is mirrored in the Government's money destruction trackers.
2. **Scan for "Ghost Sinks"**: Identify any other place where `_sub_assets` is called without a matching `_add_assets` or `record_revenue/destroy`.
3. **Verify Late-Stage Stability**: Run `scripts/diagnose_money_leak.py` for 100+ ticks.

## 3. MANDATORY: Insight & Culprit Reporting (Constitution Rule #6)
You are the detective on the ground.
**Requirement**: You MUST record any anomalies found in `Bank.py` or `CentralBank.py` regarding asset disappearance.
- Report these in your **Commit Messages** or a **Summary Report** in your final response.
- Even if you find multiple smaller leaks (interest rounding, etc.), list them with estimated impact.

## 4. SUCCESS CRITERIA
- `scripts/diagnose_money_leak.py` shows **Leak: < 10.0** at Tick 100.
- Provide a clear explanation of why the -680k was occurring.
