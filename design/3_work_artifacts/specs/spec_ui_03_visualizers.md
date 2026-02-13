# 🖋️ Specification: Watchtower Visualizers (UI-03)

**Status**: Draft (Scribe)  
**Mission Key**: UI-03 (GODMODE-WATCHTOWER-EXECUTION)  
**Domain**: `dashboard/components`  
**Parent**: Phase 3 (Dashboard & UX)

---

## 1. 개요 (Executive Summary)

`UI-03`은 `ScenarioVerifier`(DATA-03)가 생성한 검증 리포트와 시뮬레이션의 실시간 경제 지표를 시각화하는 고성능 대시보드 컴포넌트 집합입니다. 본 명세는 시나리오의 진행 상황을 직관적으로 파악할 수 있는 'Scenario Cockpit'과 거시 지표에서 미시 지표로 파고드는 'Drill-down Heatmap'의 연동 구조를 정의합니다. 특히, `On-Demand Telemetry`와 연계하여 불필요한 데이터 전송을 억제하는 효율적인 통신 구조를 지향합니다.

---

## 2. 아키텍처 및 설계 원칙

### 2.1 Component-Driven Masking (Pull Model)
- 각 시각화 컴포넌트(Visualizer)는 자신이 렌더링에 필요한 데이터 필드(`TelemetryMask`)를 스스로 정의합니다.
- 대시보드 엔진은 현재 활성화된(화면에 보이는) 컴포넌트들의 마스크를 병합(Merge)하여 `TelemetryCollector`에 데이터를 요청합니다.

### 2.2 Data Flow
1. **Trigger**: Streamlit UI 업데이트 (Tick 완료 시그널 수신).
2. **Subscription**: 활성 탭/컴포넌트 식별 및 `TelemetryMask` 취합.
3. **Request**: `GodCommandDTO`를 통해 특정 마스크가 적용된 데이터 요청.
4. **Render**: 수신된 `WatchtowerV2-DTO`를 기반으로 차트 업데이트.

---

## 3. 상세 설계 초안 (API & Components)

### 3.1 Scenario Cockpit (Gauge & Status)
- **목표**: SC-001~006 시나리오의 실시간 합격/불합격 여부 및 진행률 시각화.
- **UI 요소**:
    - **Radial Gauge**: `ScenarioReportDTO.progress_pct` 표시.
    - **Status Badge**: `SUCCESS`(Green), `RUNNING`(Blue), `FAILED`(Red), `PENDING`(Gray).
    - **Trend Line**: 최근 50틱간의 KPI 변동 추이 (Mini-sparkline).

### 3.2 MicroInsight Drill-down (Heatmaps)
- **목표**: 거시 지표(예: Gini) 이상 발생 시, 에이전트 단위의 세부 분포 시각화.
- **인터렉션**: 
    - 지니 계수 차트 클릭 → `DrillDownEvent` 발생.
    - 요청 마스크 확장: `mask += ["agent_wealth_distribution", "need_satisfaction_matrix"]`.
- **시각화**: 에이전트 속성(소득, 나이, 성별) 기반 2D 히트맵 또는 산점도.

### 3.3 `dashboard/components/visuals.py` (Draft Interface)

```python
from typing import List, Dict, Any
import streamlit as st
import pandas as pd

class BaseVisualizer:
    """모든 차트 컴포넌트의 기본 클래스"""
    @property
    def required_mask(self) -> List[str]:
        """이 차트가 필요로 하는 데이터 필드 목록"""
        raise NotImplementedError

    def render(self, data: Dict[str, Any]):
        """데이터를 받아 Streamlit에 렌더링"""
        raise NotImplementedError

class ScenarioCardVisualizer(BaseVisualizer):
    def render(self, report: ScenarioReportDTO):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("Progress", f"{report.progress_pct}%", delta=f"{report.current_kpi_value - report.target_kpi_value:.2f}")
        with col2:
            st.subheader(f"Scenario: {report.scenario_id}")
            st.write(f"Status: {report.status.value}")
```

---

## 4. 로직 상세 (Pseudo-code)

### 4.1 On-Demand Mask Aggregation
```python
def get_active_telemetry_mask(active_tabs: List[BaseVisualizer]) -> List[str]:
    full_mask = set()
    for component in active_tabs:
        full_mask.update(component.required_mask)
    
    # 필수 메타데이터 추가
    full_mask.add("tick_count")
    full_mask.add("simulation_status")
    
    return list(full_mask)
```

### 4.2 Drill-down Trigger Logic
```python
def handle_gini_click():
    if st.session_state.get("drill_down_active"):
        # 미시 데이터 요청을 위해 마스크 동적 추가
        current_mask = st.session_state.telemetry_mask
        st.session_state.telemetry_mask = list(set(current_mask + ["household_detailed_stats"]))
        render_agent_heatmap()
```

---

## 5. 검증 계획 (Testing & Verification Strategy)

### 5.1 New Test Cases
- **Mask Integrity**: 특정 컴포넌트 활성화 시, 요청되는 `GodCommandDTO`의 `mask` 필드가 해당 컴포넌트의 `required_mask`와 일치하는지 검증.
- **DTO Safety**: `ScenarioReportDTO`에 `NaN`이나 `None` 값이 포함되어 들어올 때 차트 컴포넌트가 크래시되지 않고 'No Data'를 출력하는지 테스트.
- **Latency Check**: 데이터 크기가 큰 히트맵(에이전트 1,000명 이상) 요청 시 UI 렌더링 지연 시간 측정 및 60fps(또는 적절한 갱신율) 유지 확인.

### 5.2 Integration Check
- `DATA-02`(Telemetry Engine)와 연동하여 실제 마스크된 데이터가 정상적으로 필터링되어 넘어오는지 확인.
- `ScenarioVerifier`의 판정 결과가 대시보드의 Gauge 차트에 실시간 반영되는지 End-to-End 테스트.

---

## 6. 🚨 Risk & Impact Audit (기술적 위험 분석)

1. **렌더링 병목 (UI Blocking)**:
   - 위험: 대규모 에이전트 데이터를 한 번에 시각화할 경우 Streamlit의 리런(Rerun) 메커니즘으로 인해 조종석 반응 속도 저하.
   - 방지: 데이터 집계(Aggregation) 로직을 프론트엔드가 아닌 백엔드(`TelemetryCollector`)에서 수행하여, UI는 정제된 요약 데이터만 수신하도록 설계.
2. **상태 동기화 오류 (State Desync)**:
   - 위험: 시뮬레이션의 틱 속도가 UI 렌더링 속도보다 빠를 경우, 차트가 특정 틱을 건너뛰거나 데이터가 밀리는 현상.
   - 대응: UI 업데이트 시 최신 틱 데이터만 가져오는 'LIFO(Last-In-First-Out)' 방식의 데이터 버퍼링 적용.
3. **의존성 순환 (Dependency Loop)**:
   - 위험: UI 컴포넌트가 `modules/` 내부 클래스에 직접 의존할 경우 임포트 에러 발생 가능.
   - 방지: 모든 시각화 데이터는 오직 `simulation/dtos/`에 정의된 DTO를 통해서만 전달받도록 엄격히 분리.

---

## 7. 🚨 Mandatory Reporting Verification

본 설계 초안 작성 과정에서 식별된 인사이트와 잠재적 부채를 다음 경로에 기록하였습니다.
- **인사이트 보고서**: `communications/insights/UI_03_VISUALIZERS_INSIGHTS.md`
- **주요 기록 내용**:
    - `Plotly` 또는 `Altair` 라이브러리 사용 시 데이터 직렬화 오버헤드 최적화 방안 (JSON 최소화).
    - 사용자가 직접 대시보드에서 새로운 마스크를 조합할 수 있는 'Advanced Query' 인터페이스 기획.
    - 시나리오 실패 시의 상태를 스냅샷으로 저장하여 나중에 '리플레이'할 수 있는 타임머신 기능의 기초 설계 반영.

> **"지표는 단순한 숫자가 아니라 경제의 맥박이다. Visualizer는 그 맥박을 가장 선명하게 보여주는 청진기가 되어야 한다."** - Administrative Scribe