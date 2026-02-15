# 🖋️ Specification Draft: God-Mode Watchtower (Simulation Cockpit)

**Status**: Draft (Scribe)  
**Ref Version**: v1.0.0 (2026-02-13)  
**Authority**: Antigravity (Architect Prime)  
**Mission Key**: WATCHTOWER-GOD-MODE-UPGRADE

---

## 1. 개요 (Executive Summary)

본 문서는 `Watchtower`를 단순한 상태 모니터링 도구에서 `SCENARIO_CARDS.md`에 정의된 사회 현상을 실시간으로 조작, 관찰, 검증할 수 있는 **'God-Mode Control Tower'**로 격상시키기 위한 아키텍처 및 데이터 연동 설계를 다룹니다.

### 1.1 핵심 목표
- **Controllability**: 시뮬레이션 중단 없이 `FORMULA_TECH_LEVEL` 등의 거시 변수를 실시간 조정.
- **Visibility**: 거시 지표(GDP)에서 미시 지표(에이전트별 욕구 만족도 히트맵)로의 드릴다운.
- **Verification**: 시나리오별 '성공 기준(Success Criteria)' 달성 여부를 엔진이 실시간 판정하여 보고.

---

## 2. API & Data Contract (simulation/dtos/watchtower_v2.py)

### 2.1 God-Mode Command Envelope (Write-side)
모든 God-Mode 개입은 `SettlementSystem`에 의해 추적 가능한 트랜잭션 형태로 인입되어야 합니다.

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class GodCommandDTO:
    """
    God-Mode 조작 명령을 위한 최상위 봉투.
    'Sacred Sequence'의 Phase 0(Intercept)에서 처리됨.
    """
    command_type: str  # SET_PARAM, TRIGGER_EVENT, PAUSE, RESUME, INJECT_MONEY
    target_domain: str # Economy, Population, Tech, Finance
    parameter_name: str
    new_value: Any
    metadata: Dict[str, Any] # "reason": "SC-001 Verification" 등
```

### 2.2 Expanded Telemetry (Read-side)
기존 `WatchtowerSnapshotDTO`를 확장하여 시나리오 검증 및 미시 통계 데이터를 포함합니다.

```python
@dataclass
class ScenarioVerificationDTO:
    sc_id: str               # "SC-001", "SC-002"
    is_active: bool
    progress_pct: float      # 성공 기준 도달률 (0.0 ~ 1.0)
    current_kpis: Dict[str, float]
    status_msg: str          # "Success Criteria Met" 등

@dataclass
class MicroInsightDTO:
    """미시적 에이전트 상태의 통계적 요약. 에이전트 객체 직접 참조 금지."""
    need_satisfaction_heatmap: Dict[str, List[float]] # 욕구 단계별 5분위 점수
    gender_labor_gap: float
    social_mobility_index: float
    wealth_distribution_bins: List[float]
```

---

## 3. God-Mode UX 전략 및 인터페이스 기획

### 3.1 시나리오 카드 제어반 (Scenario Control Panel)
- **동적 슬라이더**: `SCENARIO_CARDS.md`에 정의된 조작 변수(`CHILD_MONTHLY_COST`, `FORMULA_TECH_LEVEL` 등)를 엔진의 `GlobalRegistry`와 동기화하여 실시간 조정.
- **Threshold Visualizer**: 조작 변수가 특정 임계점을 넘을 때 발생하는 '위상 전이(Phase Transition)'를 시각화.

### 3.2 인위적 블랙스완 개입 (Event Trigger)
- **Bank Run Mode**: 특정 은행에 `MassWithdrawalEvent`를 강제 주입하여 SC-004 시나리오 즉시 실행.
- **Harvest Failure**: `ProductionEngine`의 토지 생산성 계수를 일시적으로 0.1로 강제 고정하여 멜서스 함정(SC-003) 유도.

### 3.3 미시-거시 드릴다운 (Drill-down Insight)
- **Heatmap Interaction**: 대시보드의 'Gini 계수' 클릭 시, 소득 5분위별 에이전트들의 매슬로 욕구 만족도 분포(Heatmap)를 즉시 표시.
- **Agent Sampling**: 특정 조건을 만족하는 '샘플 에이전트' 5인의 `System 2` 내부 모델(NPV Projection)을 시각화하여 결정 과정 추적.

---

## 4. 엔진 레이어 요구사항 및 로직 (Pseudo-code)

### 4.1 God-Mode Interceptor (Sacred Sequence Integration)
God-Mode 명령은 시뮬레이션 인과율을 해치지 않도록 `TickScheduler`의 특정 지점에서만 집행됩니다.

```python
# modules/system/scheduler.py 내 가상 로직
def run_tick(self):
    # Phase 0: God-Mode Interception
    commands = self.command_buffer.consume_all()
    for cmd in commands:
        if cmd.command_type == "SET_PARAM":
            GlobalRegistry.update(cmd.target_domain, cmd.parameter_name, cmd.new_value)
        elif cmd.command_type == "PAUSE":
            self.state = SimulationState.PAUSED
    
    # Phase 1 ~ 7: Standard Sacred Sequence
    self.execute_normal_phases()
    
    # Phase 8: Telemetry Harvesting & Scenario Verification
    snapshot = TelemetryCollector.capture_all()
    ScenarioVerifier.audit(snapshot) # SC-XXX 달성 여부 판정
    self.telemetry_socket.broadcast(snapshot)
```

### 4.2 필수 데이터 포인트 (Data Points to Export)
1. **Gender-Specific Stats**: 노동 시간, 임금, 교육 수준의 성별 평균 및 분산.
2. **Age-Group Dynamics**: 연령대별 자산 축적 곡선 및 출산 결정 확률분포.
3. **Institutional Health**: 은행 지준율 상태 및 기업들의 Altman Z-Score 히트맵.
4. **Environment Constraints**: `fixed_land_factor`에 따른 수확 체감 임계값 도달 정도.

---

## 5. Audit & Risk Analysis (기술적 위험 분석)

### 5.1 주요 위험 및 대응 전략
- **Government God Class 의존성 (TD-226~229)**: 
    - *위험*: `PAUSE`나 `TAX_ADJUST` 명령이 거대해진 `Government` 클래스에 직접 의존하면 유지보수가 불가능함.
    - *대응*: `CommandService`를 독립 모듈로 분리하고, 정부 로직과는 `SettlementSystem` 트랜잭션을 통해서만 통신하게 함.
- **순환 참조 (Circular Dependency)**: 
    - *위험*: `Watchtower`가 통계 산출을 위해 전 도메인을 임포트하고, 각 도메인이 로깅을 위해 `Watchtower`를 임포트하는 현상.
    - *대응*: 모든 통계 데이터는 각 도메인이 `TickEnd` 시점에 `SharedStatsBuffer`에 기록하고, `Watchtower`는 이 버퍼만 참조하도록 설계.
- **Purity Gate 위반**: 
    - *위험*: UX 편의를 위해 UI가 직접 에이전트 객체를 메모리에서 읽으려 시도함.
    - *대응*: Purity Gate를 통해 직렬화된 DTO 외의 모든 접근을 차단하고, 대량 데이터는 NumPy Vector 형태로 전달.

### 5.2 선행 작업 권고
- **TD-226~229 (Government Decomposition)**: 시나리오 조작 전, 정부 모듈의 분리(Welfare/Tax/Bond Service)가 선행되어야 함.
- **GlobalRegistry 구현**: 하드코딩된 상수들을 런타임에 수정 가능한 `Registry` 구조로 마이그레이션 필수.

---

## 6. 검증 계획 (Verification Strategy)

### 6.1 신규 테스트 케이스
- **Test God-Mode Latency**: 명령 주입 후 실제 엔진 변수 반영까지의 틱 지연 검증 (목표: 1틱 이내).
- **Test Scenario Trigger Integrity**: `Harvest Failure` 트리거 시 `Money Leak`이 발생하지 않는지 `SettlementSystem Audit` 수행.

### 6.2 UI/UX 정합성 체크
- WebSocket 단절 시 명령 큐 보존 여부 및 재접속 시 상태 동기화 검증.

---

## 7. Mandatory Reporting Verification

본 설계 초안 작성 과정에서 발견된 다음의 인사이트와 기술 부채를 별도 보고서로 기록하도록 지시함.
- **파일 위치**: `communications/insights/WATCHTOWER_GOD_MODE.md`
- **기록 필수 항목**:
    - `GlobalRegistry` 부재에 따른 하드코딩 상수 관리 부채.
    - `WatchtowerSnapshotDTO`의 거대화(Monolithic DTO) 위험 및 분리 방안.
    - 시나리오 검증 로직의 엔진 내장 vs 독립 모듈화 결정 사유.

> **"신은 주사위를 던지지 않지만, 시뮬레이터의 설계자는 주사위의 눈을 고정할 수 있어야 한다."** - Scribe's Architectural Note