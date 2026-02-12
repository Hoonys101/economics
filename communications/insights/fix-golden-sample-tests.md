# Insight: Fix Golden Sample Tests & Protocol Compliance

## Architectural Decisions & Technical Debt

### 1. Adoption of Golden Samples over MagicMocks
To resolve recurring issues with `MagicMock` failing `isinstance` checks and missing attributes in complex interactions (e.g., `TaxService`, `WelfareManager`), we introduced `simulation.factories.golden_agents.GoldenAgent`.
- **Benefit**: Provides a compliant, reusable agent implementation that satisfies multiple protocols (`IFinancialAgent`, `IMortgageBorrower`, `IPropertyOwner`, `IResident`, `IWelfareRecipient`) natively.
- **Standardization**: Eliminates ad-hoc mocking of agent attributes in every test file.

### 2. Strict Penny Standard Enforcement
The system has migrated to using integer pennies for all monetary values. Tests were failing because they used floating-point dollar values in assertions or configurations.
- **Fix**: Updated `mock_config` thresholds (e.g., `WEALTH_TAX_THRESHOLD`) and test assertions to use integer pennies (e.g., $10.0 -> 1000 pennies).
- **Compliance**: Ensures tests align with the core `modules.finance` architecture.

### 3. Protocol Purity & Verification
The `HousingTransactionHandler` relies on `isinstance` checks against runtime-checkable protocols (`IMortgageBorrower`, `IFinancialAgent`).
- **Issue**: Previous `MockAgent` implementations did not fully adhere to the protocols, causing transaction failures.
- **Resolution**: `GoldenAgent` explicitly inherits from these protocols, ensuring both static type checking and runtime `isinstance` validation pass.

### 4. Protocol Shield Testing
The `enforce_purity` decorator test was improved to correctly mock the stack frame structure, ensuring that path normalization logic is verified accurately.

## Test Evidence

All relevant tests passed successfully.

```
tests/common/test_protocol.py::TestProtocolShield::test_authorized_call PASSED [  9%]
tests/common/test_protocol.py::TestProtocolShield::test_disabled_shield PASSED [ 18%]
tests/common/test_protocol.py::TestProtocolShield::test_unauthorized_call
-------------------------------- live log call ---------------------------------
ERROR    modules.common.protocol:protocol.py:60 PURITY_VIOLATION | Unauthorized call to 'protected_function' from '/app/scripts/random_script.py'
PASSED                                                                   [ 27%]
tests/modules/government/test_tax_service.py::test_collect_wealth_tax PASSED [ 36%]
tests/modules/government/test_tax_service.py::test_collect_wealth_tax_below_threshold PASSED [ 45%]
tests/modules/government/test_welfare_manager.py::test_run_welfare_check_unemployment PASSED [ 54%]
tests/modules/government/test_welfare_manager.py::test_run_welfare_check_stimulus
-------------------------------- live log call ---------------------------------
WARNING  modules.government.welfare.manager:manager.py:125 STIMULUS_TRIGGERED | GDP Drop Detected. Requests generated.
PASSED                                                                   [ 63%]
tests/modules/government/test_welfare_manager.py::test_provide_firm_bailout PASSED [ 72%]
tests/modules/government/test_welfare_manager.py::test_run_welfare_check_with_firm PASSED [ 81%]
tests/test_wo_4_1_protocols.py::test_housing_handler_with_protocol_agent PASSED [ 90%]
tests/test_wo_4_1_protocols.py::test_protocol_compliance PASSED          [100%]

============================== 11 passed in 0.24s ==============================
```
