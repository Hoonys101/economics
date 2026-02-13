# [Insight] Apply Stability Fix Plan

## Architectural Insights
1.  **CommandService Dependency Injection**: The primary cause of failure was the `Simulation` facade attempting to instantiate `CommandService` with no arguments, while the service required `GlobalRegistry`, `SettlementSystem`, and `AgentRegistry`. This was resolved by restructuring `SimulationInitializer` to pre-instantiate these core services and inject them into `Simulation`, aligning with Dependency Injection principles. This eliminates circular dependencies and ensures testability.

2.  **DTO Evolution & Backward Compatibility**: `GodCommandDTO` was strictly typed for the new `CommandService`, breaking legacy tests that relied on `target_agent_id` and `amount` fields (implicit `INJECT_MONEY` logic). We resolved this by adding these fields as optional to the DTO, preserving the ability to run legacy tests while the system transitions to the new `parameter_key`/`new_value` schema.

3.  **Fiscal Policy Integration Testing**: The `test_debt_ceiling_enforcement` integration test was failing because it mocked `FinanceSystem` but the `Government` agent had migrated to using `FiscalBondService` for deficit spending. Furthermore, the test relied on implicit wallet state. We updated the test to mock the correct service (`FiscalBondService`), explicitly manage wallet state (clearing it to force bond issuance), and aligned the mock data structures with the current `BondDTO` definition. This highlights the importance of keeping integration tests synchronized with service decomposition (Finance -> FiscalBond).

## Test Evidence

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-7.4.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
testpaths: tests/unit, tests/integration, tests/system, tests
plugins: anyio-4.4.0
collected 7 items

tests/unit/simulation/orchestration/phases/test_intercept.py::test_execute_no_commands PASSED [ 14%]
tests/unit/simulation/orchestration/phases/test_intercept.py::test_execute_commands_audit_pass PASSED [ 28%]
tests/integration/test_fiscal_policy.py::test_potential_gdp_ema_convergence PASSED [ 42%]
tests/integration/test_fiscal_policy.py::test_counter_cyclical_tax_adjustment_recession PASSED [ 57%]
tests/integration/test_fiscal_policy.py::test_counter_cyclical_tax_adjustment_boom PASSED [ 71%]
tests/integration/test_fiscal_policy.py::test_debt_ceiling_enforcement PASSED [ 85%]
tests/integration/test_fiscal_policy.py::test_calculate_income_tax_uses_current_rate PASSED [100%]

========================= 7 passed, 1 warning in 0.18s =========================
```
