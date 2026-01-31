# Work Order: - Iron Test Balancing

**Phase:** 21.5 (Stabilization)
**Date:** 2026-01-10
**Objective:** 자동화 도입에 따른 경제 붕괴 시나리오를 방지하기 위한 파라미터 튜닝.

---

## 1. Test Scenario (Stress Test)

| Parameter | Value |
|---|---|
| **Firms** | 50 |
| **Households** | 200 |
| **Duration** | 3650 Ticks (10 Years) |
| **FORMULA_TECH_LEVEL** | 1.0 (Max Labor Supply) |
| **AUTOMATION_COST** | Low (Initial) |

---

## 2. Key Metrics (Success Criteria)

| Metric | Threshold | Failure Condition |
|---|---|---|
| **Labor Share** | ≥ 30% | Falls below 30% → System Failure |
| **Unemployment Spike** | < 30% | Exceeds 30% for > 100 ticks |
| **Market Concentration** | Top 3 < 90% | Top 3 firms own > 90% market share |

---

## 3. Tuning Knobs

| Config Key | Description | Initial Value |
|---|---|---|
| `AUTOMATION_COST_PER_PCT` | Cost to increase automation 1% | 1000.0 |
| `AUTOMATION_LABOR_REDUCTION` | Alpha reduction factor | 0.5 |
| `HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD` | Market Cap threshold for hostile bid | 0.7 |

---

## 4. Deliverables

1. **Balanced Config**: `config.py` tuned for sustainable automation.
2. **Report**: `reports/iron_test_phase21_result.md` (Automation impact analysis).
3. **Dashboard Verification**: Run 1000 ticks via Cockpit, observe stability.

---

## 5. Verification Steps

```bash
# Run Iron Test Script
python scripts/iron_test.py --ticks 3650 --output reports/iron_test_phase21_result.md

# Key Assertions
- No population collapse (> 50 households survive)
- GDP stabilizes (no >50% drop)
- Labor Share remains > 30%
```
