# W-1 Specification: [W-2] Economic Control Tower (Revised for Phase 5)

**작성자**: Architect Prime / Antigravity
**목표**: Phase 5 실험 결과(시간 배분, 래퍼 곡선 효과)를 실시간으로 모니터링하기 위한 대시보드 고도화.

---

## 1. HUD (Head-Up Display) Updates
최상단 고정 패널에 '실험 변수'와 '핵심 반응 변수'를 추가하여 즉각적인 상태 파악 지원.

- **기존 지표**: GDP, 인구수, 평균 자산, 고용률, 지니계수.
- **추가 지표 (Phase 5 반영)**:
    - **Avg Tax Rate (평균 실효세율)**: 현재 정부가 가계로부터 걷고 있는 실제 소득세율 평균. (실험의 X값)
    - **Avg Leisure Hours (평균 여가 시간)**: 24시간 중 노동하지 않는 시간. (실험의 Y값 1)
    - **Parenting Rate (육아 참여율)**: 전체 여가 시간 중 Parenting이 차지하는 비중(%). (실험의 Y값 2)

---

## 2. Tab 1: Society (사회 탭) - The Life of Agents
에이전트들이 시간을 어떻게 쓰고 있는지 시각화.

### 2.1 Time Allocation Chart (New)
- **Type**: Pie Chart
- **Data Source**: AgentState의 `leisure_type` 집계.
- **Segments**:
    - 🟥 **Work**: `time_worked`의 총합.
    - 🟩 **Parenting**: `leisure_type=PARENTING`인 에이전트의 여가 시간 합.
    - 🟦 **Self-Dev**: `leisure_type=SELF_DEV`인 에이전트의 여가 시간 합.
    - 🟨 **Entertainment**: `leisure_type=ENTERTAINMENT`인 에이전트의 여가 시간 합.
    - ⬜ **Idle**: 아무것도 안 한 시간 (나머지).

---

## 3. Tab 2: Government (정부 탭) - Fiscal Reality
정부가 걷은 돈의 출처와 쓴 곳을 명확히 표시.

### 3.1 Tax Revenue Breakdown (New)
- **Type**: Stacked Bar Chart (최근 50 Tick 이력)
- **Series**:
    - **Income Tax** (소득세)
    - **Corporate Tax** (법인세)
    - **Wealth Tax** (부유세)
    - **Consumption Tax** (소비세)

### 3.2 Welfare Expenditure (New)
- **Type**: Line Chart / Area Chart
- **Metrics**: **Unemployment Benefit** (실업 급여 지출액) vs **Stimulus Check** (재난 지원금).

---

## 4. Backend & DTO Updates (Work Order for Jules)

### 4.1 Data Schema (simulation/dtos.py)
```python
@dataclass
class DashboardGlobalIndicatorsDTO:
    # ... existing ...
    avg_tax_rate: float
    avg_leisure_hours: float
    parenting_rate: float

@dataclass
class SocietyTabDataDTO:
    # ... existing ...
    time_allocation: Dict[str, float]  # {"work": 1200.5, "parenting": 300.0, ...}
    avg_leisure_hours: float

@dataclass
class GovernmentTabDataDTO:
    # ... existing ...
    tax_revenue_breakdown: Dict[str, float]
    welfare_spending: float
    current_avg_tax_rate: float
```

### 4.2 Aggregation Logic (snapshot_viewmodel.py)
- **Optimization**: `AgentState` 조회 시 `group by leisure_type` 쿼리 또는 인메모리 집계 사용.
- **Caching Strategy**: 
    - HUD 데이터: **매 틱(Every Tick)** 갱신.
    - 탭 상세 데이터 (Society/Gov): **5~10틱 주기**로 갱신하여 성능 확보.

---

## 5. Work Order
1. **Jules**: `dtos.py` 확장 및 `SnapshotViewModel`에서 집계 로직 고도화.
2. **Assistant**: `HUD.tsx`, `SocietyTab.tsx`, `GovernmentTab.tsx` 컴포넌트 수정 및 Recharts 연동.
