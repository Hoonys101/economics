# Technical Debt Report: mod-finance

| TD-ID | Location | Description | Impact |
| :--- | :--- | :--- | :--- |
| TD-FIN-001 | `simulation/bank.py` | `Bank.grant_loan` returns `Optional[Tuple[LoanInfoDTO, Transaction]]` but its interface `IBank.grant_loan` specifies `Optional[LoanInfoDTO]`. | Violation of Interface Segregation/Liskov Substitution. Callers expecting just DTO will fail (as seen in tests). |
| TD-FIN-002 | `modules/finance/system.py` | `FinanceSystem.grant_bailout_loan` is deprecated and returns `None`, but is still present in the class. | Confusion for developers. Tests were still trying to use it. Should be removed or strictly aliased to `request_bailout_loan` (though return types differ). |
| TD-FIN-003 | `modules/finance/managers/loan_manager.py` | `repay_loan` originally returned `bool` (False on failure) while `Bank` interface implied/tests expected exception. | Inconsistent error handling strategy. Fixed to raise `LoanNotFoundError` but `Bank.repay_loan` signature says `-> bool` which might be misleading now. |
| TD-FIN-004 | `tests/unit/modules/finance/test_system.py` | `StubCentralBank` did not implement `add_bond_to_portfolio`, causing silent failures in state updates within `FinanceSystem`. | Fragile tests. The stub didn't match the expected interface of the collaborator. |
| TD-FIN-005 | `modules/finance/api.py` | `IDepositManager.create_deposit` used default argument `currency="USD"`. | Hardcoded constant in interface definition. Fixed to `DEFAULT_CURRENCY`. |

## Problem Phenomenon & Root Cause Analysis

### 1. `Bank.grant_loan` Return Type Mismatch
- **Phenomenon**: `tests/unit/finance/test_bank_service_interface.py` failed with `TypeError: tuple indices must be integers...` because it tried to access dict keys on a tuple.
- **Root Cause**: `Bank.grant_loan` was updated to return `(LoanInfoDTO, Transaction)` to support the "Sacred Sequence" (generating transaction object for credit creation), but the interface definition and tests were not updated to reflect this change.
- **Solution**: Updated tests to unpack the tuple. Recommended updating `IBank` interface definition to match implementation or wrapping the return value in a dedicated DTO.

### 2. `FinanceSystem.grant_bailout_loan` Deprecation
- **Phenomenon**: Tests failed with `TypeError` due to argument mismatch and `None` return value.
- **Root Cause**: `FinanceSystem` moved to a Command Pattern (`request_bailout_loan` returning `GrantBailoutCommand`) but left a deprecated `grant_bailout_loan` method that logged a warning and returned `None`. Tests were not updated.
- **Solution**: Updated tests to use `request_bailout_loan` and verify the command object.

### 3. Missing Method on Stub
- **Phenomenon**: `test_service_debt_central_bank_repayment` failed because the bond was not found in Central Bank's assets.
- **Root Cause**: `FinanceSystem` uses `hasattr(buyer, 'add_bond_to_portfolio')` to update state. `StubCentralBank` had `purchase_bonds` instead.
- **Solution**: Renamed `StubCentralBank.purchase_bonds` to `add_bond_to_portfolio`.

## Lessons Learned
- **Interface Consistency**: When changing return types for "Sacred Sequence" (Transactions), ensure interfaces and tests are updated immediately.
- **Stubs vs Mocks**: Stubs in tests must strictly adhere to the expected interface of the real object, especially when `hasattr` checks are used in the SUT.
- **Deprecation Strategy**: When deprecating a method, ensure tests are updated to use the new method, or the deprecated method maintains enough backward compatibility to pass existing tests (though in this case, the architectural shift to Command pattern made strict compatibility hard).
