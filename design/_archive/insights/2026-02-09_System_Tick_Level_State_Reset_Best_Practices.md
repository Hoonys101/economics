# Mission Insight: Firm Reset Logic Fix (FIRM-RESET-FIX)

## 1. Problem Phenomenon
- **Symptom**: `FIRM_RESET_SKIPPED` warnings in simulation logs.
- **Location**: `simulation/orchestration/phases/post_sequence.py`.
- **Cause**: The orchestrator was checking for a `finalize_tick` method on the `firm.finance` property, which did not exist on the `Firm` class (which `firm.finance` proxies to).

## 2. Root Cause Analysis
- The `Firm` class implements a `finance` property that returns `self` for backward compatibility.
- The `post_sequence.py` orchestrator phase attempts to call `firm.finance.finalize_tick(market_context)` to handle end-of-tick cleanup (resetting counters).
- This method was missing from `Firm`, leading to the warning.
- **Deeper Issue**: Financial counters (`expenses_this_tick`) were being reset prematurely in `Firm.generate_transactions` (Phase 4.3), causing data loss for subsequent phases (like `post_sequence` learning updates in Phase 5) that rely on these counters.

## 3. Solution Implementation
- **Firm Class Updates** (`simulation/firms.py`):
    - Added `reset_finance()` method to delegate to `finance_state.reset_tick_counters()`.
    - Added `reset()` method as an alias for `reset_finance()`.
    - **Crucial Fix**: Removed the call to `self.finance_state.reset_tick_counters()` from `generate_transactions()`. This ensures that tick-level financial data persists until the actual end of the tick (Post-Sequence phase).
- **Orchestrator Updates** (`simulation/orchestration/phases/post_sequence.py`):
    - Updated the loop to prioritize calling `f.reset()` if it exists.
    - Maintained legacy check for `finalize_tick` for safety, though `Firm` now uses the new interface.

## 4. Verification
- ran `scripts/trace_leak.py` for 1 tick (sufficient to trigger post-sequence).
- Confirmed `FIRM_RESET_SKIPPED` warnings are absent.
- Confirmed Zero-Sum Integrity passed (`Leak: -0.0000`).

## 5. Lessons Learned & Technical Debt
- **Lesson**: "Reset" logic should always happen at the very end of the lifecycle (Post-Sequence), not during transaction generation, to ensure data availability for analysis/learning phases.
- **Tech Debt**: The `Firm` class is still a "God Object" mixing multiple concerns. The `finance` property returning `self` is a legacy artifact that should eventually be removed in favor of a distinct `FinanceDepartment` component.
- **Insight**: `FinanceEngine` logic for `_process_profit_distribution` also resets some counters (`revenue_this_turn`). This might still cause issues if `post_sequence` relies on `revenue_this_turn`. Future work should verify if `revenue_this_turn` needs to be preserved longer or if `last_revenue` is sufficient.
