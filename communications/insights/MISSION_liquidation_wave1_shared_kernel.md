# Mission: Shared Financial Kernel & Cycle Breaker (Wave 1)

## 1. Overview
This mission successfully established the `modules.common.financial` shared kernel, breaking the circular dependency between `modules.finance` and `modules.hr`. It also enforced strict "Penny Standard" (integer arithmetic) for financial claims.

## 2. Execution Summary
1.  **Kernel Creation**: Created `modules/common/financial` with `dtos.py` and `api.py`.
2.  **DTO Migration**:
    -   `MoneyDTO` moved from `finance` to `common.financial`.
    -   `Claim` moved from `common` to `common.financial`.
    -   `Claim` upgraded to use `amount_pennies: int`.
3.  **Interface Migration**:
    -   `IFinancialEntity` and `IFinancialAgent` moved to `common.financial`.
    -   `IFinancialAgent` now explicitly inherits `IFinancialEntity`.
4.  **Refactoring**: Updated all dependent modules (`finance`, `hr`, `simulation`) to use the new kernel.
5.  **Logic Updates**:
    -   `LiquidationManager`, `TaxService`, `HRService` updated to use integer math for Claims.
    -   `SettlementSystem` updated to strictly respect `IFinancialEntity` protocol.
    -   `Government` and `MockAgent` implementations updated to fully satisfy `IFinancialEntity` (`deposit`, `withdraw`).

## 3. Modified Files
-   `modules/common/financial/__init__.py` (New)
-   `modules/common/financial/dtos.py` (New)
-   `modules/common/financial/api.py` (New)
-   `modules/finance/api.py`
-   `modules/finance/dtos.py`
-   `modules/hr/api.py`
-   `modules/hr/service.py`
-   `modules/finance/service.py`
-   `simulation/firms.py`
-   `simulation/core_agents.py`
-   `simulation/agents/government.py`
-   `simulation/systems/liquidation_manager.py`
-   `modules/finance/wallet/wallet.py`
-   `modules/common/dtos.py` (Deleted)
-   `tests/integration/test_liquidation_waterfall.py`
-   `tests/unit/systems/test_liquidation_manager.py`
-   `tests/unit/finance/test_settlement_system_overdraft.py`
-   `tests/unit/systems/test_settlement_system.py`
-   `tests/unit/test_ssot_compliance.py`
-   `tests/unit/simulation/systems/test_audit_total_m2.py`
-   `tests/finance/test_settlement_fx_swap.py`
-   `tests/finance/test_protocol_integrity.py`
-   `tests/unit/modules/finance/test_double_entry.py`
-   `tests/unit/systems/test_housing_system.py`
-   `tests/integration/test_liquidation_services.py`

## 4. Test Evidence
Ran `pytest tests/`.
Result: **1005 passed, 11 skipped**.
All relevant tests for Liquidation, Settlement, and Finance passed.
Regression tests passed.
