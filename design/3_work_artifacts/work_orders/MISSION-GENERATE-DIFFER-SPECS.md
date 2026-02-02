# Mission: Generate Specs for 'Differ' Tech Debt Liquidation

**Objective**: Create detailed Specifications for liquidating 3 Active Tech Debts (TD-073, TD-005, TD-006) and 1 Compliance Debt (TD-122).

## 📂 Context Files
Read these files first to understand the current state:
- `design/TECH_DEBT_LEDGER.md` (Definitions)
- `simulation/firms.py` (For TD-073 Wrapper Bloat, TD-005 Visionary Halo)
- `simulation/components/finance_department.py` (For TD-073 ownership)
- `simulation/decisions/corporate_manager.py` (For TD-073 usage)
- `simulation/core_agents.py` (For TD-006 Static Personality)
- `tests/conftest.py` (For TD-122 structure)

## 📝 Tasks

### 1. Create `design/3_work_artifacts/specs/SPEC_TD073_FIRM_REFACTOR_V2.md`
- **Goal**: Full implementation plan to remove `@property` wrappers from `Firm` class.
- **Direction**:
    - `Firm` must become a pure Facade/Orchestrator.
    - All state access from `CorporateManager` must use `firm.finance.assets`, `firm.hr.employees` etc.
    - **No new convenience properties** allowed.
    - Define a `FirmStateDTO` that is a composite of Department DTOs.

### 2. Create `design/3_work_artifacts/specs/SPEC_TD005_HALO_LIQUIDATION.md`
- **Goal**: Remove hardcoded "Visionary" or "Halo" advantages (e.g., bankruptcy threshold doubling).
- **Direction**:
    - Locate `is_visionary` checking logic in `Firm` and remove it.
    - If `HRDepartment` or `LaborMarket` has preference logic for specific IDs, remove it.
    - Replace the advantage with a **Brand Awareness** check via `BrandManager`.
    - Firms with high brand recognition should naturally attract more talent/customers, not via hardcoded `if is_visionary:` checks.

### 3. Create `design/3_work_artifacts/specs/SPEC_TD006_DYNAMIC_PERSONALITY.md`
- **Goal**: Convert Static Personality to Dynamic Motivation.
- **Direction**:
    - Modify `Household` to update its `Personality` (values/needs) based on economic status.
    - Define thresholds:
        - Top 10% Wealth -> `STATUS_SEEKING` (Increases Luxury preference)
        - Bottom 20% Wealth or High Debt -> `SURVIVAL_MODE` (Decreases price sensitivity, increases savings preference)
    - Remove fixed `personality` init argument if it conflicts.

### 4. Create `design/3_work_artifacts/specs/SPEC_TD122_TEST_REORG.md`
- **Goal**: Gradual migration plan for tests.
- **Direction**:
    - Define the new directory structure: `tests/unit/`, `tests/integration/`, `tests/system/`.
    - Policy: New tests MUST go to new folders. Old tests migrated only when touched.
    - Define a `pytest.ini` update if needed.

## 🚀 Execution
Write these 4 files to disk. Ensure they follow the standard Spec template (Problem, Objective, Implementation Plan, Verification).
