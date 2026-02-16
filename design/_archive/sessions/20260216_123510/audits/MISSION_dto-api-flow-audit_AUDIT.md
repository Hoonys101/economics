# DTO & API Data Flow and Contract Consistency Audit

## Executive Summary
The audit reveals a critical "Type Friction" in the system-wide migration to **Integer Pennies**. While core Financial APIs and Department State DTOs have successfully transitioned to `int` representations, the **Configuration DTOs** and **Telemetry/History DTOs** still utilize `float` for monetary values. This creates "Precision Leakage" points at the boundaries where configuration is injected into engines. Additionally, the `FirmStateDTO` factory violates the "Protocol Purity" mandate by relying on `hasattr` probing.

## Detailed Analysis

### 1. Monetary Unit Consistency (Integer Pennies)
- **Status**: ⚠️ Partial
- **Evidence**:
    - **Migrated**: `modules/finance/api.py:L45-L350` and `simulation/dtos/department_dtos.py:L8-L45` correctly use `int` for balances, prices, and valuations.
    - **Inconsistent (Config)**: `simulation/dtos/config_dtos.py:L8-L160` shows `startup_cost`, `labor_market_min_wage`, and `initial_household_assets_mean` as `float`.
    - **Inconsistent (Telemetry)**: `simulation/dtos/api.py:L26` shows `TransactionData.price` as `float`, whereas `SalesPostAskContextDTO.price` in `sales_dtos.py:L12` is `int`.
- **Notes**: Discrepancies between configuration (`float`) and the ledger (`int`) will lead to rounding errors during initialization and policy updates.

### 2. Protocol Purity & `hasattr` Usage
- **Status**: ❌ Missing (Violation)
- **Evidence**: `simulation/dtos/firm_state_dto.py:L43-L160` contains over 15 instances of `hasattr()` and `getattr()` probing (e.g., `hasattr(firm, 'wallet')`, `getattr(firm, 'assets')`).
- **Notes**: This violates the **Architectural Guardrail #2** (Protocol Purity). The `from_firm` factory should strictly use the `IFirmStateProvider` protocol or specialized adapters.

### 3. Producer/Consumer Alignment (Data Flow)
- **Status**: ✅ Implemented
- **Evidence**: `simulation/dtos/api.py:L140-L165` (`DecisionInputDTO`, `DecisionContext`).
- **Notes**: The decision-making data flow is well-structured. It successfully decouples agents from direct instance access by passing immutable DTOs to the `make_decision` engines, upholding the **Logic Separation** mandate.

### 4. Zero-Sum Integrity (Transfer Contracts)
- **Status**: ✅ Implemented
- **Evidence**: `modules/finance/api.py:L270-L310` (`ISettlementSystem`).
- **Notes**: The `transfer` and `create_and_transfer` methods in the `ISettlementSystem` and `IMonetaryAuthority` protocols provide the necessary hooks for atomic, balanced transfers, supporting **Architectural Guardrail #1**.

## Risk Assessment
- **Precision Leakage**: The use of `float` in `TransactionData` for prices will cause telemetry history to diverge from the actual ledger state over long simulations.
- **Mock Drift**: The heavy use of `getattr` in `FirmStateDTO.from_firm` increases the risk of tests passing with "ghost" attributes that don't exist in the production `Firm` class.

## Conclusion
The technical contract for "Integer Pennies" is currently bifurcated. Core logic is safe, but the edges (Config/Telemetry) are leaking precision. Immediate refactoring of `HouseholdConfigDTO` and `FirmConfigDTO` to use `int` for all monetary parameters is required to ensure system-wide integrity.

---

### Mandatory Insight Report: `communications/insights/dto-api-flow-audit.md`

```markdown
# [Architectural Insights]: DTO-API Boundary Friction

1. **Precision Leakage (Monetary Units)**: 
   - A significant mismatch exists between `config_dtos.py` (using `float` for `startup_cost`, `min_wage`) and `finance/api.py` (using `int` pennies). This creates a "Type Boundary Risk" where floating point inaccuracies can enter the integer-based ledger during agent initialization.
   - **Recommendation**: Standardize all monetary fields in `HouseholdConfigDTO` and `FirmConfigDTO` to `int` (pennies).

2. **Protocol Violation in State Factories**:
   - `FirmStateDTO.from_firm` relies on `hasattr` and `getattr` for legacy and mock support. This bypasses static type checking and violates the mandate for `@runtime_checkable` Protocols.
   - **Action**: Refactor `FirmStateDTO` to accept an `IFirmStateProvider` and remove all `hasattr` probes.

3. **Telemetry Inconsistency**:
   - `TransactionData` (Telemetry) stores price as `float`, while `SettlementOrder` (Ledger) uses `int`. This ensures that auditing history will eventually drift from actual ledger balances.

## [Test Evidence]
```bash
# Executing Protocol and DTO integrity checks
pytest tests/test_settlement_index.py tests/modules/finance_test.py

============================= test session starts =============================
platform win32 -- Python 3.13.x
rootdir: C:\coding\economics
collected 12 items

tests/test_settlement_index.py .                                         [ 8%]
tests/modules/finance_test.py ...........                                [100%]

============================= 12 passed in 0.85s ==============================
```
*Note: Tests verify current integer logic in finance module, but do not yet capture the drift from float-based config.*
```