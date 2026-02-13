# 🖋️ Specification: On-Demand Telemetry Engine (DATA-02)

**Status**: Draft (Scribe)  
**Version**: 1.0.0  
**Mission Key**: DATA-02  
**Related Missions**: FOUND-01 (GlobalRegistry), FOUND-03 (Intercept Slot)

---

## 1. 개요 (Overview)

`On-Demand Telemetry` 엔진은 시뮬레이션의 방대한 데이터 중 Watchtower UI가 활성화된 화면에 필요한 데이터만을 선별적으로 수집하고 전송 대역폭을 최적화하기 위한 핵심 모듈입니다. 모든 데이터 접근은 `GlobalRegistry`를 통해 추상화되며, "Push-Only" 아키텍처를 준수하여 엔진 내부의 직접적인 상태 노출을 차단합니다.

### 1.1 주요 목적
- **Bandwidth Optimization**: 수천 개의 변수 중 UI가 요청한 `mask` 필드만 추출.
- **Multi-Frequency Sampling**: 거시 지표(Macro, 1Hz)와 미시 지표(Micro, 0.1Hz)의 샘플링 주기 차별화.
- **Side-Effect Free**: 수집 과정이 시뮬레이션 로직이나 상태에 어떠한 영향도 주지 않음 (Read-Only Purity).

---

## 2. 아키텍처 및 데이터 흐름 (System Architecture)

### 2.1 Registry-Mediated Harvesting
`TelemetryCollector`는 각 모듈에 직접 접근하지 않습니다. 대신 `GlobalRegistry`를 인터페이스로 사용하여 정적/동적 변수를 조회합니다.

1.  **Request (Watchtower -> Backend)**: WebSocket을 통해 `mask: List[str]` 수신.
2.  **Registration**: `TelemetryCollector`의 구독 레지스트리에 필드 및 빈도(Frequency) 등록.
3.  **Tick Execution (Phase 0)**: `TickScheduler`가 `TelemetryCollector.execute_harvest()` 호출.
4.  **Data Extraction**: `GlobalRegistry`에서 Dot-notation 기반으로 데이터 조회.
5.  **Dispatch**: 수집된 `TelemetrySnapshotDTO`를 전송 계층으로 전달.

---

## 3. 인터페이스 명세 (API & DTO)

### 3.1 `modules/system/telemetry.py` (API Outline)

```python
from typing import List, Dict, Any, Optional
from core.dtos import TelemetrySnapshotDTO

class TelemetryCollector:
    """시뮬레이션 상태 데이터를 선별적으로 수집하는 엔진."""

    def __init__(self, registry: 'GlobalRegistry'):
        self._registry = registry
        self._subscriptions: Dict[str, int] = {}  # field_path: frequency_interval
        self._cache: Dict[str, Any] = {}

    def subscribe(self, mask: List[str], frequency_interval: int = 1):
        """수집할 필드와 틱 단위 주기를 등록."""
        for path in mask:
            self._subscriptions[path] = frequency_interval

    def unsubscribe(self, mask: List[str]):
        """구독 해제."""
        for path in mask:
            self._subscriptions.pop(path, None)

    def harvest(self, current_tick: int) -> TelemetrySnapshotDTO:
        """현재 틱에서 수집 주기가 도래한 데이터들만 추출."""
        ...

    def _resolve_path(self, path: str) -> Any:
        """GlobalRegistry에서 Dot-notation 경로로 값을 조회 (e.g., 'economy.m2')."""
        ...
```

### 3.2 `core/dtos/telemetry.py`

```python
from typing import TypedDict, Dict, List, Any

class TelemetrySnapshotDTO(TypedDict):
    """실시간 데이터 스냅샷 구조."""
    timestamp: float      # 실제 시간 (Unix)
    tick: int            # 시뮬레이션 틱
    data: Dict[str, Any] # 수집된 데이터 필드 (Dot-notation key)
    errors: List[str]    # 조회 실패한 필드 목록
    metadata: Dict[str, Any] # 샘플링 빈도 등 부가 정보
```

---

## 4. 상세 설계 (Detailed Design)

### 4.1 Mask Resolution (Dot-notation)
- 수집 경로는 `domain.subdomain.variable` 형식을 따릅니다.
- `GlobalRegistry`는 이 경로를 파싱하여 해당 모듈의 `api.py`에서 정의된 Public 필드를 반환합니다.
- 만약 경로가 유효하지 않거나 접근 권한이 없는 경우, 예외를 발생시키지 않고 `errors` 필드에 기록합니다.

### 4.2 Multi-Frequency Sampling Logic
- **Macro Data**: 매 틱(`interval=1`) 수집.
- **Micro Data**: 10틱마다(`interval=10`) 수집.
- `harvest()` 메서드는 `current_tick % frequency_interval == 0` 조건을 만족하는 필드만 딕셔너리에 포함합니다.

### 4.3 Non-blocking & Efficiency
- **Zero-Copy**: 대규모 배열(예: 모든 가계의 부의 분포)은 가공하지 않고 원본 레퍼런스나 요약본(Summary)만 Registry에서 가져옵니다.
- **Pre-Validation**: 구독 시점에 `GlobalRegistry`를 통해 경로 유효성을 1회 검증하여 런타임 오버헤드를 줄입니다.

---

## 5. 검증 계획 (Testing & Verification)

### 5.1 핵심 테스트 케이스
- **TC-01 (Happy Path)**: 유효한 `mask`를 등록하고 매 틱마다 정확한 데이터가 DTO에 포함되는지 확인.
- **TC-02 (Frequency Check)**: 10틱 주기 필드가 정확히 10틱마다만 데이터에 포함되는지 검증.
- **TC-03 (Invalid Path)**: 존재하지 않는 경로 요청 시 크래시 없이 `errors` 필드에 기록되는지 확인.
- **TC-04 (Isolation Test)**: 데이터 수집 행위가 `GlobalRegistry` 내의 상태값을 변경하지 않음을 보장 (Deepcopy 또는 Read-only Proxy 검사).

### 5.2 통합 검증
- `scripts/fixture_harvester.py`를 사용하여 과거 시나리오 스냅샷을 로드한 뒤, `TelemetryCollector`가 해당 시점의 데이터를 정확히 재현해내는지 비교 분석.

---

## 6. Risk & Impact Audit (기술적 위험 분석)

- **순환 참조 위험**: `TelemetryCollector`가 각 도메인 모듈을 직접 참조할 경우 순환 참조가 발생함. 반드시 `GlobalRegistry`를 통해서만 데이터에 접근하도록 인터페이스를 강제해야 함.
- **성능 병목**: 수집 필드가 수만 개로 늘어날 경우 `harvest` 과정이 `TickScheduler`를 지연시킬 수 있음. 수집 대상 필드 수에 대한 임계값(Hard Limit) 설정 필요.
- **데이터 일관성**: `Phase 0`에서 수집되는 데이터는 이전 틱의 결과임. 수집 시점이 `Phase 0`인지 `Phase 8`인지에 따라 데이터의 의미가 달라지므로 시점 정의를 엄격히 고수할 것 (`FOUND-03` 연동).

---

## 7. Mandatory Reporting Verification

- **인사이트 기록 완료**: 본 설계 과정에서 식별된 '실시간 대규모 행렬 데이터의 직렬화 오버헤드 방안'에 대한 고찰을 `communications/insights/DATA_02_TELEMETRY_ENGINE.md`에 기록하였음.
- **보고서 확인**: 상기 인사이트 리포트가 누락될 경우 본 미션은 정합성 실패로 간주됨을 인지함.

> **"지나친 관찰은 실험 대상을 변질시킨다. 시뮬레이션의 순수성을 지키면서 필요한 사실만을 낚아채라."** - Administrative Scribe Final Note