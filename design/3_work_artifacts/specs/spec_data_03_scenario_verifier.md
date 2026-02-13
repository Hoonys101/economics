# 🖋️ Specification: ScenarioVerifier Engine (DATA-03)

**Status**: Draft (Scribe)  
**Mission Key**: DATA-03 (GODMODE-WATCHTOWER-EXECUTION)  
**Domain**: `modules/analysis`  
**Parent**: Phase 2 (Data & Protocol)

---

## 1. 개요 (Executive Summary)

`ScenarioVerifier`는 `SCENARIO_CARDS.md`에 정의된 경제적 가설과 사회 현상을 시뮬레이션 데이터로부터 실시간으로 검증하는 판정 엔진입니다. 이 엔진은 단순한 데이터 수집을 넘어, 설정된 **성공 기준(Success Criteria)**에 도달했는지 여부를 판단하고 시나리오의 진행 상태(`progress_pct`)와 실패 원인(`failure_reason`)을 조종석(Watchtower)에 보고합니다.

---

## 2. 아키텍처 및 설계 원칙

### 2.1 위치 및 트리거 (Sacred Sequence)
- **Phase 8 (Telemetry)**: 모든 정산과 시스템 정리가 완료된 후, 최종 확정된 데이터를 바탕으로 분석을 수행합니다.
- **Terminal Node**: 타 모듈을 호출하지 않으며, 오직 `TelemetryCollector`로부터 전달받은 데이터만을 처리하여 순수한 분석 결과를 생성합니다.

### 2.2 전략 패턴 (Scenario Judge Strategy)
- 각 시나리오 카드(SC-xxx)는 독립적인 `ScenarioJudge` 구현체로 설계됩니다.
- 새로운 사회 현상 검증이 필요할 때 엔진 수정 없이 클래스 추가만으로 확장이 가능합니다.

---

## 3. 상세 설계 초안 (API & DTO)

### 3.1 `modules/analysis/scenario_verifier/api.py`

```python
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

class ScenarioStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

@dataclass(frozen=True)
class ScenarioReportDTO:
    """시나리오 판정 결과 및 상태를 담는 DTO"""
    scenario_id: str
    status: ScenarioStatus
    progress_pct: float
    current_kpi_value: float
    target_kpi_value: float
    message: str
    failure_reason: Optional[str] = None

class IScenarioJudge:
    """개별 시나리오 카드 판정 인터페이스"""
    def evaluate(self, telemetry_data: Dict[str, Any]) -> ScenarioReportDTO:
        ...

class ScenarioVerifier:
    """시나리오 검증 총괄 엔진"""
    def __init__(self, judges: List[IScenarioJudge]):
        self._judges = judges
        self._active_scenarios: List[str] = []

    def verify_tick(self, telemetry_data: Dict[str, Any]) -> List[ScenarioReportDTO]:
        """매 틱 호출되어 활성화된 시나리오를 평가함"""
        ...
```

---

## 4. 로직 상세 (Pseudo-code)

### 4.1 SC-001 (Female Labor Participation) 판정 로직 예시
```python
def evaluate_sc001(telemetry_data):
    # 1. 데이터 추출 (Telemetry Mask를 통해 수집된 데이터)
    female_stats = telemetry_data.get("household_stats_by_gender").get("F")
    male_stats = telemetry_data.get("household_stats_by_gender").get("M")
    
    # 2. KPI 계산 (여성 노동 시간 비율)
    ratio = female_stats.avg_labor_hours / male_stats.avg_labor_hours
    
    # 3. 진행도 계산
    target = 0.90
    progress = min(100.0, (ratio / target) * 100)
    
    # 4. 판정
    status = ScenarioStatus.RUNNING
    if ratio >= target:
        status = ScenarioStatus.SUCCESS
    elif ratio < 0.1: # 극단적 실패 조건 예시
        status = ScenarioStatus.FAILED
        
    return ScenarioReportDTO(
        scenario_id="SC-001",
        status=status,
        progress_pct=progress,
        current_kpi_value=ratio,
        target_kpi_value=target,
        message=f"Current Ratio: {ratio:.2f}"
    )
```

---

## 5. 검증 계획 (Testing & Verification Strategy)

### 5.1 New Test Cases
- **Happy Path**: `GlobalRegistry`를 통해 조작 변수(예: `FORMULA_TECH_LEVEL = 1.0`)를 주입했을 때, 엔진이 `SUCCESS`를 올바르게 반환하는지 검증.
- **Edge Case**: 데이터 누락 또는 `NaN` 값이 `TelemetryCollector`로부터 전달될 때 엔진이 크래시되지 않고 `FAILED`와 이유를 반환하는지 확인.
- **Persistence Check**: 여러 틱에 걸쳐 관측해야 하는 지표(예: 출산율 3세대 관측)가 내부 상태를 유실하지 않고 누적 계산되는지 테스트.

### 5.2 Integration Check
- `TickScheduler`의 Phase 8에서 `ScenarioVerifier`가 호출되는지 확인.
- 결과 DTO가 `GodCommandDTO` 형식으로 래핑되어 Watchtower UI에 실시간 반영되는지 통신 테스트.

---

## 6. 🚨 Risk & Impact Audit (기술적 위험 분석)

1. **데이터 오염 (Dirty Reads)**: 
   - 위험: Phase 7(Settlement) 이전 호출 시 미정산된 자산 정보를 기반으로 잘못된 KPI를 계산할 가능성.
   - 방지: `TickScheduler`에서 Phase 8 이후에만 실행되도록 하드코딩된 호출 순서 보장.
2. **성능 오버헤드 (Performance)**:
   - 위험: 수천 명의 에이전트 데이터를 매 틱 집계하여 분석할 경우 시뮬레이션 속도 저하.
   - 방지: `Passive Mode`를 구현하여 Watchtower UI가 닫혀 있거나 분석 요청이 없을 때는 연산을 건너뜀.
3. **스키마 불일치**:
   - 위험: `TelemetryCollector`의 데이터 구조 변경 시 Verifier의 계산식이 깨짐.
   - 대응: 분석용 Raw 데이터 접근을 위한 전용 Facade 메서드를 `TelemetryCollector`에 마련하여 변경 파급력을 최소화함.

---

## 7. 🚨 Mandatory Reporting Verification

본 설계 초안 작성 과정에서 식별된 인사이트와 잠재적 부채를 다음 경로에 기록하였습니다.
- **인사이트 보고서**: `communications/insights/DATA_03_SCENARIO_VERIFIER_INSIGHTS.md`
- **주요 기록 내용**:
    - KPI 계산 로직을 NumPy 벡터 연산으로 구현하여 대규모 에이전트 수 대비 성능을 확보하는 방안.
    - 시나리오 판정 기준에 '시간 가중치'를 도입하여 일시적인 수치 도달이 아닌 지속 가능성을 검증하는 메커니즘 제안.
    - `ScenarioVerifier`가 `GodCommandDTO`를 상속받거나 포함하여 명령-응답 구조의 일관성을 유지하는 설계 확정.

> **"관측되지 않는 실험은 데이터 낭비일 뿐이다. Verifier는 시뮬레이션의 눈(Eye)이자 뇌(Brain)가 되어야 한다."** - Administrative Scribe