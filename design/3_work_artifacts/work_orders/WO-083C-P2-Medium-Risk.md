# WO-083C-P2: Test Migration Phase 2 - MEDIUM Risk Batch

## 🎯 Objective
Migrate **MEDIUM risk** MEDIUM complexity tests to Golden Fixtures as the second batch of WO-083C.

> **Risk Level**: MEDIUM (per `design/gemini_output/audit_wo083c_risk.md`)

---

## 🔨 Target Tests (2 files)

### 1. `tests/verification/verify_inheritance.py`
**Current Setup:** Manually creates `deceased` and `heir` mock households.
**Migration:**
- Use `golden_households[0]` (deceased) and `golden_households[1]` (heir).
- **Pre-test validation**: Assert that selected households have **sufficient and diverse assets** (positive cash, shares, debt) to robustly test wealth transfer logic.

**Risk:** MEDIUM - Tests wealth transfer logic, ensure golden data has sufficient assets.

**Mitigation:**
```python
def test_inheritance(golden_households):
    deceased = golden_households[0]
    heir = golden_households[1]
    
    # Pre-test validation
    assert deceased.assets > 0, "Deceased must have assets"
    assert hasattr(deceased, 'portfolio'), "Deceased must have portfolio"
    
    # Test logic...
```

### 2. `tests/api/test_dashboard_api.py`
**Current Setup:** Mocks `Repo`, `Sim`, `Trackers`, `Govt`, `Stock`.
**Migration:**
- Replace `mock_households` and `mock_firms` with `golden_households` and `golden_firms`.
- Keep infrastructure mocks (`Repo`, `Trackers`) as lightweight.
- **Create golden JSON snapshot**: Save expected API output to `tests/goldens/dashboard_snapshot.json` and compare against it to detect structural regressions.

**Risk:** MEDIUM - Dashboard snapshot test, verify JSON structure compatibility.

**Mitigation:**
```python
def test_dashboard_snapshot(golden_households, golden_firms):
    # Generate API response
    response = dashboard_api.get_snapshot(golden_households, golden_firms)
    
    # Load expected snapshot
    with open("tests/goldens/dashboard_snapshot.json") as f:
        expected = json.load(f)
    
    assert response == expected, "Dashboard structure changed"
```

---

## Migration Pattern

Same as P1: Load golden data → Override state if needed → Run test.

---

## Constraints

1. **NO production code changes**.
2. **Pre-test validation** for `verify_inheritance.py`.
3. **Golden snapshot** for `test_dashboard_api.py`.

---

## Verification

Run: `pytest tests/verification/verify_inheritance.py tests/api/test_dashboard_api.py -v`

All tests must pass.
