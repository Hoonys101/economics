# Phase 23 Regression Cleanup Insight Report

## 1. Architectural Insights

### 1.1. Government Architecture Alignment
The transition to a singleton `Government` instance (`state.government` vs `state.governments`) required updates in test mocks. The `SimulationState` DTO uses `primary_government`, which must be consistently populated in tests. We identified that tests interacting with governance systems often mocked `SimulationState` without setting this attribute, leading to `AttributeError`.

### 1.2. M&A Manager Type Safety
The M&A logic now strictly enforces integer arithmetic (Penny Standard). Comparisons between `market_cap` (derived from float stock price) and `intrinsic_value_pennies` (int) caused `TypeError` in mocks where attributes were not explicitly typed. We reinforced the principle that all financial values in state DTOs (e.g., `FinanceStateDTO`) must be initialized with concrete types, even in mocks.

### 1.3. Agent Decision Pipeline Isolation
The "Stateless Engine & Orchestrator" (SEO) refactor introduced parallel execution of `DecisionEngine` and `HREngine`. Integration tests verifying agent decisions were failing because `HREngine` generated automatic orders (e.g., "BUY labor") that polluted the assertions targeting `DecisionEngine` output. We adopted a strategy of mocking the `HREngine` output in isolation tests to ensure "Logic Separation" and cleaner verification.

### 1.4. Settlement System Audit Integrity
The `SettlementSystem.audit_total_m2` method enforces strict type checking (`isinstance(agent, IFinancialAgent)`). Tests using simplified mocks (implementing only `IFinancialEntity` without the full Agent ID contract) were being silently skipped during audit summation, leading to assertions failures. We enforced "Protocol Purity" in tests by ensuring mocks satisfy the full `IFinancialAgent` protocol when interacting with the Settlement System.

## 2. Regression Analysis

### 2.1. Government Attribute Error
- **Symptom:** `AttributeError: Mock object has no attribute 'primary_government'` in `test_system_command_processor.py`.
- **Root Cause:** Test fixture `mock_simulation_state` set `state.government` but not `state.primary_government`.
- **Fix:** Updated fixture to alias `state.primary_government = state.government` and ensured proper protocol adherence.

### 2.2. M&A Type Conflicts
- **Symptom:** `TypeError: '<' not supported between instances of 'float' and 'MagicMock'` in `ma_manager.py` and `test_phase29_depression.py`.
- **Root Cause:** Firm mocks did not initialize `finance_state.valuation_pennies`, causing it to default to a `MagicMock` object, which failed comparison with integer/float thresholds.
- **Fix:** Explicitly initialized `valuation_pennies` and `consecutive_loss_turns` in firm mocks.

### 2.3. Agent Decision Assertion Failure
- **Symptom:** `AssertionError: assert 2 == 1` in `test_agent_decision.py`.
- **Root Cause:** `Firm.make_decision` aggregated orders from both `DecisionEngine` (mocked) and `HREngine` (live/default), resulting in an unexpected labor order.
- **Fix:** Mocked `HREngine.manage_workforce` to return an empty order list, isolating the `DecisionEngine` test scope.

### 2.4. Audit Integrity Mismatch
- **Symptom:** `assert False` in `test_audit_total_m2_logic` (Actual 200 vs Expected 300).
- **Root Cause:** The Household mock implemented `IFinancialEntity` but not `IFinancialAgent`. The `audit_total_m2` loop filters for `IFinancialAgent`, so the household's cash was ignored.
- **Fix:** Updated the mock to strictly satisfy `IFinancialAgent`.

## 3. Test Evidence

All tests passed successfully after fixes.

```
============================== 3 passed in 0.35s ===============================
tests/unit/test_ma_pennies.py::TestMAManagerPennies::test_friendly_merger_price_is_int PASSED
tests/unit/test_ma_pennies.py::TestMAManagerPennies::test_hostile_takeover_price_is_int PASSED
tests/unit/test_ma_pennies.py::TestMAManagerPennies::test_bankruptcy_liquidation_values_are_int PASSED

tests/integration/scenarios/diagnosis/test_agent_decision.py::test_household_makes_decision PASSED
tests/integration/scenarios/diagnosis/test_agent_decision.py::test_firm_makes_decision PASSED

tests/unit/simulation/systems/test_audit_total_m2.py::test_audit_total_m2_logic PASSED

tests/system/test_phase29_depression.py::TestPhase29Depression::test_depression_scenario_triggers PASSED
tests/system/test_phase29_depression.py::TestPhase29Depression::test_crisis_monitor_logging PASSED

tests/modules/governance/test_system_command_processor.py::test_set_corporate_tax_rate PASSED
tests/modules/governance/test_system_command_processor.py::test_set_income_tax_rate PASSED
tests/modules/governance/test_system_command_processor.py::test_set_base_interest_rate PASSED
tests/modules/governance/test_system_command_processor.py::test_missing_government PASSED
tests/modules/governance/test_system_command_processor.py::test_protocol_guardrails PASSED
```
