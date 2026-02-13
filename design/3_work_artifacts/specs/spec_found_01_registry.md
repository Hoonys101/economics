# Technical Specification: FOUND-01 GlobalRegistry

**Status**: Specification Draft  
**Mission Key**: FOUND-01  
**Target Module**: `modules/system/registry.py`  
**Orchestrator**: Antigravity (Architect Prime)  
**Scribe**: Gemini-CLI Administrative Assistant

---

## 1. Executive Summary
시뮬레이션의 하드코딩된 상수(`economy_params.yaml`, `config.py`)를 런타임에 제어 가능한 동적 파라미터로 전환하기 위한 `GlobalRegistry`를 설계합니다. 본 모듈은 God-Mode Watchtower의 핵심 인프라로서, 'Foundation First' 원칙에 따라 데이터의 무결성을 보장하며 엔진 내부 로직과 관찰자 개입 간의 충돌을 방지하는 권한 기반 Lock 메커니즘을 제공합니다.

---

## 2. Interface Specification (`api.py` 초안)

```python
"""
API Interface for GlobalRegistry (FOUND-01).
Defines the contract for dynamic parameter management and hot-swapping.
"""

from typing import Any, Protocol, List, Optional, Dict
from enum import IntEnum
from dataclasses import dataclass

class OriginType(IntEnum):
    """우선순위 기반의 데이터 소스 정의"""
    SYSTEM = 0   # 엔진 기본값 (Hardcoded Fallback)
    CONFIG = 1   # YAML 파일 로드 값
    GOD_MODE = 2 # 관찰자 직접 개입 (Highest Priority, Forced Lock)

@dataclass(frozen=True)
class RegistryEntry:
    """레지스트리 저장 단위"""
    value: Any
    origin: OriginType
    is_locked: bool = False
    last_updated_tick: int = 0

class RegistryObserver(Protocol):
    """값 변경 통지를 받기 위한 프로토콜"""
    def on_registry_update(self, key: str, value: Any, origin: OriginType) -> None:
        """파라미터 변경 시 호출될 콜백"""
        ...

class IGlobalRegistry(Protocol):
    """GlobalRegistry 공개 인터페이스"""
    
    def get(self, key: str, default: Any = None) -> Any:
        """파라미터의 현재 값을 반환"""
        ...

    def set(self, key: str, value: Any, origin: OriginType = OriginType.CONFIG) -> bool:
        """
        파라미터 값을 설정. 
        권한(Origin)이 현재 값보다 낮거나 Locked 상태이면 False 반환 또는 Exception 발생.
        """
        ...

    def lock(self, key: str) -> None:
        """특정 파라미터를 God-Mode 권한으로 잠금"""
        ...

    def unlock(self, key: str) -> None:
        """잠금 해제"""
        ...

    def subscribe(self, observer: RegistryObserver, keys: Optional[List[str]] = None) -> None:
        """특정 키 또는 전체 변경 사항 관찰 등록"""
        ...

    def snapshot(self) -> Dict[str, RegistryEntry]:
        """현재 모든 파라미터 상태를 스냅샷으로 반환 (UndoStack 연동용)"""
        ...
```

---

## 3. Detailed Design (Logic & Pseudo-code)

### 3.1 로직 단계 (Pseudo-code)

**[Initialization]**
1. `config/` 내의 모든 YAML 파일을 스캔.
2. `OriginType.CONFIG` 권한으로 초기 `RegistryEntry` 딕셔너리 구축.
3. 시뮬레이션 엔진에 의존성 주입(DI).

**[Set Operation Logic]**
```python
def set(key, value, origin):
    current_entry = self._storage.get(key)
    
    # 1. 권한 체크
    if current_entry and current_entry.is_locked:
        if origin < current_entry.origin:
            raise PermissionError(f"Target '{key}' is locked by {current_entry.origin.name}")
    
    # 2. 신성한 시퀀스 (Phase 0) 정합성 확인
    if not self.scheduler.is_in_phase_0():
        # 즉시 반영 시 데이터 오염 위험이 있는 핵심 변수는 큐에 저장
        self._pending_updates.append((key, value, origin))
        return False

    # 3. 값 업데이트 및 메타데이터 기록
    new_entry = RegistryEntry(
        value=value,
        origin=origin,
        is_locked=(origin == OriginType.GOD_MODE),
        last_updated_tick=self.scheduler.current_tick
    )
    self._storage[key] = new_entry
    
    # 4. 옵저버 통지 (Synchronous)
    self._notify(key, value, origin)
    return True
```

### 3.2 예외 처리 전략
- **KeyNotFoundError**: 존재하지 않는 키 참조 시 로깅 후 `SYSTEM` 기본값 반환 시도, 없으면 `KeyError`.
- **TypeError**: Registry 수준에서 타입 검증은 하지 않으나, `set` 호출 시 기존 값과 타입이 다를 경우 경고 로그 출력.
- **PermissionError**: 하위 권한(예: 엔진 자동 업데이트)이 상위 권한(God-Mode)에 의해 잠긴 변수를 수정하려 할 때 발생.

---

## 4. 🕵️ Pre-flight Risk Analysis (Audit)

아키텍처 감사(Audit)를 통해 식별된 지뢰와 대응 방안입니다.

1.  **Ghost Constants (유령 상수)**: 기존 `config.py`의 `getattr` 방식과 Registry가 혼용될 경우 시뮬레이션 상태가 분산될 위험이 있음.
    - **대응**: `config.py` 내부를 `Registry.get()`을 호출하는 프록시로 전면 대체하여 단일 진실 공급원(SSoT) 확보.
2.  **Circular Import (순환 참조)**: `Government`가 Registry를 참조하고, Registry가 `Government` 설정을 로드할 때 발생 가능.
    - **대응**: Registry는 도메인 지식(Domain Knowledge)을 갖지 않는 순수 데이터 저장소로 설계. 초기화 시점은 `main.py`의 최우선 순위로 배치.
3.  **Dirty Reads (mid-tick update)**: 연산 중간에 파라미터가 바뀌면 `SettlementSystem`의 제로섬 검증이 깨질 수 있음.
    - **대응**: `Sacred Sequence Phase 0 (Intercept)` 슬롯에서만 실제 `set`이 집행되도록 강제.
4.  **Test Flakiness**: 테스트 종료 후 Lock 상태가 남으면 다음 테스트에 영향을 줌.
    - **대응**: `tests/conftest.py`에 `registry_reset` 픽스처 추가 필수.

---

## 5. Verification Plan (Testing)

### 5.1 New Test Cases
- **Happy Path**: `set(GOD_MODE)` -> `get()` 결과가 일치하는지 확인.
- **Lock Enforcement**: `OriginType.GOD_MODE`로 잠근 후 `OriginType.CONFIG`로 수정을 시도할 때 `PermissionError`가 발생하는지 검증.
- **Observer Notification**: 값 변경 시 `RegistryObserver`의 콜백이 지연 없이 호출되는지 확인.
- **Hot-swapping**: 시뮬레이션 러닝 중 `Sacred Sequence`의 특정 시점에 값이 안전하게 교체되는지 통합 테스트.

### 5.2 Integration Check
- `SimulationConfig` 객체가 Registry를 통해 필드 값을 로드하는지 확인.
- `Government.tax_rate` 변경 시 관련 캐시가 무효화(Invalidate)되는지 확인.

---

## 6. Implementation Roadmap

1.  **Step 1**: `modules/system/registry.py` 인터페이스 및 기본 저장소 구현.
2.  **Step 2**: `config.py`를 Registry 프록시로 마이그레이션.
3.  **Step 3**: `TickScheduler`에 `Phase 0 Intercept` 로직 추가하여 업데이트 큐 연동.
4.  **Step 4**: God-Mode Watchtower용 명령 인터페이스 테스트.

---

## 7. Mandatory Reporting & Insights

**[Routine] Mandatory Reporting Instruction**: 
본 설계 및 구현 과정에서 발견된 모든 아키텍처적 통찰(Insight)과 기술 부채는 반드시 `communications/insights/FOUND_01_REGISTRY_INSIGHTS.md` 파일에 독립적으로 기록하십시오. 특히 `config.py`와의 정합성 정체 구간 및 `Sacred Sequence` 연동 시의 오버헤드 측정 결과를 포함해야 합니다.

---
> **"기초가 흔들리면 조종석은 흉기가 된다. 레지스트리는 시뮬레이션의 물리 법칙을 정의하는 법전이다."** - Administrative Scribe's Final Note