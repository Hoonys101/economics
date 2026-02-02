# TD-162_Household_Refactor_Spec.md

# TD-162: Household God Class Decomposition (Stage B)

- **Mission**: Liquidate `TD-162` technical debt.
- **Objective**: Complete the decomposition of the `Household` agent by executing **Stage B**: the removal of all property delegates. This will enforce architectural separation by forcing all other modules to interact with the `Household`'s state via its constituent components (`bio`, `econ`, `social`) and their respective state DTOs.

---

## 1. Refactoring Plan: Stage B - Property Delegate Removal

This is a high-impact, "stop-the-world" refactoring. The process must be systematic to manage the widespread, cascading changes.

### Step 1: Full-Scale Call Site Analysis
- **Action**: Use `ripgrep` to find every usage of a `Household` property delegate across the entire project.
- **Command**: `rg "household\.(assets|age|is_employed|personality|...)"` (with the full list of properties from `core_agents.py`).
- **Output**: A comprehensive file (`refactor_call_sites.log`) listing every file and line number that needs modification. This log will serve as our checklist.

### Step 2: Phased Property Group Removal & Code Modification
The removal will be done in three phases, grouped by component. For each phase:
1.  Remove the `@property` definitions from `simulation/core_agents.py`.
2.  Work through the `refactor_call_sites.log` to fix all resulting `AttributeError` exceptions.

**Phase 2A: EconComponent Properties**
- **Properties to Remove**: `assets`, `inventory`, `is_employed`, `employer_id`, `current_wage`, `labor_skill`, `portfolio`, `owned_properties`, `is_homeless`, etc.
- **Replacement Pattern**:
  - `household.assets` -> `household._econ_state.assets`
  - `household.is_employed` -> `household._econ_state.is_employed`
  - `if household.is_homeless:` -> `if household._econ_state.is_homeless:`

**Phase 2B: BioComponent Properties**
- **Properties to Remove**: `age`, `gender`, `parent_id`, `generation`, `is_active`, `needs`, etc.
- **Replacement Pattern**:
  - `household.age` -> `household._bio_state.age`
  - `household.needs` -> `household._bio_state.needs`

**Phase 2C: SocialComponent Properties**
- **Properties to Remove**: `personality`, `social_status`, `discontent`, `conformity`, `optimism`, `ambition`, etc.
- **Replacement Pattern**:
  - `household.personality` -> `household._social_state.personality`
  - `household.social_status` -> `household._social_state.social_status`

*Note: After this refactor, a follow-up task should be considered to make the component state DTOs (`_bio_state`, etc.) public (`bio_state`).*

### Step 3: Script-Assisted Refactoring (Optional but Recommended)
- **Action**: Create a Python script (`scripts/refactor_household_access.py`) that uses file I/O and string replacement to automate the most common substitutions.
- **Example**:
  ```python
  # scripts/refactor_household_access.py
  replacements = {
      "household.assets": "household._econ_state.assets",
      "household.age": "household._bio_state.age",
      # ... and so on
  }
  # ... logic to iterate files and perform replacement ...
  ```
- **Caution**: This script must be used with care and changes reviewed via `git diff` before committing.

---

## 2. API Definition Changes

-   **File**: `simulation/core_agents.py`
-   **Change**: This work does not create a new API, but **destroys an existing implicit one**. All `@property` methods delegating to `_bio_state`, `_econ_state`, and `_social_state` will be **deleted**.
-   **New Contract**: Any external module needing to access `Household` state **MUST** do so through the component state DTOs. For example: `household._econ_state.assets`. The `Household` class itself will no longer expose these fields directly.

---

## 3. Verification Plan

This refactor will cause massive, predictable test failures. The verification plan is focused on managing this fallout efficiently.

-   **New Script**: `scripts/verify_household_decomposition.py`.
-   **Methodology**:
    1.  The script will first run `pytest --collect-only -q`. This is a fast way to catch all `AttributeError` and `SyntaxError` issues at the module level without running any test logic.
    2.  Once collection passes, the script will execute the full `pytest` suite.
    3.  A log of all failing tests (`test_failures_household_refactor.log`) will be generated.
-   **Triage Strategy**:
    1.  **Fix Core Systems First**: Prioritize fixing test failures in core infrastructure, systems, and markets (`tests/simulation/`, `tests/systems/`, `tests/markets/`).
    2.  **Tackle Mock-Related Failures**: A significant number of failures will be due to `unittest.mock.patch` targeting the now-deleted properties (e.g., `@patch('...Household.assets', new_callable=PropertyMock)`). These must be updated to patch the DTO attributes instead (e.g., `@patch.object(EconStateDTO, 'assets', ...)`), or preferably, refactored to use golden data fixtures.
    3.  **Fix Agent-Level Tests**: Finally, fix the higher-level agent decision-making tests.

---

## 4. Risk & Impact Audit

-   **Primary Risk (CRITICAL)**: **Widespread Codebase Breakage**. This is the intended outcome, but the scale requires a meticulous, checklist-driven approach (`refactor_call_sites.log`) to ensure all call sites are updated. Any missed site is a guaranteed runtime bug.
-   **Test Impact (EXTREME)**: A significant percentage (estimated 40-60%) of the test suite will fail. The primary challenge is not the complexity of the fix (most are simple substitutions), but the sheer volume. The risk is that a subtle bug is introduced while fixing a failing test.
-   **Precedent**: This operation is a direct successor to the `Firm` refactor (TD-073). The lessons learned there (e.g., the need for systematic call site analysis, the pain of mock-heavy tests) are directly applicable here.
-   **Recommendation**: This refactoring should be performed on a dedicated branch and should be the only major change in its associated Pull Request to simplify code review. All other feature development should be paused until this debt is liquidated.
