# WO-083B: Test Migration - Phase 1 (Easy Targets)

## 🎯 Objective
Migrate "EASY" difficulty level tests from manual `MagicMock` setups to the new **Golden Fixture** system. This is the first step in stabilizing our test suite with realistic data.

> **Prerequisite**: WO-083A must be completed (Golden JSON files must exist).

---

## 🔨 Tasks
Replace manual mocks with `golden_households`, `golden_firms`, or `golden_config` fixtures in the following files.

### 1. Simple Data Containers
Target files identified by Gemini Audit:
- [ ] `tests/simulation/decisions/test_corporate_manager.py`
  - Replace `firm_mock` with `golden_firms[0]`.
- [ ] `tests/simulation/systems/test_generational_wealth_audit.py`
  - Replace `create_mock_household` helper with `golden_households`.
- [ ] `tests/simulation/decisions/test_household_decision_engine_new.py`
  - Replace `mock_household` with `golden_households[0]`.

### 2. AI & Component Tests
- [ ] `tests/simulation/systems/test_ai_training_manager.py` (and `_new.py`)
  - Replace `mock_agents` list with `golden_households`.
- [ ] `tests/simulation/components/test_agent_lifecycle.py`
  - Use `golden_households[0]` as the subject agent.
- [ ] `tests/simulation/components/test_demographics_component.py`
  - Use `golden_households[0]` to test demographic logic.

### 3. Verification Scripts
- [ ] `tests/verification/verify_automation_tax.py`
- [ ] `tests/verification/verify_leviathan.py`
  - Ensure these verification scripts run against the golden data snapshots instead of empty mocks.

---

## 🔍 Migration Pattern

**Before:**
```python
@pytest.fixture
def mock_household():
    agent = MagicMock(spec=Household)
    agent.id = 1
    agent.assets = 1000
    # ... 20 lines of setup
    return agent

def test_something(mock_household):
    ...
```

**After:**
```python
def test_something(golden_households):
    agent = golden_households[0] # Load real data
    # No manual setup needed
    ...
```

---

## ✅ Acceptance Criteria
1. [ ] All targeted tests pass with `pytest`.
2. [ ] No manual `MagicMock(spec=Household)` instantiation in the migrated test functions.
3. [ ] Test code size is reduced (removed setup boilerplate).
