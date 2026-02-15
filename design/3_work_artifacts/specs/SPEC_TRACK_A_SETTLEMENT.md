# Mission Guide: Track A - Settlement & Logic Purity

## 1. Objectives
- **TD-CRIT-FLOAT-SETTLE**: Fix critical float leak by ensuring all engine result DTOs use `int` (pennies).
- **TD-INT-PENNIES-FRAGILITY**: Refactor `Firm` to prioritize `IFinancialEntity` (Pennies) and deprecate `IFinancialAgent` (Floats).

## 2. Reference Context (MUST READ)
- **Primary Spec**: `design/3_work_artifacts/specs/RESOLUTION_STRATEGY_PHASE_18.md` (Sections 2 & 4)
- **Affected Files**:
    - `modules/firm/api.py` (DTO definitions)
    - `simulation/firms.py` (Firm class & Protocols)
    - `simulation/engines/production_engine.py` (Logic implementation)
    - `simulation/engines/asset_management_engine.py` (Logic implementation)

## 3. Implementation Roadmap
### Phase 1: DTO & Engine Refactor
- Update `ProductionResultDTO` and `LiquidationResultDTO` in `modules/firm/api.py` to use `int` for penny fields.
- Update `ProductionEngine` and `AssetManagementEngine` to cast final results to `int` (using `math.ceil` for costs).
### Phase 2: Firm Orchestrator Update
- Remove manual `int()` casts in `Firm` when calling `SettlementSystem`.
- Implement `IFinancialEntity` properties.
- Mark `IFinancialAgent` methods as deprecated.

## 4. Verification
- Run: `pytest tests/modules/firm/test_production_int_cost.py`
- Run: `pytest tests/simulation/test_settlement_types.py`
