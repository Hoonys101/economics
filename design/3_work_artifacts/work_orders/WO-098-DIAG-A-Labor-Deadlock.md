# WO-098-DIAG-A: Labor Market Deadlock Investigation (Household Side)

**Objective**: Verify if households are failing to supply labor during survival crises due to sequential decision logic.

**Hypothesis**: 
In `RuleBasedHouseholdDecisionEngine.py`, if a household decides to `BUY_BASIC_FOOD` (even if they have no money), the logic skips the `PARTICIPATE_LABOR_MARKET` step because `chosen_tactic` is no longer `NO_ACTION`.

**Tasks**:
1. [x] **Analysis**: Inspect `simulation/decisions/rule_based_household_engine.py` line 110.
   - **Finding**: The code sets `chosen_tactic = Tactic.BUY_BASIC_FOOD` *before* checking if the household can actually afford any food.
   - Later, the labor market logic checks `if chosen_tactic == Tactic.NO_ACTION`. Since the tactic is already set to `BUY_BASIC_FOOD`, the labor logic is skipped.
   - If the household has 0 assets, `quantity_to_buy` is 0, so no `BUY` order is created.
   - Result: No Food Bought, No Labor Sold. Infinite Loop of Poverty.

2. [x] **Experiment**: Create a script `scripts/diag_labor_deadlock.py`.
   - Mock a household with 0 Assets, 0 Food, and 80 Survival Need.
   - Run `make_decisions` and log if a `SELL labor` order is generated.
   - **Result**:
     ```
     Running Labor Deadlock Experiment...
     Chosen Tactic: Tactic.BUY_BASIC_FOOD
     Orders generated: 0
     DEADLOCK CONFIRMED: Household tried to buy food (failed due to 0 assets) and skipped labor market.
     ```

3. [x] **Report**: Document if the deadlock exists.
   - **Status**: **CONFIRMED**.
   - **Root Cause**: Premature assignment of `chosen_tactic` in `RuleBasedHouseholdDecisionEngine` and strict mutual exclusivity between buying food and selling labor.
   - **Proposed Fix**:
     - Allow Labor Participation even if `chosen_tactic` is `BUY_BASIC_FOOD` (if `is_employed` is False).
     - Or, only set `chosen_tactic` if an order is actually generated.
     - Better yet: Allow multiple tactics (e.g., Buy Food AND Sell Labor). For rule-based, we can just remove the `if chosen_tactic == Tactic.NO_ACTION` check for the labor block, or modify it to allow labor if the previous tactic failed to produce results, or just allow both.
     - **Selected Fix Strategy**: Remove the `if chosen_tactic == Tactic.NO_ACTION` restriction for Labor Participation. A household should *always* try to work if unemployed and poor, regardless of whether they are also buying food. Buying food consumes assets; selling labor generates assets. They are complementary, not mutually exclusive.
