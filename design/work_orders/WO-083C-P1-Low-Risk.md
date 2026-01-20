# WO-083C-P1: Test Migration Phase 2 - LOW Risk Batch

## 🎯 Objective
Migrate **LOW risk** MEDIUM complexity tests to Golden Fixtures as the first safe batch of WO-083C.

> **Risk Level**: LOW (per `design/gemini_output/audit_wo083c_risk.md`)

---

## 🔨 Target Tests (2 files)

### 1. `tests/simulation/test_stock_market.py`
**Current Setup:** Mocks `Config` and `Firm`.
**Migration:**
- Replace `Config` mock with `golden_config`.
- Replace `Firm` mock with `golden_firms[0]`.
- Use **State Override Pattern** to set `firm.cash` or `firm.shares` for test preconditions.

**Risk:** LOW - Isolated market logic test.

### 2. `tests/api/test_api_extensions.py`
**Current Setup:** Mocks `Repo`, `Household`, `Firm`, `Market`.
**Migration:**
- Replace `Household`/`Firm` mocks with `golden_households[0]` and `golden_firms[0]`.
- Keep `Repo`/`Market` as lightweight mocks (infrastructure).
- Make ViewModel logic **defensive** to handle potentially `None` attributes from golden fixtures.

**Risk:** LOW - ViewModel logic test, minimal state dependency.

---

## Migration Pattern

```python
# Before
@pytest.fixture
def mock_firm():
    firm = MagicMock(spec=Firm)
    firm.cash = 1000
    return firm

# After
def test_something(golden_firms):
    firm = golden_firms[0]
    firm.cash = 1000  # State Override if needed
    # Test logic...
```

---

## Constraints

1. **NO production code changes**.
2. **State Override Pattern**: Override attributes AFTER loading golden data.
3. **Preserve test logic**: Do not change assertions.

---

## Verification

Run: `pytest tests/simulation/test_stock_market.py tests/api/test_api_extensions.py -v`

All tests must pass.
