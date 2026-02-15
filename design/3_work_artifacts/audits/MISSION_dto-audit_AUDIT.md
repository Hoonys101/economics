# Technical Report: DTO-API Data Flow Integrity Audit

## Executive Summary
The audit reveals a significant **"Type Drift"** between the core simulation DTOs and the specialized finance module APIs. While the project mandate requires integer pennies for financial precision (Phase 33), several key global DTOs still utilize `float` or `Dict[str, float]`. Additionally, the **Purity Gate** principle is violated in `FirmStateDTO`, which contains heavy extraction logic rather than being a pure data container.

## Detailed Analysis

### 1. DTO Integrity: Pennies vs. Floats (Phase 33 Inconsistency)
- **Status**: ⚠️ Partial
- **Evidence**: 
    - `modules/finance/dtos.py:L9-13`: Explicitly defines `MoneyDTO` as `amount_pennies: int`.
    - `simulation/dtos/api.py:L41`: `EconomicIndicatorData.total_household_assets` still uses `Dict[CurrencyCode, float]`.
    - `simulation/dtos/department_dtos.py:L8`: `FinanceStateDTO` uses `Dict[CurrencyCode, float]` for balance, revenue, and expenses.
    - `modules/household/dtos.py:L114-118`: `EconStateDTO` correctly uses `int` for wages and expected wages.
- **Notes**: There is a critical divergence between the Household module (migrated) and the Firm/Indicator DTOs (unmigrated). This inconsistency risks rounding errors and breaks the **Zero-Sum Integrity** mandate during state transitions.

### 2. Layer Violation: Logic in DTOs (Purity Gate Failure)
- **Status**: ❌ Missing (Violation Found)
- **Evidence**: 
    - `simulation/dtos/firm_state_dto.py:L43-176`: The `from_firm` class method contains 130+ lines of logic, including attribute discovery, legacy fallbacks, and internal dictionary construction.
    - `simulation/dtos/api.py:L173-183`: `SimulationState` includes functional logic for `register_currency_holder` and `unregister_currency_holder`.
- **Notes**: These files violate the mandate that DTOs be "pure data containers." `FirmStateDTO.from_firm` effectively acts as an Assembler/Factory but resides within the DTO definition, creating tight coupling between the DTO and the internal implementation of the `Firm` agent.

### 3. API Contract Alignment
- **Status**: ✅ Implemented
- **Evidence**:
    - `modules/finance/api.py:L263-275`: `ISettlementSystem` methods (`transfer`, `get_balance`) strictly use `int` for amounts.
    - `modules/government/dtos.py:L21`: `TaxHistoryItemDTO` total is documented as `MIGRATION: pennies`.
- **Notes**: The core financial interfaces are correctly defined to handle integer precision, even where the underlying DTOs feeding them are lagging.

### 4. Layer Violation: Dependency Inversion
- **Status**: ⚠️ Partial
- **Evidence**:
    - `simulation/dtos/api.py:L123-145`: `SimulationState` references concrete classes `Household` and `Firm` (imported via `TYPE_CHECKING` at L12-13), which is acceptable for typing but dangerous if used in runtime logic (as seen in `from_firm`).
- **Notes**: High-level simulation DTOs are importing from `modules.simulation.api`, which is the correct boundary, but `firm_state_dto.py` imports `DEFAULT_CURRENCY` from `modules.system.api`, showing healthy lower-level dependency.

## Risk Assessment
- **Critical (High)**: **Floating point drift.** Reporting `EconomicIndicatorData` as floats while processing `SettlementSystem` transfers as ints will cause the `audit_total_m2` to fail due to precision mismatch (1-cent leaks).
- **High**: **Assembler Logic.** If the `Firm` class structure changes, the `FirmStateDTO.from_firm` logic will break silently if not strictly tested, as it relies on `getattr` and `hasattr` fallbacks.
- **Medium**: **Dead Data.** `HouseholdStateDTO` in `modules/household/dtos.py` is marked `[DEPRECATED]` but remains in the file, potentially leading to "Mock Drift" in tests.

## Conclusion
The project has a clear architectural vision for integer-based financial integrity, but the implementation is fragmented. The Household module is "Contract-Ready," whereas the Firm module and Global Indicators are still "Legacy-Linked." 

**Recommended Actions**:
1. Refactor `simulation/dtos/firm_state_dto.py` to remove `from_firm` logic into a dedicated `SnapshotAssembler`.
2. Update `FinanceStateDTO` and `EconomicIndicatorData` to use `int` pennies for all monetary fields.
3. Enforce the use of `HouseholdSnapshotDTO` and remove the deprecated `HouseholdStateDTO` to prevent developer confusion.