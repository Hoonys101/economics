# WO-083A: Golden Fixture Generation

## 🎯 Objective
Run the existing simulation engine to generate **"Golden Fixtures"** (verified clean JSON data) using the newly refactored `Bank` logic. These files will be the foundation for all future tests.

---

## 🔨 Tasks

### 1. Fix `scripts/generate_golden_fixtures.py`
- Ensure it imports `Simulation` correctly (handle `sys.path` issue if needed).
- Update logic to handle any API changes from `WO-081` (Bank Refactor), although the Simulation engine should already handle this.
- Add robust error handling to print logs if generation fails.

### 2. Generate Files
Run the script to produce the following in `tests/goldens/`:
- `initial_state.json` (Tick 0)
- `early_economy.json` (Tick 10)
- `stable_economy.json` (Tick 100)

### 3. Verify `conftest.py` Integration
- Create a temporary verification script `verify_golden_load.py` that:
  - Uses `tests.utils.golden_loader.GoldenLoader`.
  - Loads `tests/goldens/stable_economy.json`.
  - Asserts that loaded objects are `MagicMock` instances.
  - Asserts that `mock_agent.demographics.age` exists and matches the JSON.

---

## ✅ Acceptance Criteria
1. [ ] `scripts/generate_golden_fixtures.py` runs successfully without error.
2. [ ] `tests/goldens/*.json` files are created and populated with data.
3. [ ] `verify_golden_load.py` passes, confirming the data is loadable by our tooling.
4. [ ] No "TOKEN/SECRET" leaks in the JSON files.

---

## 🛠 Handover Note
Once this is done, we will proceed to WO-083B (Test Migration).
