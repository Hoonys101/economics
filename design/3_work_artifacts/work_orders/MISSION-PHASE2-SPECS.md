# Mission: Plan Phase 2 Tech Debt Liquidation

**Objective**: Create specifications for the next critical liquidation phase, focusing on **Housing Market Repair** and **Household Architecture**.

## 📂 Context
- **Current Status**: Phase 1 (Firm Refactor, Halo, Personality) is nearing completion.
- **Top Priority**: The Housing Market is functionally broken (Orphaned Logic).
- **Secondary Priority**: `Household` class is maintaining the same "God Class" pattern that `Firm` just resolved.

## 📝 Tasks

### 1. Create `design/3_work_artifacts/specs/spec_td065_housing_planner.md`
- **Target**: **HousingRefactor** (Critical) & **TD-065**.
- **Context**: The `HousingSystem` currently has "orphaned" mortgage logic, and `DecisionUnit` duplicates housing decision logic.
- **Goal**:
    - Centralize all housing decision logic into a `HousingPlanner` (Stateless, Functional).
    - Ensure `DecisionUnit` calls this planner via `HousingMarket.make_offer` or similar DTO-based interface.
    - Re-integrate the Mortgage/Loan creation logic that was being bypassed.
- **Direction**: "One Logic, One Path". Ensure the transaction handler actually calls the mortgage system.

### 2. Create `design/3_work_artifacts/specs/TD-065_Household_Refactor_Spec.md`
- **Target**: **TD-162** (Bloated God Class: Household).
- **Context**: `Household` agent is 900+ lines. It needs the same treatment as `Firm` (TD-073).
- **Goal**: Decompose `Household` into:
    - `BioComponent` (Needs, Age, Life)
    - `EconComponent` (Assets, Income, Work)
    - `SocialComponent` (Personality, Relationships - *Already started in TD-006*)
- **Direction**:
    - `Household` becomes a Facade.
    - Remove all `@property` delegates (e.g., `household.assets` -> `household.econ.assets`).
    - **Note**: This is a massive refactor. Plan it in 2 stages: (A) Component Extraction, (B) Property Removal.

### 3. Verification Strategy
- Define how to verify the Housing Market repair (e.g., "Mortgage Count > 0" metric).
- Define `verify_mitosis.py` equivalent for Household decomposition.

## 🚀 Execution
Generate these 2 key specifications.
