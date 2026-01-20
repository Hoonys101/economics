# WO-083C: Test Migration - Phase 2 (Medium Targets)

## 🎯 Objective
Migrate "MEDIUM" difficulty level tests from manual `MagicMock` setups to the **Golden Fixture** system. This continues the test suite stabilization effort.

> **Prerequisite**: WO-083B must be completed (EASY tests migrated).

---

## 🔨 Tasks

### Target Selection (5-7 files)
Select MEDIUM complexity tests that verify **individual module behavior** (NOT integration tests).

**Recommended Targets from Gemini Audit:**
- [ ] `tests/simulation/decisions/test_firm_decision_engine.py`
- [ ] `tests/simulation/test_firms.py`
- [ ] `tests/simulation/test_stock_market.py`
- [ ] `tests/verification/verify_inheritance.py`
- [ ] `tests/verification/verify_mitosis.py`
- [ ] `tests/api/test_dashboard_api.py`
- [ ] `tests/api/test_api_extensions.py`

### Migration Strategy

#### A. Data Injection Pattern
For tests requiring specific states (e.g., bankrupt firm, full inventory):

**Before:**
```python
firm = MagicMock()
firm.cash = 50  # Danger zone
```

**After:**
```python
def test_bankruptcy_danger(golden_firms):
    firm = golden_firms[0]
    firm.assets = 50  # Override for test scenario
    # Test logic...
```

#### B. Constraints
1. **NO production code changes** (`modules/`, `simulation/` core logic).
2. **Only modify test files** (`tests/`).
3. If test fails, adjust **test setup**, NOT golden data.

---

## ✅ Acceptance Criteria
1. [ ] 5-7 MEDIUM tests migrated to `golden_loader`.
2. [ ] All migrated tests pass with `pytest`.
3. [ ] No `MagicMock(spec=Firm)` or `MagicMock(spec=Household)` in migrated tests.
4. [ ] Test code size reduced (removed boilerplate).

---

## 🛠 Handover Note
After completion, we will have a **unified test safety net** ready for God Class refactoring (TD-065~067).
