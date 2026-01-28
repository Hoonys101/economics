# Work Order: WO-052-Social-Mobility-Analysis (The Dynasty Report)

**Date:** 2026-01-12
**Phase:** Phase 22 (Completion)
**Assignee:** Jules (Worker AI)
**Objective:** 최적화된 엔진을 장기간(1,000 Ticks) 가동하여, 부모의 경제력이 자녀에게 세습되는 정도(Intergenerational Mobility)를 정량적으로 분석한다.

## 1. Core Component: MobilityTracker

새로운 파일 `simulation/metrics/mobility_tracker.py`를 생성하고 다음 인터페이스를 구현하라.

```python
import numpy as np
from typing import Dict

class MobilityRecord:
    def __init__(self, parent_id: int, child_id: int, parent_wealth_at_birth: float):
        self.parent_id = parent_id
        self.child_id = child_id
        self.parent_wealth = parent_wealth_at_birth
        self.child_wealth = 0.0
        self.is_complete = False

class MobilityTracker:
    def __init__(self):
        self.records: Dict[int, MobilityRecord] = {} # Key: child_id

    def register_birth(self, parent_id: int, child_id: int, parent_wealth: float):
        """자녀 출생 시 부모의 현재 자산을 기록합니다."""
        self.records[child_id] = MobilityRecord(parent_id, child_id, parent_wealth)

    def record_final_wealth(self, child_id: int, wealth: float):
        """자녀 사망 시 또는 시뮬레이션 종료 시 자녀의 최종 자산을 기록합니다."""
        if child_id in self.records:
            self.records[child_id].child_wealth = wealth
            self.records[child_id].is_complete = True

    def calculate_ige(self) -> float:
        """
        IGE (Intergenerational Income Elasticity) 계산.
        산식: log(Child_Wealth + 1) = alpha + Beta * log(Parent_Wealth + 1)
        Beta (IGE) = Cov(log_p, log_c) / Var(log_p)
        """
        valid_data = [
            (np.log(r.parent_wealth + 1), np.log(r.child_wealth + 1))
            for r in self.records.values() if r.is_complete and r.parent_wealth > 0
        ]
        
        if len(valid_data) < 2:
            return 0.0
            
        x, y = zip(*valid_data)
        return float(np.cov(x, y)[0, 1] / np.var(x))
```

## 2. Integration Requirements

1.  **DemographicManager (`simulation/systems/demographic_manager.py`)**:
    *   `process_births` 내에서 **상속 gift(10%)가 차감되기 직전**의 부모 자산을 `mobility_tracker.register_birth`로 기록하라.
2.  **Simulation Engine (`simulation/engine.py`)**:
    *   `self.mobility_tracker = MobilityTracker()`를 초기화하라.
    *   에이전트가 사망(`is_active=False`) 시점에, **InheritanceManager가 자산을 영(0)으로 만들기 직전**의 최종 자산을 `record_final_wealth`에 반영하라.
3.  **Experiment Script (`scripts/experiments/dynasty_report.py`)**:
    *   초기 인구 50명으로 1,000틱 시뮬레이션을 Headless 모드로 구동하는 스크립트를 작성하라.
    *   **Engine Stability**: 기본 `config.py`를 사용하되, 시뮬레이션이 경제 붕괴(Population < 5)로 조기 종료될 경우 `WAGE_DECAY_RATE`를 0.01로 완화하거나 `GOVERNMENT_UNEMPLOYMENT_BENEFIT`을 상향 조정하는 `STABILITY_PATCH` 모드를 활성화할 수 있다.
    *   종료 시 살아있는 모든 에이전트의 현재 자산을 `record_final_wealth`에 반영한 후, IGE 성적표를 출력하라.

## 3. Deliverables

Jules는 시뮬레이션 종료 후 다음 결과를 **`reports/dynasty_report_20260112.md`** 파일로 생성해야 한다.
1.  **Survival Rate**: 1,000틱 이후 생존 인구수 및 세대별 인구 분포.
2.  **IGE Metric**:
    - 계산된 IGE 값 ($\beta$).
    - 결정계수 ($R^2$) - 데이터의 설명력 확인용.
3.  **The Verdict**: IGE 값에 따른 사회 계층 고착화 진단.
4.  **ASCII/Log Scatter Plot**: 부모 자산(log) vs 자녀 자산(log)의 분포를 Markdown 코드 블록 내에 시각화하라.

## 4. Acceptance Criteria
- 1,000틱 완주 성공.
- IGE 수치가 0.0 ~ 1.2 사이의 값으로 출력됨.
- `simulation.mobility_tracker`가 메모리 누수 없이 데이터를 수집함.
