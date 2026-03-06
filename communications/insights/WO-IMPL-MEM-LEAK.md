---
mission_key: "WO-IMPL-MEM-LEAK"
date: "2026-03-06"
target_manual: "TECH_DEBT_LEDGER.md"
actionable: true
---

# Insight Report: WO-IMPL-MEM-LEAK

## 1. [Architectural Insights]
- **TD-MEM-GLOBAL-AUDIT-LEAK (Resolved)**: The primary memory leak driving exponential `O(N*T)` growth was isolated to `GLOBAL_WALLET_LOG` in `modules/finance/wallet/audit.py`. This unbounded list tracked all wallet transfers across all ticks indefinitely.
  - *Fix*: The global variable has been eradicated. The base `Wallet` initialization pattern was refactored to disable default unbounded audit logging (`self._audit_log = None`). This entirely closes the GC-escaping memory sink while preserving local audit buffers only when explicitly injected.
- **TD-MEM-AGENT-ENGINE-BLOAT (Partially Resolved)**: High initial memory allocation (`O(N)`) during `SimulationInitializer` was tied to duplicating `RuleBasedHouseholdDecisionEngine` and `RuleBasedFirmDecisionEngine` instantiations for every agent.
  - *Fix*: The `RuleBased` engines were entirely decoupled into global singletons within `modules/system/builders/simulation_builder.py` prior to the agent creation loops, and injected per agent, drastically decreasing memory and load footprint for rule-based configurations.
- **TD-ARCH-AI-STATE-DECOUPLING (New Tech Debt)**: While attempting to also singletonize `HouseholdAI` and `AIDrivenHouseholdDecisionEngine`, it was found that the `BaseAIEngine` relies strictly on agent-level state mappings initialized via `agent_id` tracking (e.g. `self.last_consumption_states`). Consequently, transforming AI models directly into singletons without first separating behavioral weights (Q-tables) from localized state logic breaks `1-to-1` unit assertions and creates new architectural debt. This transition has been gracefully backed out to maintain stability and filed as discrete future work.

## 2. [Regression Analysis]
- Tests pertaining to `SimulationInitializer` behavior pass cleanly.
- The AI Engine singleton refactor initially broke tightly-coupled tests (`test_household_decision_engine_new.py`, `test_household_ai.py`). Following Agile/Sprint principles, this incomplete AI refactor was rolled back while preserving the successful Rule-Based refactor, restoring the `Total Test Pass Mandate` immediately.

## 3. [Test Evidence]
```text
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
collected 14 items

tests/unit/test_household_decision_engine_new.py ........                [ 57%]
tests/unit/test_household_ai.py ......                                   [100%]

============================== 14 passed in 7.94s ==============================
```
