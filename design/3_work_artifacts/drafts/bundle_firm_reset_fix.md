# Mission Guide: Firm Reset Logic Fix (FIRM-RESET-FIX)

## 1. Objective
Resolve `FIRM_RESET_SKIPPED` warnings by implementing a proper financial reset mechanism in the `Firm` class that bridges the legacy orchestrator call with the new `FinanceEngine`/`FinanceState` architecture.

## 2. Reference Context
- **Analysis Report**: [report_20260209_203200_Analyze_trace_leak_p.md](file:///c:/coding/economics/reports/temp/report_20260209_203200_Analyze_trace_leak_p.md)
- **Target File**: [firms.py](file:///c:/coding/economics/simulation/firms.py)

## 3. Implementation Steps

### Step 1: Implement `reset_finance` in `Firm`
The simulation orchestrator (specifically `post_sequence`) expects a way to reset the firm's financial counters at the end of a tick. Currently, it's failing to find a compatible method.

**Action**: Add the following method to the `Firm` class in `simulation/firms.py`. This method should delegate to the `FinanceState`'s reset logic.

```python
    def reset_finance(self) -> None:
        """
        Resets the financial state for the next tick.
        This is called by the simulation orchestrator's post-processing phase.
        """
        if hasattr(self, 'finance_state'):
            # Assuming DEFAULT_CURRENCY is 'USD', or import it if needed
            self.finance_state.reset_tick_counters('USD') 
```

### Step 2: Verify `finance` Proxy
Ensure the `finance` property proxy added in the previous mission points to an object that exposes this `reset_finance` (if the orchestrator calls `firm.finance.reset()`) OR ensure the orchestrator calls `firm.reset_finance()`.

*Self-Correction*: The log says `FIRM_RESET_SKIPPED`. This warning likely comes from `simulation/orchestration/phases/post_sequence.py`. It's safer to align the `Firm` class with what the orchestrator expects.

If the orchestrator calls `firm.finance.reset()`, then the `finance` property (which returns `self`) works IF `self` has a `reset()` method.

**Refined Action**: 
1. Add a `reset()` method to `Firm` that aliases `reset_finance()`.
2. Ensure `reset_finance()` correctly resets the `finance_state`.

## 4. Verification
Run `trace_leak.py` for 50 ticks and ensure:
1. `FIRM_RESET_SKIPPED` warnings disappear from the logs.
2. Zero-sum integrity remains intact.
