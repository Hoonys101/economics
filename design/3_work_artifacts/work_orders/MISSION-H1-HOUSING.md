# Mission Order: MISSION-H1-HOUSING (1st Liquidation Phase)

**Task ID**: MISSION-H1-HOUSING
**Target Spec**: `design/3_work_artifacts/specs/spec_td065_housing_planner.md`
**Objective**: Decouple housing decision logic into a stateless `HousingPlanner`.

## 📋 Instructions
1.  **Stateless Planner**: Implement `HousingPlanner` in `modules/housing/planner.py` based on the spec. It must be a pure function/stateless component.
2.  **DTO Implementation**: Create necessary DTOs in `modules/housing/api.py` as defined in the spec.
3.  **Orchestration Update**: Update `simulation/core_agents.py` and `DecisionUnit` to use the new `HousingPlanner` for housing decisions.
4.  **Decoupling**: Remove raw housing market access where possible, funneling data through the new DTO interfaces.
5.  **Verification**: 
    - Ensure all existing tests pass.
    - Create a unit test for `HousingPlanner` logic.
    - Verify with `pytest tests/integration/test_td194_integration.py` (ensure no regressions in DTO handling).

## 🚨 Constraints
- Do NOT modify Firm or unrelated Household state.
- Strictly adhere to `MarketSnapshotDTO` for market inputs.
- Log any technical debt found in a new insight report.
