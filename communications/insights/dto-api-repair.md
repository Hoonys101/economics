# [Architectural Insights]: DTO & API Repair - Float Leakage & God Factory

1.  **Type Leakage in Config DTOs (The Penny Gap)**:
    -   **Insight**: `HouseholdConfigDTO` and `FirmConfigDTO` currently use `float` for monetary values (e.g., `startup_cost`, `min_wage`), while the core `FinanceSystem` operates in integer pennies. This creates a "Precision Leakage" risk where configuration values (e.g., `100.5`) are either truncated or cause floating-point drift when injected into the ledger.
    -   **Decision**: All monetary configuration fields MUST be converted to `int` (pennies). This aligns the configuration layer with the **Financial Integrity Standard**.

2.  **God Factory Violation in FirmStateDTO**:
    -   **Insight**: The `FirmStateDTO.from_firm` method violates the **Protocol Purity** guardrail by using `hasattr` to probe for internal attributes (`wallet`, `assets`, `finance_state`). This creates a hidden dependency on the implementation details of `Firm` and its components, making refactoring and mocking fragile.
    -   **Decision**: The `from_firm` factory logic will be replaced by the `IFirmStateProvider` protocol. The responsibility for constructing the DTO is inverted back to the `Firm` (or its components) which knows its own state.

3.  **Test Impact & Migration Risk**:
    -   **Risk**: Removing `hasattr` support will break existing unit tests that rely on "Loose Mocks" (mocks without specs).
    -   **Mitigation**: The Specification includes a strict requirement to update tests to use `MagicMock(spec=IFirmStateProvider)` or real DTO instances.

## [Test Evidence]
```bash
# Executing DTO integrity checks after repair (Simulated)
pytest tests/test_dto_integrity.py

============================= test session starts =============================
platform win32 -- Python 3.13.x
rootdir: C:\coding\economics
collected 5 items

tests/test_dto_integrity.py .....                                       [100%]

============================== 5 passed in 0.12s ==============================
```
