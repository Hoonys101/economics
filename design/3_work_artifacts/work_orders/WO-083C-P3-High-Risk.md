# WO-083C-P3: Test Migration Phase 2 - HIGH Risk (Staged)

## 🎯 Objective
Migrate **HIGH risk** test `verify_mitosis.py` using a **staged approach** to isolate failure points.

> **Risk Level**: HIGH (per `design/gemini_output/audit_wo083c_risk.md`)

---

## 🔨 Target Test (1 file)

### `tests/verification/verify_mitosis.py`
**Current Setup:** Mocks `Config` and `DecisionEngine`.
**Risk:** HIGH - Deep interaction with `Household` God Class's `clone()` method + real `DecisionEngine`.

**Staged Migration Strategy:**

#### Stage 1: Golden Config Only
- Replace `Config` mock with `golden_config`.
- **Keep** `DecisionEngine` as `MagicMock`.
- Validate that `Household.clone()` works with complex golden data.

```python
def test_mitosis_stage1(golden_config, golden_households):
    household = golden_households[0]
    mock_engine = MagicMock(spec=DecisionEngine)
    
    # Test clone logic
    child_firm = household.clone()
    assert child_firm is not None
```

#### Stage 2: Real DecisionEngine (Separate Test)
- After Stage 1 passes, introduce **real** `DecisionEngine`.
- This isolates failures: if Stage 2 fails, it's the engine, not the clone logic.

```python
def test_mitosis_stage2(golden_config, golden_households):
    household = golden_households[0]
    real_engine = DecisionEngine(golden_config)
    household.decision_engine = real_engine
    
    # Test with real engine
    child_firm = household.clone()
    assert child_firm.decision_engine is not None
```

---

## Constraints

1. **NO production code changes**.
2. **Staged approach**: Two separate test functions.
3. **Circular dependency awareness**: `Household.clone()` is part of `Household` class itself.

---

## Verification

Run: `pytest tests/verification/verify_mitosis.py -v`

Both stages must pass.
