# WO-098-DIAG-A: Labor Market Deadlock Investigation (Household Side)

**Objective**: Verify if households are failing to supply labor during survival crises due to sequential decision logic.

**Hypothesis**: 
In `RuleBasedHouseholdDecisionEngine.py`, if a household decides to `BUY_BASIC_FOOD` (even if they have no money), the logic skips the `PARTICIPATE_LABOR_MARKET` step because `chosen_tactic` is no longer `NO_ACTION`.

**Tasks**:
1. **Analysis**: Inspect `simulation/decisions/rule_based_household_engine.py` line 110.
2. **Experiment**: Create a script `scripts/diag_labor_deadlock.py`. 
   - Mock a household with 0 Assets, 0 Food, and 80 Survival Need.
   - Run `make_decisions` and log if a `SELL labor` order is generated.
3. **Report**: Document if the deadlock exists.
