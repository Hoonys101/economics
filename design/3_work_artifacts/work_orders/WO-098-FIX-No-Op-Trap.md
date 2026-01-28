# Work Order: WO-098-FIX-No-Op-Trap

## 1. Objective
Restore functionality to the `RuleBasedHouseholdDecisionEngine` by ensuring `DecisionContext` receives the `household` instance. This resolves the "No-Op Trap" where households were neither working nor eating.

## 2. Implementation Instructions
**Target File**: `simulation/core_agents.py`

**Change**:
- Locate the `make_decision` method in the `Household` class.
- Find where `DecisionContext` is instantiated.
- Change `household=None` to `household=self`.
- Keep `context.state = state_dto` as it is useful for future migration, but ensure `household=self` restores immediate functionality.

**Diff Spec**:
```python
# Before
context = DecisionContext(
    household=None, # Deprecated/Removed dependency
    markets=markets,
    ...
)

# After
context = DecisionContext(
    household=self, # COMPATIBILITY RESTORED: Required for RuleBasedHouseholdDecisionEngine
    markets=markets,
    ...
)
```

## 3. Verification
1. Run `python scripts/verify_phase23_harvest.py --ticks 50`.
2. Ensure log NO LONGER shows `[DIAG-D] No-Op Triggered!`.
3. Verify that `Order` objects are being generated (check logs for `Household ... offers labor` or `BUY`).
4. **Remove the diagnostic log** added in WO-098-DIAG-D from `rule_based_household_engine.py` before committing.

## 4. Success Criteria
- [ ] Households generate BUY/SELL orders.
- [ ] Simulation runs without "No-Op" warnings.
