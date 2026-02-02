# Mission Order: MISSION-F1-FIRM (1st Liquidation Phase)

**Task ID**: MISSION-F1-FIRM
**Target Spec**: `design/3_work_artifacts/specs/TD-067_Phase_BC_Firm_Refactor_Spec.md`
**Objective**: Eliminate Firm facade properties and enforce component-based state ownership.

## 📋 Instructions
1.  **Wrapper Removal**: Remove all 20+ `@property` wrappers from `simulation/firms.py` that proxy internal component state.
2.  **Encapsulation**: Implement investment and hiring APIs within `FinanceDepartment` and `HRDepartment` as specified.
3.  **Refactor CorporateManager**: Update `simulation/decisions/corporate_manager.py` to use `firm.finance.invest_in_automation()` instead of direct property manipulation.
4.  **Test Suite Adaptation**: Update `tests/test_corporate_manager.py` and `tests/test_firms.py` to interact with sub-components.
5.  **SoC Enforcement**: Ensure `Firm` class becomes a pure orchestrator of its departments.

## 🚨 Constraints
- Do NOT re-add any wrapper properties for "convenience".
- Do NOT touch Household or Housing modules.
- Ensure `verify_mitosis.py` passes to maintain golden data integrity.
