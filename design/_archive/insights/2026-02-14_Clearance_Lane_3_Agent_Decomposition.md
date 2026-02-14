# Lane 3: Agent Class Decomposition (Insight Report)

**Date**: 2026-02-14
**Status**: COMPLETED
**Debt ID**: `TD-STR-GOD-DECOMP`

## 1. Architectural Insights

### Decomposition Strategy
The god-class decomposition for `Firm` and `Household` was achieved by extracting "imperative execution logic" into separate orchestrator/connector classes. This pattern allows the Agent classes to remain focused on State Management and high-level Orchestration (Routing), while the detailed execution of decisions (interactions with engines and external systems) is handled by dedicated components.

*   **Firm**: Extracted `execute_internal_orders` into `FirmActionExecutor`. This removes ~100 lines of complex conditional logic handling investments, hiring, firing, and tax payments from the main class.
*   **Household**: Extracted `_execute_housing_action` into `HousingConnector`. This isolates the Household from the `HousingSystem` implementation details and sets a pattern for "System Connectors".

### Protocol Compliance
*   Implemented `IHousingSystem` protocol to ensure `HousingConnector` interacts with the Housing System via a defined interface, replacing loose `hasattr` checks.
*   Enforced usage of strict DTOs (`CanonicalOrderDTO`, `HousingActionDTO`) in the new components.

## 2. Test Evidence

The following tests verify the correct behavior of the extracted components and ensure no regressions in the original agents.

```
$ python3 -m pytest tests/unit/firm/test_firm_actions.py tests/unit/household/test_housing_connector.py tests/unit/test_firms.py tests/unit/test_household_refactor.py

============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.24.0, mock-3.15.1, anyio-4.12.1
asyncio: mode=Mode.AUTO, default_loop_scope=None
collected 14 items

tests/unit/firm/test_firm_actions.py::TestFirmActionExecutor::test_invest_automation_success
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:88 INTERNAL_EXEC | Firm 1 invested 100 in INVEST_AUTOMATION.
PASSED                                                                   [  7%]
tests/unit/firm/test_firm_actions.py::TestFirmActionExecutor::test_invest_rd_success
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:112 INTERNAL_EXEC | Firm 1 R&D SUCCESS (Budget: 100.0)
PASSED                                                                   [ 14%]
tests/unit/firm/test_firm_actions.py::TestFirmActionExecutor::test_fire_employee
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:147 INTERNAL_EXEC | Firm 1 fired employee 2.
PASSED                                                                   [ 21%]
tests/unit/household/test_housing_connector.py::TestHousingConnector::test_initiate_purchase
-------------------------------- live log call ---------------------------------
INFO     modules.household.connectors.housing_connector:housing_connector.py:31 HOUSING_CONNECTOR | Initiated purchase for property 1 by agent 1
PASSED                                                                   [ 28%]
tests/unit/household/test_housing_connector.py::TestHousingConnector::test_unknown_action PASSED [ 35%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_no_liabilities PASSED [ 42%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_with_liabilities PASSED [ 50%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_with_treasury_shares PASSED [ 57%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_negative_net_assets PASSED [ 64%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_zero_shares PASSED [ 71%]
tests/unit/test_firms.py::TestFirmProduction::test_produce PASSED        [ 78%]
tests/unit/test_firms.py::TestFirmSales::test_post_ask PASSED            [ 85%]
tests/unit/test_firms.py::TestFirmSales::test_adjust_marketing_budget_increase PASSED [ 92%]
tests/unit/test_household_refactor.py::TestHouseholdRefactor::test_property_management PASSED [100%]

============================== 14 passed in 0.26s ==============================
```

## 3. Deviations
*   `HousingConnector` was created as a new module instead of modifying `Household` in place, to strictly follow the separation of concerns.
*   `hasattr` usage in `HousingConnector` was replaced with `isinstance(system, IHousingSystem)` where `IHousingSystem` is a `runtime_checkable` Protocol defined in the connector file (temporary location until System Protocols are unified in Lane 2).
