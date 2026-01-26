# WO-121: Newborn Initialization Fix & Feedback Integration

**Date:** 2026-05-25 (Simulation Time)
**Author:** Jules
**Status:** Completed

## 1. Summary of Changes

To address the "Dead on Arrival" newborn agent issue, we have:
1.  **Configuration Centralization**: Externalized `NEWBORN_INITIAL_NEEDS` to `config/economy_params.yaml`. This allows tuning of newborn motivation without code changes.
2.  **Logic Update**: Refactored `DemographicManager.process_births` to inject these configured needs into new `Household` agents, replacing the empty default.
3.  **Documentation**: Added the "Principle: All Agents are Born with Purpose" to `AGENTS.md` to codify this architectural decision.
4.  **Test Coverage**: Created `tests/systems/test_demographic_manager_newborn.py` to verify the fix in isolation.

## 2. Technical Insights & Challenges

### Mocking the Simulation "God Object"
The `DemographicManager` is tightly coupled to the `Simulation` object, which made unit testing challenging. To test `process_births` in isolation, we had to mock:
-   `simulation.next_agent_id`
-   `simulation.time`
-   `simulation.logger`
-   `simulation.ai_trainer` (and its `get_engine` method)
-   `simulation.markets` (specifically `loan_market`)
-   `simulation.goods_data`
-   `simulation.ai_training_manager` (as a class property)

This confirms the high coupling risk identified in the audit. Future refactoring should consider injecting specific services (e.g., `IAITrainer`, `IMarketProvider`) instead of the entire `simulation` object.

### Test Fixture Fragility
We encountered an `AttributeError` in `SocialComponent` because the test fixture provided a string `"STABLE"` for personality, while the component expected a `Personality` Enum member. This highlights the importance of using typed Enums in test fixtures to match the strict typing of the codebase.

### Regression in `verify_mitosis.py`
While validating changes, we discovered that `tests/verification/verify_mitosis.py` was broken due to a recent refactor of the `Household` class (delegating assets to `EconComponent`). The test was attempting to modify `parent._assets` directly, which no longer affected the actual assets. We fixed this by targeting `parent.econ_component._assets`, ensuring the regression suite is green.

## 3. Conclusion
The fix is robust and verified. The newborn agents now start with intrinsic motivation (needs), preventing them from being culled due to inactivity. The testing ecosystem is slightly cleaner with the new isolated test, though the `Simulation` dependency remains a long-term architectural concern.
