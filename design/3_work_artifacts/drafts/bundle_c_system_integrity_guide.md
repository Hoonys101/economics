# Mission Guide: Simulation Systems & Engine Hardening [Bundle C]

This document provides consolidated context and implementation requirements for Jules to resolve technical debts related to core simulation mechanics and engine structure.

## 1. Objectives
- **TD-231**: Fix Sales Tax atomicity in `CommerceSystem`.
- **TD-232**: Integrate `InheritanceManager` with `TransactionProcessor`.
- **TD-225/223**: Unify Liquidation logic and clean up redundant Loan DTOs.
- **TD-238**: Decompose the `phases.py` monolith into modular phase handlers.

## 2. Reference Context (MUST READ)
- **Audit Reports**: 
  - [Economic Integrity Audit (SALESTAX)](file:///c:/coding/economics/design/3_work_artifacts/reports/inbound/refactor_sales-tax-atomicity-inheritance-381587902011087733_audit_economic_WO_SALESTAX.md)
  - [Structural Integrity Audit](file:///c:/coding/economics/design/3_work_artifacts/reports/inbound/structural-structural-001-15007860028193717728_audit_structural_STRUCTURAL-001.md)
- **Base Spec**: [TD-225 Unified Liquidation Protocol](file:///c:/coding/economics/design/3_work_artifacts/specs/TD-225_Unified_Liquidation.md)

## 3. Implementation Roadmap

### Phase 1: Engine Decomposition (TD-238)
1. Create `simulation/orchestration/phases/` directory.
2. Extract each method in `phases.py` (e.g., `Phase_Production`, `Phase_Consumption`) into standalone classes/files.
3. Update `TickOrchestrator` to loop through these modular phase objects.

### Phase 2: Transaction & Inheritance Refactor (TD-232)
1. Modify `InheritanceManager.py` to stop using direct `settlement_system.transfer`.
2. Generate `Transaction(type="asset_liquidation")` and dispatch via `TransactionProcessor`.

### Phase 3: Sales Tax Atomicity (TD-231)
1. Inject `SALES_TAX_RATE` into `CommerceSystem.plan_consumption_and_leisure`.
2. Ensure the affordability check covers `Price * (1 + Tax)`.

### Phase 4: DTO & Liquidation Cleanup (TD-225/223)
1. Delete one of the redundant Loan DTOs and migrate all callers to the survivor.
2. Align `Firm` write-off logic with `LiquidationManager` sell-off logic.

## 4. Verification
- `pytest tests/unit/simulation/test_engine_structure.py`
- `trace_leak.py` must result in 0.0000 leak.
