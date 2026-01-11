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
    *   `process_births` 시점에 `simulation.mobility_tracker.register_birth`를 호출하여 부모 자산을 기록하라.
2.  **Simulation Engine (`simulation/engine.py`)**:
    *   `self.mobility_tracker = MobilityTracker()`를 초기화하라.
    *   에이전트가 사망(`is_active=False`) 시점에 `mobility_tracker.record_final_wealth`를 호출하라.
3.  **Experiment Script (`scripts/experiments/dynasty_report.py`)**:
    *   초기 인구 50명으로 1,000틱 시뮬레이션을 Headless 모드로 구동하는 스크립트를 작성하라.
    *   종료 시 살아있는 모든 에이전트의 현재 자산을 `record_final_wealth`에 반영한 후, IGE 성적표를 출력하라.

## 3. Deliverables

Jules는 다음 결과를 로그 또는 파일로 산출해야 한다.
1.  **Survival Rate**: 1,000틱 이후 생존 인구수.
2.  **IGE Verdict**: 계산된 IGE 값 ($\beta$). 
    - `IGE ≈ 0.0`: Meritocracy
    - `IGE ≈ 0.5`: Status Quo
    - `IGE > 0.8`: Caste System
3.  **ASCII Scatter Plot**: 로그 파일에 부모 자산 vs 자녀 자산의 대략적인 분포를 시각화하라 (선택 사항이나 권장).

## 4. Acceptance Criteria
- 1,000틱 완주 성공.
- IGE 수치가 0.0 ~ 1.2 사이의 값으로 출력됨.
- `simulation.mobility_tracker`가 메모리 누수 없이 데이터를 수집함.
