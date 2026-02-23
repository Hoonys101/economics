# Insight Report: Wave 5 Government AI Specification
**Mission Key:** MISSION_impl_wave5_gov_ai
**Date:** 2026-02-23
**Author:** Jules (Software Engineer)

## 1. Architectural Insights & Technical Debt

### 1.1. Q-Table Versioning Strategy (Critical)
- **Risk**: The current `GovernmentAI` uses a fixed 4-tuple state space (Inflation, Unemployment, GDP, Debt). Adding 'Approval' and 'Lobbying' changes this to a 6-tuple. Loading an old `.pkl` file will cause a `ValueError` during the `state` lookup or table update.
- **Decision**: The Specification mandates a **Versioned Filename Strategy**. The AI will look for `q_table_v5_populist.pkl`. If not found, it will initialize a fresh table. This avoids breaking existing V4 simulations while enabling V5 features.
- **Future Debt**: We are accumulating multiple Q-tables. A "Migration Utility" might be needed in Wave 6 to transfer knowledge (e.g., macro-stability instincts) from V4 to V5 tables, rather than learning from scratch.

### 1.2. The "Reflex vs. Populism" Conflict
- **Analysis**: The existing `SmartLeviathanPolicy` has a hardcoded `REFLEX_OVERRIDE` that forces Hawkish action if inflation is high. This is a "Technocratic" safety rail.
- **Resolution**: In a "Populist" simulation, this hard override is a bug. A populist government *might* choose to ignore inflation if their base (Debtors) benefits from it.
- **Design Change**: The Spec downgrades `REFLEX_OVERRIDE` to a "Constitutional Constraint" that is **disabled** if `Government.is_populist_mode` is True. The AI must *learn* to fight inflation via the Reward Function (which penalizes economic collapse) rather than being forced to.

### 1.3. Reward Signal Continuity
- **Insight**: Voting happens potentially every `ELECTION_CYCLE` (e.g., 360 ticks). Q-Learning needs feedback every `ACTION_INTERVAL` (30 ticks).
- **Solution**: `PoliticalOrchestrator` must provide a "Rolling Polling Average" (SMA of recent sentiment) accessible at every tick. The Reward Function will use this `current_approval_rating` rather than waiting for election day results.

## 2. Risk Assessment
- **Feature Interaction**: The `Lobbying` mechanic introduces a "Pay-to-Win" vector for Firms. If the AI learns that "High Corp Tax" = "High Lobbying Revenue" = "High Spending Power" = "High Approval", it might create a racket. This is an intended emergent behavior (Rent-seeking), not a bug.
- **Testing**: Existing tests for `GovernmentAI` mock the state tuple. These tests will fail when the state tuple definition changes. The Spec includes a plan to update `MockGovernment` and test fixtures.

## 3. Verification Strategy
- **Golden Data**: A new `golden_q_table_v5.pkl` must be generated after initial training.
- **Unit Tests**: Verify that `calculate_reward` correctly weights Approval vs. Stability based on the configured `populism_factor`.

## 4. Regression Analysis
I have verified that the refactoring of `GovernmentAI` and `SmartLeviathanPolicy` does not break existing integration tests.
- `tests/integration/test_government_ai_logic.py`: Updated to verify new 6-tuple state and populist reward logic. passed.
- `tests/integration/test_government_integration.py`: Confirmed legacy integration behavior remains intact. passed.
- `tests/integration/test_government_refactor_behavior.py`: Confirmed fiscal and execution engines still operate correctly under the new policy shell. passed.
- `tests/unit/test_government_structure.py`: Verified structural integrity of the Government singleton. passed.

The new `GovernmentAI` maintains backward compatibility in behavior where possible (defaults), but the state space change necessitates a fresh Q-Table (`q_table_v5_populist.pkl`), which is handled gracefully (starts fresh if missing).

## 5. Test Evidence
```
tests/integration/test_government_ai_logic.py::TestGovernmentAILogic::test_get_state_ideal
-------------------------------- live log call ---------------------------------
INFO     simulation.ai.government_ai:government_ai.py:83 No existing Q-Table q_table_v5_populist.pkl. Starting fresh.
PASSED                                                                   [  9%]
tests/integration/test_government_ai_logic.py::TestGovernmentAILogic::test_lobbying_bonus
-------------------------------- live log call ---------------------------------
INFO     simulation.ai.government_ai:government_ai.py:83 No existing Q-Table q_table_v5_populist.pkl. Starting fresh.
PASSED                                                                   [ 18%]
tests/integration/test_government_ai_logic.py::TestGovernmentAILogic::test_lobbying_logic
-------------------------------- live log call ---------------------------------
INFO     simulation.ai.government_ai:government_ai.py:83 No existing Q-Table q_table_v5_populist.pkl. Starting fresh.
PASSED                                                                   [ 27%]
tests/integration/test_government_ai_logic.py::TestGovernmentAILogic::test_populist_reward
-------------------------------- live log call ---------------------------------
INFO     simulation.ai.government_ai:government_ai.py:83 No existing Q-Table q_table_v5_populist.pkl. Starting fresh.
PASSED                                                                   [ 36%]
tests/integration/test_government_integration.py::test_government_execute_social_policy_tax_and_welfare
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:166 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
PASSED                                                                   [ 45%]
tests/unit/test_government_structure.py::TestGovernmentStructure::test_government_singleton PASSED [ 54%]
tests/unit/test_government_structure.py::TestGovernmentStructure::test_simulation_delegation PASSED [ 63%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_fiscal_engine_taylor_rule PASSED [ 72%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_execution_engine_state_update PASSED [ 81%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_orchestrator_integration
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:166 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
-------------------------------- live log call ---------------------------------
INFO     modules.common.utils.shadow_logger:shadow_logger.py:36 ShadowLogger initialized at logs/shadow_hand_stage1.csv
PASSED                                                                   [ 90%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_social_policy_execution
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:166 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
PASSED                                                                   [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 11 passed, 1 warning in 0.45s =========================
```
