# Execution Insight: Test Regression Fixes

## 1. Architectural Insights

### DTO Purity & Dataclass vs TypedDict Conflict
We encountered a regression where `FiscalEngine` (using `modules.government.engines.api`) was expecting a `TypedDict` style `MarketSnapshotDTO` (supporting subscript access `market["current_gdp"]`), while the core system (represented by `simulation.dtos.api` and `modules.system.api`) had evolved `MarketSnapshotDTO` into a `dataclass`.

The decision was made to **align the Engine with the Core System**, updating `FiscalEngine` to use the `dataclass` definition and dot notation (`market.market_data`). This reinforces the **DTO Purity** guardrail by moving away from loose dictionaries towards structured objects.

This also required updating `Government` agent to construct the correct `MarketSnapshotDTO` dataclass instead of a raw dictionary when invoking the engine, ensuring consistent type contracts across the boundary.

### Mock Discipline & Protocol Fidelity
Several tests failed due to "Mock Drift" where `MagicMock` objects were leaking into arithmetic operations (`<` not supported between `MagicMock` and `float`) or formatting strings. This occurred because the `mock_config` fixture relied on `MagicMock`'s default behavior of returning new mocks for accessed attributes.

To fix this, we enforced stricter mock configuration in tests:
1.  **Explicit Values:** Key configuration parameters (`INCOME_TAX_RATE`, `CB_INFLATION_TARGET`, etc.) are now explicitly set to concrete values (floats/bools) in the `mock_config` fixture.
2.  **Fixture Alignment:** The `test_agent_factory.py` was using a mismatched fixture name (`mock_config_module` vs `mock_config`), which was corrected to use the global `conftest.py` fixture, reducing duplication and setup errors.

### Factory Integrity
The `HouseholdFactory` enforces a strict **Zero-Sum Integrity** policy where it initializes agent assets to 0, expecting the caller (or a settlement system transfer) to fund the agent. The test `test_create_household` was asserting legacy behavior (direct asset injection). We updated the test to verify the `initial_assets_record` in the state DTO instead of the active wallet balance, respecting the factory's design contract.

## 2. Test Evidence

```
tests/simulation/factories/test_agent_factory.py::test_create_household PASSED [ 16%]
tests/simulation/factories/test_agent_factory.py::test_create_newborn
-------------------------------- live log call ---------------------------------
INFO     simulation.factories.household_factory:ai_driven_household_engine.py:43 AIDrivenHouseholdDecisionEngine initialized (Modularized).
PASSED                                                                   [ 33%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_fiscal_engine_taylor_rule PASSED [ 50%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_execution_engine_state_update PASSED [ 66%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_orchestrator_integration
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
-------------------------------- live log call ---------------------------------
INFO     modules.common.utils.shadow_logger:shadow_logger.py:36 ShadowLogger initialized at logs/shadow_hand_stage1.csv
PASSED                                                                   [ 83%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_social_policy_execution
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
PASSED                                                                   [100%]

============================== 6 passed in 0.35s ===============================
```
