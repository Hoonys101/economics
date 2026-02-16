# [Architectural Insights]: DTO & API Repair - Float Leakage & God Factory

## 1. Architectural Insights

### 1.1. Type Leakage in Config DTOs (The Penny Gap)
-   **Problem**: Configuration values for monetary fields (e.g., `INITIAL_FIRM_CAPITAL_MEAN`, `INITIAL_HOUSEHOLD_ASSETS_MEAN`) were defined as floats in `config/defaults.py`, creating a "Precision Leakage" risk when interacting with the integer-based `FinanceSystem`.
-   **Resolution**: Updated `config/defaults.py` to store these values as strict integers (pennies). Specifically:
    -   `INITIAL_HOUSEHOLD_ASSETS_MEAN`: `5000.0` -> `500000` (Pennies)
    -   `INITIAL_FIRM_CAPITAL_MEAN`: `50000.0` -> `5000000` (Pennies)
-   **Impact**: Ensures financial integrity by eliminating floating-point drift at the configuration boundary.

### 1.2. God Factory Violation in FirmStateDTO
-   **Problem**: The `FirmStateDTO.from_firm` method previously violated **Protocol Purity** by using `hasattr` to probe internal attributes of the `Firm` class. This created a fragile dependency on implementation details.
-   **Status**: This issue was verified as **already resolved** in the codebase.
    -   `FirmStateDTO.from_firm` has been removed.
    -   `IFirmStateProvider` protocol is implemented in `modules/simulation/dtos/api.py`.
    -   `Firm` class implements `IFirmStateProvider` and `get_state_dto()`.
-   **Action**: No code changes required for this specific issue in this PR, but verified compliance.

### 1.3. Mock Protocol Compliance Fix
-   **Problem**: `tests/unit/simulation/systems/test_audit_total_m2.py` failed because it mocked `IFinancialEntity` incorrectly (trying to use `get_balance` method instead of the required `balance_pennies` property).
-   **Resolution**: Updated the test to use `PropertyMock` for `balance_pennies`, ensuring the test aligns with the strict protocol definition.

## 2. Test Evidence

### 2.1. Audit Total M2 Test (Protocol Compliance)
Verifies that the `SettlementSystem` correctly audits M2 using strict protocol checks (`IFinancialEntity`/`IBank`).

```bash
$ python3 -m pytest tests/unit/simulation/systems/test_audit_total_m2.py
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.12.1, asyncio-0.23.5, mock-3.14.0
collected 1 item

tests/unit/simulation/systems/test_audit_total_m2.py::test_audit_total_m2_logic PASSED [100%]

============================== 1 passed in 0.44s ===============================
```

### 2.2. Finance System Unit Tests
The `FinanceSystem` tests confirm that `StubFirm` (which implements `IFinancialFirm`) and the system operate correctly with strict typing.

```bash
$ python3 -m pytest tests/unit/modules/finance/test_system.py
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.12.1, asyncio-0.23.5, mock-3.14.0
collected 10 items

tests/unit/modules/finance/test_system.py::test_evaluate_solvency_startup_pass PASSED [ 10%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_startup_fail PASSED [ 20%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_established_pass PASSED [ 30%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_established_fail PASSED [ 40%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_market PASSED [ 50%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_qe PASSED [ 60%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_fail PASSED [ 70%]
tests/unit/modules/finance/test_system.py::test_bailout_fails_with_insufficient_government_funds PASSED [ 80%]
tests/unit/modules/finance/test_system.py::test_grant_bailout_loan PASSED [ 90%]
tests/unit/modules/finance/test_system.py::test_service_debt_central_bank_repayment PASSED [100%]

============================== 10 passed in 0.70s ==============================
```

### 2.3. Purity Gate Tests
Verifies that `FirmStateDTO` is correctly instantiated and accepted by Decision Engines.

```bash
$ python3 -m pytest tests/integration/test_purity_gate.py
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.12.1, asyncio-0.23.5, mock-3.14.0
collected 3 items

tests/integration/test_purity_gate.py::test_decision_context_purity PASSED [ 33%]
tests/integration/test_purity_gate.py::test_standalone_firm_engine_uses_dto PASSED [ 66%]
tests/integration/test_purity_gate.py::test_household_engine_uses_dto PASSED [100%]

============================== 3 passed in 0.25s ===============================
```
