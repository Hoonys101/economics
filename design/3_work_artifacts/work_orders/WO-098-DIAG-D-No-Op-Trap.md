# Diagnostic Work Order: -D (The No-Op Trap)

## 1. Hypothesis
Rule-based households are generating ZERO orders because `DecisionContext.household` is passed as `None` from `core_agents.py`, causing an early return (no-op) in the engine. This makes the "Great Harvest" impossible as households neither work nor eat.

## 2. Verification Steps (FOR JULES)
1. **Insert Diagnostic Log**:
 - Open `simulation/decisions/rule_based_household_engine.py`.
 - At the beginning of `make_decisions(self, context, macro_context)`, add:
 ```python
 if context.household is None:
 self.logger.warning(f"[DIAG-D] No-Op Triggered! Household is None for agent.")
 return [], (None, None)
 ```
2. **Run Mini-Simulation**:
 - Run `python scripts/verify_phase23_harvest.py --ticks 10`.
3. **Analyze Logs**:
 - Check `simulation.log` or console output for the `[DIAG-D]` prefix.
 - Count how many times this occurs per tick.

## 3. Reporting
If the log appears frequently, the hypothesis is **PROVEN**. Do not fix yet; report the result first.
