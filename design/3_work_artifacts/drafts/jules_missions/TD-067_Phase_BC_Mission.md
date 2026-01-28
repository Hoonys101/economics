# TD-067 Phase B/C: Firm Facade Deconstruction

## Context
You are continuing the TD-067 refactoring work. **Phase A (FinanceDepartment Extraction) has been successfully merged**. Your task is to complete **Phase B (Remove Wrapper Properties)** and **Phase C (Reduce CorporateManager Coupling)**.

## Critical Instructions

### ⚠️ SoC Preservation (MANDATORY)
**DO NOT regress to God Class pattern.** The codebase has undergone extensive SoC refactoring:
- `Simulation` → `WorldState`, `TickScheduler`, `ActionProcessor` (TD-066)
- `Household` → `BioComponent`, `EconComponent`, `SocialComponent` (TD-065)
- `Firm` → `HRDepartment`, `FinanceDepartment`, `ProductionDepartment`, `SalesDepartment` (TD-067 Phase A)

**You MUST maintain this architecture.** Do not create wrapper properties or consolidate logic back into `Firm`.

### 📋 Pre-Merge Checklist (You MUST confirm in PR description)
- [ ] Zero `@property` wrappers in `Firm` class
- [ ] All `CorporateManager` methods use encapsulation APIs
- [ ] `tests/test_corporate_manager.py` passes
- [ ] `tests/verification/verify_mitosis.py` passes (Golden Fixture compatibility)
- [ ] No direct `firm.assets` access outside `FinanceDepartment`

---

## Task Specification

Read the full specification at: `design/specs/TD-067_Phase_BC_Firm_Refactor_Spec.md`

### Summary of Work

#### Track B: Eliminate Wrapper Properties
1. Remove **all 20+ `@property` wrappers** from `simulation/firms.py` (lines 181-299)
2. Move logic to components:
   - `calculate_valuation()` → `FinanceDepartment`
   - `get_book_value_per_share()` → `FinanceDepartment`
   - `get_financial_snapshot()` → `FinanceDepartment`

#### Track C: Reduce CorporateManager Coupling
1. Add encapsulation methods to `FinanceDepartment`:
   - `invest_in_automation(amount: float) -> bool`
   - `invest_in_rd(amount: float) -> bool`
   - `invest_in_capex(amount: float) -> bool`
   - `set_dividend_rate(rate: float) -> None`

2. Refactor `simulation/decisions/corporate_manager.py`:
   - Replace `firm.assets -= budget` → `firm.finance.invest_in_automation(budget)`
   - Replace `firm.dividend_rate = x` → `firm.finance.set_dividend_rate(x)`
   - Update methods: `_manage_automation`, `_manage_r_and_d`, `_manage_capex`, `_manage_dividends`, `_manage_hiring`

#### Track D: Refactor All Call Sites
1. Update `tests/test_corporate_manager.py`:
   - Mock sub-components: `firm_mock.finance.assets = 10000.0`
   - Update assertions: `assert firm_mock.finance.assets == expected`

2. Update `tests/test_firms.py`:
   - Call `firm.finance.get_book_value_per_share()` instead of `firm.get_book_value_per_share()`

3. Update `Firm` internal methods:
   - `make_decision()`, `get_agent_data()`, `update_needs()` → access sub-components directly

---

## Verification Requirements

### Must Pass
- `pytest tests/test_corporate_manager.py` ✅
- `pytest tests/test_firms.py` ✅
- `pytest tests/verification/verify_mitosis.py` ✅ (Golden Fixture gate check)
- `ruff check simulation/` (no unused imports)

### Manual Checks
- Grep for `firm.assets` outside `FinanceDepartment` → should return 0 results (except in tests)
- Grep for `@property` in `Firm` class → should return 0 results

---

## Reference Documents
- **Spec**: `design/specs/TD-067_Phase_BC_Firm_Refactor_Spec.md` (FULL DETAILS)
- **Template**: `design/specs/TD-065_Household_Refactor_Spec.md` (Similar refactoring pattern)
- **Handover Warning**: `design/handovers/HANDOVER_2026-01-20.md` (Jules regression alert)
- **Tech Debt**: `design/TECH_DEBT_LEDGER.md` (TD-067 entry)

---

## Success Criteria
✅ All wrapper properties removed
✅ `CorporateManager` uses encapsulation methods only
✅ All tests pass (including Golden Fixtures)
✅ No God Class regression (verified by code review)
✅ Pre-merge checklist confirmed in PR description
