# Work Order: Laffer Curve Experiment Completion

**To**: Jules (Implementer)  
**From**: Antigravity (Team Leader)  
**Date**: 2025-12-31  
**Subject**: Finalize Experiment Infrastructure (Operation Proving Ground)

---

## 1. Context & Status

| 항목 | 상태 |
|------|------|
| **Phase 5** (Time Allocation) | ✅ Completed & Merged |
| **Experiment Infrastructure** | ✅ Pushed by Team Leader |
| **Your Task** | Integrate & Run Experiment |

**목표**: 세율(0.1 → 0.9)에 따른 **래퍼 곡선(Laffer Curve)** 검증.

---

## 2. Pre-Work

```bash
git pull origin main
```

확인 파일:
- `config.py` - `TAX_MODE`, `BASE_INCOME_TAX_RATE`, `RANDOM_SEED`
- `simulation/dtos.py` - `time_worked`, `time_leisure`
- `experiments/run_lab_laffer.py` - 실험 러너 스켈레톤

---

## 3. Implementation Tasks

| # | 파일 | 작업 |
|---|------|------|
| 1 | `main.py` | `create_simulation(overrides)` 팩토리 함수 추가 |
| 2 | `government.py` | `calculate_income_tax`에 FLAT 모드 추가 |
| 3 | `engine.py` | `time_worked`, `time_leisure` DTO 기록 |
| 4 | `run_lab_laffer.py` | 팩토리 연동 및 실행 테스트 |

---

## 4. Logic Details

### A. Factory Function (main.py)
```python
def create_simulation(overrides: Dict[str, Any] = None) -> Simulation:
    if overrides:
        for key, value in overrides.items():
            setattr(config, key, value)
    random.seed(config.RANDOM_SEED)
    # ... existing init ...
    return sim
```

### B. Flat Tax Logic (government.py)
```python
def calculate_income_tax(self, income: float, survival_cost: float) -> float:
    tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")
    if tax_mode == "FLAT":
        return income * getattr(self.config_module, "BASE_INCOME_TAX_RATE", 0.2)
    # else: existing progressive logic
```

### C. Time Tracking (engine.py)
```python
agent_data = AgentStateData(
    ...
    time_worked=household_time_allocation.get(agent.id, 0.0),
    time_leisure=config.HOURS_PER_TICK - time_worked - config.SHOPPING_HOURS,
)
```

---

## 5. Verification

```bash
python experiments/run_lab_laffer.py
```

Output: `results/laffer_experiment.csv`

**Expected**: Revenue peaks ~50% tax rate, then declines (Inverted U-curve).

---

## 6. Constraints

- ❌ 대시보드 수정 불필요
- ✅ `RANDOM_SEED = 42` 고정
- ✅ 부유세 0% 고정

**Execute and report CSV results.** 📊
