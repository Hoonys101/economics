# Work Order: - Test Directory Refactoring

**Phase:** 2
**Priority:** HIGH
**Prerequisite:** None

## 1. Problem Statement
The `tests/` directory has grown organically, resulting in a flat structure that mixes unit tests, integration tests, API tests, and standalone verification scripts. This makes navigation difficult, test purposes unclear, and maintenance cumbersome. Duplicate and deprecated test files exist, creating confusion and redundancy.

## 2. Objective
Refactor the `tests/` directory into a clean, hierarchical structure based on testing scope (unit, integration, api, e2e). Deprecate old test files and move non-test verification scripts to a more appropriate location.

## 3. Target Metrics
| Metric | Current | Target |
|---|---|---|
| Test Directory Root File Count | >80 | <10 |
| Clarity of Test Purpose | Low | High |
| Redundant Test Files | >3 pairs | 0 |
| Verification Scripts in `tests/` | >20 | 0 |

## 4. Implementation Plan

Jules shall execute the following file move, merge, and delete operations.

### Track A: Move Standalone Verification Scripts

**Action:** Move all `verify_*.py` and other standalone scripts from `tests/` to a new `scripts/verification/` directory. After moving, update the `sys.path` modification in each script to be robust.

**Example `sys.path` fix:**
```python
# Replace this:
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# With this:
sys.path.append(str(Path(__file__).resolve().parent.parent))
```

**Files to Move:**
- `tests/verify_*.py` (all files starting with `verify_`)
- `tests/test_wo065_minimal.py`
- `tests/test_e2e_playwright.py` -> **Move to `tests/e2e/` instead.**

### Track B: Consolidate Duplicate/Deprecated Tests

**Action:** Merge the `_new.py` test files into their original counterparts and delete the `_new.py` and other deprecated files. The `_new` files contain the more modern DTO-based approach and should be preferred.

1. **AI Training Manager:**
 - Delete `tests/test_ai_training_manager.py`.
 - Rename `tests/test_ai_training_manager_new.py` to `tests/test_ai_training_manager.py`.
2. **Firm Decision Engine:**
 - Delete `tests/test_firm_decision_engine.py`.
 - Rename `tests/test_firm_decision_engine_new.py` to `tests/test_firm_decision_engine.py`.
3. **Household Decision Engine:**
 - Delete `tests/test_household_decision_engine_multi_good.py`.
 - Rename `tests/test_household_decision_engine_new.py` to `tests/test_household_decision_engine.py`.

### Track C: Restructure `tests/` Directory

**Action:** Create the new directory structure and move the remaining test files according to their scope.

**New Structure:**
```
tests/
├── unit/
│ ├── ai/
│ ├── components/
│ ├── decisions/
│ ├── domain/
│ ├── systems/
│ └── utils/
├── integration/
│ ├── ai/
│ ├── features/
│ ├── finance/
│ ├── government/
│ ├── scenarios/
│ └── systems/
├── api/
├── e2e/
└── goldens/
```

**Move Plan:**

1. **Create Directories:** Create the structure outlined above.
2. **Move existing test subdirectories** into `tests/unit/`:
 - `tests/agents/` -> `tests/unit/agents/`
 - `tests/components/` -> `tests/unit/components/`
 - `tests/modules/` -> `tests/unit/modules/`
 - `tests/systems/` -> `tests/unit/systems/`
 - `tests/utils/` -> `tests/unit/utils/`
 - `tests/diagnosis/` -> `tests/integration/diagnosis/`
3. **Move individual files:**
 - **Unit tests -> `tests/unit/`**:
 - `test_base_agent.py` -> `tests/unit/agents/`
 - `test_bank.py` -> `tests/unit/agents/`
 - `test_corporate_manager.py` -> `tests/unit/decisions/`
 - `test_household_marginal_utility.py` -> `tests/unit/decisions/`
 - `test_interest_sensitivity.py` -> `tests/unit/decisions/`
 - `test_purity_gate.py` -> `tests/unit/decisions/`
 - `test_learning_tracker.py` -> `tests/unit/ai/`
 - `test_ai_training_manager.py` (after rename) -> `tests/unit/ai/`
 - `test_household_system2.py` -> `tests/unit/ai/`
 - `test_socio_tech.py` -> `tests/unit/ai/`
 - `test_wo048_breeding.py` -> `tests/unit/ai/`
 - `test_marketing_roi.py` -> `tests/unit/components/`
 - `test_repository.py` -> `tests/unit/db/`
 - `test_logger.py` -> `tests/unit/utils/`
 - **Integration tests -> `tests/integration/`**:
 - `test_engine.py` -> `tests/integration/`
 - `test_decision_engine_integration.py` -> `tests/integration/ai/`
 - `test_firm_decision_engine.py` (after rename) -> `tests/integration/ai/`
 - `test_household_decision_engine.py` (after rename) -> `tests/integration/ai/`
 - `test_household_ai.py` -> `tests/integration/ai/`
 - `test_household_ai_consumption.py` -> `tests/integration/ai/`
 - `test_ai_driven_firm_engine.py` -> `tests/integration/ai/`
 - `test_government_ai_logic.py` -> `tests/integration/government/`
 - `test_phase*.py` (all) -> `tests/integration/scenarios/`
 - `test_stock_market.py` -> `tests/integration/finance/`
 - `test_portfolio_integration.py` -> `tests/integration/finance/`
 - `test_finance_bailout.py` -> `tests/integration/finance/`
 - `test_loan_market.py` -> `tests/integration/finance/`
 - `test_tax_collection.py`, `test_tax_incidence.py` -> `tests/integration/government/`
 - `test_fiscal_policy.py`, `test_government_fiscal_policy.py`, `test_government_tax.py` -> `tests/integration/government/`
 - `test_markets_v2.py`, `test_order_book_market.py` -> `tests/integration/systems/`
 - **API tests -> `tests/api/`**:
 - `test_app.py`
 - `test_api_history.py`
 - `test_api_extensions.py`
 - Move contents of `tests/api/` directory into the new root `tests/api/` directory.

## 5. Verification
- Run `pytest` and ensure all tests pass after the refactoring.
- Manually execute one of the moved verification scripts (e.g., `python scripts/verification/verify_gold_standard.py`) to ensure its `sys.path` logic is corrected and it runs without import errors.

## 6. Jules Assignment
| Track | Task | Files to Modify |
|---|---|---|
| A | Move verification scripts | `tests/verify_*.py`, `tests/test_wo065_minimal.py` |
| B | Consolidate duplicate tests | `tests/test_*_new.py`, `tests/test_*.py` |
| C | Restructure all other test files | All remaining files in `tests/` |
