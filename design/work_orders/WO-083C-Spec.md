# WO-083C Implementation Spec: Test Migration Phase 2

## Target Tests (5 MEDIUM Complexity)

Based on Gemini Audit, the following tests are selected for migration:

### 1. `tests/simulation/test_stock_market.py`
**Current Setup:** Mocks `Config` and `Firm` instances.
**Migration:** Replace with `golden_firms` and `golden_config`.
**Risk:** LOW - Isolated market logic test.

### 2. `tests/verification/verify_inheritance.py`
**Current Setup:** Manually creates `deceased` and `heir` mock households.
**Migration:** Use `golden_households[0]` and `golden_households[1]`.
**Risk:** MEDIUM - Tests wealth transfer logic, ensure golden data has sufficient assets.

### 3. `tests/verification/verify_mitosis.py`
**Current Setup:** Mocks `Config` and `DecisionEngine`.
**Migration:** Replace with `golden_config` and attach real `DecisionEngine` to golden household.
**Risk:** MEDIUM - Firm creation logic, may need specific market conditions.

### 4. `tests/api/test_dashboard_api.py`
**Current Setup:** Mocks `Repo`, `Sim`, `Trackers`, `Govt`, `Stock`.
**Migration:** Use `golden_households`, `golden_firms`, and create lightweight mocks for infrastructure (Repo, Trackers).
**Risk:** MEDIUM - Dashboard snapshot test, verify JSON structure compatibility.

### 5. `tests/api/test_api_extensions.py`
**Current Setup:** Mocks `Repo`, `Household`, `Firm`, `Market`.
**Migration:** Replace household/firm mocks with golden fixtures, keep Repo/Market as lightweight mocks.
**Risk:** LOW - ViewModel logic test, minimal state dependency.

---

## Migration Pattern

### Before:
```python
@pytest.fixture
def mock_firm():
    firm = MagicMock(spec=Firm)
    firm.id = 1
    firm.cash = 1000
    firm.employees = []
    return firm

def test_something(mock_firm):
    result = calculate_value(mock_firm)
    assert result == expected
```

### After:
```python
def test_something(golden_firms):
    firm = golden_firms[0]
    # Override if needed for specific test scenario
    firm.cash = 1000
    result = calculate_value(firm)
    assert result == expected
```

---

## Constraints

1. **NO production code changes** - Only modify test files.
2. **State Override Pattern** - If golden data doesn't match test requirements, override attributes AFTER loading.
3. **Preserve Test Logic** - Do not change assertions or test intent.

---

## Verification

Run `pytest tests/simulation/test_stock_market.py tests/verification/verify_inheritance.py tests/verification/verify_mitosis.py tests/api/test_dashboard_api.py tests/api/test_api_extensions.py -v` after migration.

All tests must pass.
