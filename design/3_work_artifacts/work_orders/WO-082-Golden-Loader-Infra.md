# WO-082: Golden Loader Infrastructure

## 🎯 Objective
Develop a robust **Golden Loader Utility** that converts simple JSON data into powerful `MagicMock` objects for testing. This infrastructure will be used to load the fixtures generated later.

> **Warning**: Do NOT modify `simulation/` code. Work ONLY in `scripts/` or `tests/utils/`. This task must be parallel-safe with `WO-081`.

---

## 🔨 Tasks

### 1. Create `tests/utils/golden_loader.py`
Implement a `GoldenLoader` class with the following features:

- **`load_json(path: str) -> Dict`**: Safely loads JSON files from `tests/goldens/`.
- **`dict_to_mock(data: Dict, spec: Type = None) -> MagicMock`**:
  - Recursively converts nested dictionaries into nested `MagicMock` objects.
  - If `spec` is provided (e.g., `Household` class), ensures the Mock respects the class interface (`spec=class`).
  - Handles lists of objects correctly (returns list of Mocks).

### 2. Unit Testing for Loader
Create `tests/utils/test_golden_loader.py`:
- Verify that a sample JSON dict is correctly converted to a Mock.
- Verify that accessing `mock.attribute` returns the correct value from JSON.
- Verify nested access (e.g., `agent.demographics.age`).

### 3. Integration with `fixture_harvester.py`
- Refactor `scripts/fixture_harvester.py` to Use this new `GoldenLoader` logic if applicable, OR keep them separate if `fixture_harvester.py` is purely for saving.
- Ideally, `fixture_harvester.py` handles **saving** (Capturing), and `GoldenLoader` handles **loading** (Replaying).

---

## ✅ Acceptance Criteria

1. [ ] `GoldenLoader` correctly converts nested JSON to nested MagicMocks.
2. [ ] `tests/utils/test_golden_loader.py` passes.
3. [ ] No dependency on `simulation` logic (except importing classes for `spec` arguments if needed).
4. [ ] Zero modifications to `simulation/bank.py` or `simulation/core_agents.py`.

---

## 💡 Technical Note
- Use `unittest.mock.MagicMock`.
- Focus on Developer Experience: The loader should be easy to use in `conftest.py`.
