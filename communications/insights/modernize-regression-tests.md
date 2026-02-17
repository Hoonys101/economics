# Insight Report: Modernize Regression Tests

## Architectural Insights
- Identified dependence on `MockAgent` state in Judicial tests as a violation of SSoT.
- Production Engine float math is a source of non-determinism.
- Updated `SettlementSystem` protocol in `simulation/finance/api.py` to match implementation and provide `get_balance`.

## Technical Debt
- [Resolving] TD-045: Mock Object Drift.
- [Resolving] TD-092: Non-deterministic Float Math.

## Test Evidence
```
tests/unit/governance/test_judicial_ssot.py::test_waterfall_cash_only_ssot PASSED [ 10%]
tests/unit/governance/test_judicial_ssot.py::test_waterfall_partial_cash
-------------------------------- live log call ---------------------------------
WARNING  modules.governance.judicial.system:system.py:189 JudicialSystem: Debt Restructuring Required for Agent 101. Remaining Debt: 600
PASSED                                                                   [ 20%]
tests/unit/governance/test_judicial_system.py::test_judicial_system_waterfall_full_recovery
-------------------------------- live log call ---------------------------------
INFO     modules.governance.judicial.system:system.py:58 JudicialSystem: Credit frozen for Agent 1 until tick 110.
INFO     modules.governance.judicial.system:system.py:66 JudicialSystem: Applied XP penalty to Agent 1.
PASSED                                                                   [ 30%]
tests/unit/governance/test_judicial_system.py::test_judicial_system_waterfall_partial_recovery_and_restructuring
-------------------------------- live log call ---------------------------------
INFO     modules.governance.judicial.system:system.py:58 JudicialSystem: Credit frozen for Agent 1 until tick 110.
INFO     modules.governance.judicial.system:system.py:66 JudicialSystem: Applied XP penalty to Agent 1.
INFO     modules.governance.judicial.system:system.py:143 JudicialSystem: Transferred 10 shares of Firm 99 from 1 to 2.
WARNING  modules.governance.judicial.system:system.py:189 JudicialSystem: Debt Restructuring Required for Agent 1. Remaining Debt: 850.0
PASSED                                                                   [ 40%]
tests/unit/firm/test_firm_actions.py::TestFirmActionExecutor::test_invest_automation_success
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:88 INTERNAL_EXEC | Firm 1 invested 100 in INVEST_AUTOMATION.
PASSED                                                                   [ 50%]
tests/unit/firm/test_firm_actions.py::TestFirmActionExecutor::test_invest_rd_success
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:112 INTERNAL_EXEC | Firm 1 R&D SUCCESS (Budget: 100.0)
PASSED                                                                   [ 60%]
tests/unit/firm/test_firm_actions.py::TestFirmActionExecutor::test_fire_employee
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:147 INTERNAL_EXEC | Firm 1 fired employee 2.
PASSED                                                                   [ 70%]
tests/unit/firm/test_production_int_math.py::test_production_integer_depreciation PASSED [ 80%]
tests/unit/firm/test_production_int_math.py::test_production_deterministic_output PASSED [ 90%]
tests/unit/firm/test_production_int_math.py::test_production_deterministic_floor PASSED [100%]

======================== 10 passed, 2 warnings in 0.38s ========================
```
