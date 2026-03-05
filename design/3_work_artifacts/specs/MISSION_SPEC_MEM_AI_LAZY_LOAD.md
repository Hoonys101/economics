# Specification Draft: AI Engine Lazy-Loading & Infra Optimization
**Mission Key**: WO-SPEC-MEM-FIX-AI-LAZY-LOAD

## 1. Overview
**Goal**: Resolve the MemoryError during `Phase 4` population initialization by reducing the initial "Weight of Infrastructure" memory footprint.
**Scope**: 
1. `simulation_builder.py`: Implement Lazy-Loading for AI Engines to prevent premature loading of heavy model weights.
2. `initializer.py`: Optimize the instantiation of `RealEstateUnit` arrays to defer memory allocation or reduce object overhead.

## 2. Logic Steps (Pseudo-code)

### 2.1 AI Engine Lazy-Loading (`modules/system/builders/simulation_builder.py`)
현재 `AIEngineRegistry`를 통해 모든 `value_orientation`의 모델 가중치를 선제적으로 로딩하는 로직을 제거하고, 에이전트가 최초 의사결정을 수행할 때 지연 로딩(Lazy Loading)하도록 구조를 변경합니다.

```python
# [BEFORE]
all_value_orientations = ["wealth_and_needs", "needs_and_growth", "needs_and_social_status"]
for vo in all_value_orientations:
    ai_trainer.get_engine(vo)  # 🚨 선제 로딩 발생 (150MB+ 메모리 점유)

# [AFTER]
# 해당 블록 삭제. 
# Household/Firm 생성 시 전달하는 ai_decision_engine은 Proxy 객체이거나, 
# 실제 의사결정 함수 호출(make_decision) 시점에 AIEngineRegistry에서 get_engine()을 호출하도록 위임(Delegate) 패턴 적용.
```
*Note: `HouseholdAI`와 `FirmAI` 클래스 내부에서 `AIEngineRegistry`의 참조만 들고 있다가 필요할 때 엔진을 획득하도록 생성자 시그니처 수정이 동반되어야 합니다.*

### 2.2 부동산 리스트 최적화 (`simulation/initialization/initializer.py`)
수만 단위의 `RealEstateUnit` 인스턴스를 한 번에 리스트로 생성하는 것을 방지하고, 제네레이터(Generator)나 지연 초기화(Lazy Initialization) 방식을 도입합니다.

```python
# [BEFORE]
sim.real_estate_units = [
    RealEstateUnit(id=i, estimated_value=self.config.INITIAL_PROPERTY_VALUE, rent_price=self.config.INITIAL_RENT_PRICE) 
    for i in range(self.config.NUM_HOUSING_UNITS)
]

# [AFTER]
# Option A: Dictionary 기반의 필요 시 생성 (On-demand Initialization)
sim.real_estate_units = {} # Dictionary로 변경하여 소유권 분배 시점에만 생성
# Option B: Factory를 통한 지연 생성 패턴 적용
```

## 3. 예외 처리 (Exceptions & Handling)
- `EngineNotLoadedError`: AI 엔진 지연 로딩 중 메모리 부족 또는 파일 I/O 문제로 엔진 로드에 실패할 경우, 룰 기반(Rule-based) 엔진으로 Fallback 하거나 에러를 기록하고 해당 에이전트를 `Inactive` 상태로 전환.
- `RealEstateUnitNotFoundError`: 부동산 객체가 지연 생성되기 전 접근될 경우, 시스템은 기본값을 가진 `RealEstateUnit` 객체를 동적으로 생성하여 반환.

## 4. 인터페이스 명세 (API Outline)

```python
# modules/ai_engine/api.py (Draft)
from typing import Protocol, Any
from dataclasses import dataclass

class IAIEngineRegistry(Protocol):
    def get_engine(self, value_orientation: str) -> Any:
        """요청된 성향의 엔진을 반환하며, 메모리에 없을 경우 이때 로드합니다."""
        ...

@dataclass
class LazyAIEngineProxy:
    """엔진을 지연 로딩하기 위한 프록시 DTO/클래스"""
    registry: IAIEngineRegistry
    value_orientation: str
    _engine_instance: Any = None
    
    def get_real_engine(self) -> Any:
        if self._engine_instance is None:
            self._engine_instance = self.registry.get_engine(self.value_orientation)
        return self._engine_instance
```

## 5. 🚨 [Conceptual Debt] (정합성 부채)
- **Lazy Load Timing Risk**: AI 모델이 첫 틱(Tick 1)의 `make_decision`에서 일제히 로딩될 경우, 초기화 단계의 메모리 문제는 피하지만 첫 틱 진행 시 일시적인 프리징(Spike) 현상과 OOM이 지연 발생할 가능성이 있습니다.
- **Housing System Compatibility**: `HousingService` 및 `RealEstateMarket`이 `sim.real_estate_units`가 항상 1~N까지 가득 채워진 List라고 가정하는 로직(예: 길이 기반 인덱싱)이 있다면, Dictionary나 Generator로 변경 시 `AttributeError` 또는 `KeyError`가 발생할 수 있습니다. (구현 시 전수 조사 필요)

## 6. 검증 계획 (Testing & Verification Strategy)
- **New Test Cases**: 
  1. `test_ai_engine_lazy_loading`: 에이전트 생성 후 첫 틱 진행 전까지 `AIEngineRegistry.get_engine`이 호출되지 않음을 Mock을 통해 검증.
  2. `test_real_estate_on_demand_creation`: `NUM_HOUSING_UNITS`가 10,000일 때 초기 리스트 크기가 0이거나 소유권이 부여된 수만큼만 인스턴스가 생성되는지 확인.
- **Integration Check**: `test_simulation_full_run.py` (또는 상응하는 통합 테스트)를 실행하여 10,000 단위 인구에서 `MemoryError` 없이 Phase 4 및 Phase 5가 완료되는지 확인.

## 7. 🚨 Risk & Impact Audit (기술적 위험 분석)
- **Mandatory Ledger Audit**:
  - `TECH_DEBT_LEDGER.md` 분석 결과, 본 작업은 직접적으로 리스트 참조 누수(`TD-MEM-REGISTRY-INPLACE`)나 하드코딩 메모리 누수(`TD-MEM-TEARDOWN-HARDCODE`)를 악화시키지는 않습니다. 하지만 엔진 로딩 시점을 늦추는 과정에서 프록시(Proxy) 참조를 잘못 사용할 경우 가비지 컬렉션(GC) 누수 위험이 발생할 수 있습니다.
- **DTO/DAO Interface Impact**: `sim.real_estate_units`의 자료구조가 `List`에서 `Dict`나 지연 구조로 변경될 경우, 이 속성을 직접 접근하는 `SettlementSystem`이나 `HousingSystem`에 큰 타격이 있습니다.
- **테스트 영향도**: 수많은 기존 유닛 테스트가 `sim.real_estate_units[0]` 와 같은 List 인덱싱 접근을 사용할 가능성이 매우 높습니다. `Dict`로 변경 시 테스트 픽스처 전면 수정이 불가피합니다.

## 8. Mandatory Reporting Verification
- **Reporting Status**: 본 명세 작성 중 발견된 AI 프록시 패턴 적용으로 인한 첫 틱 OOM 지연 발생 가능성 및 부동산 리스트 참조 구조 변경 위험성을 `communications/insights/WO-SPEC-MEM-FIX-AI-LAZY-LOAD.md`에 기록하도록 지시를 완수했습니다. (구현자는 반드시 해당 위치에 보고서를 작성해야 합니다.)

---

## 9. 🔍 [ANTIGRAVITY REVIEW] 보완 사항

> [!IMPORTANT]
> **`AIEngineRegistry.get_engine()`은 이미 Lazy-Caching을 구현하고 있습니다.**

```python
# simulation/ai_model.py:L88-100
def get_engine(self, value_orientation: str) -> AIDecisionEngine:
    if value_orientation not in self._engines:  # ← 이미 캐시 확인
        engine = AIDecisionEngine(...)
        self._engines[value_orientation] = engine
    return self._engines[value_orientation]
```

### 수정된 구현 가이드

**Section 2.1 수정**: `LazyAIEngineProxy` 패턴은 **불필요합니다**. 실제 필요한 변경은 단 1가지:

```python
# [BEFORE] simulation_builder.py:L69-72
all_value_orientations = ["wealth_and_needs", "needs_and_growth", "needs_and_social_status"]
for vo in all_value_orientations:
    ai_trainer.get_engine(vo)  # 🚨 선제 로딩

# [AFTER] — 이 3줄을 삭제하면 끝.
# get_engine()은 이미 lazy-caching이므로, Phase 4 루프의
# ai_trainer.get_engine(value_orientation) (L160) 호출 시 최초 1회만 생성됩니다.
```

> [!WARNING]
> **Section 2.2 (RealEstateUnit Dict 전환)은 폭발 반경이 높아 별도 미션으로 분리를 권고합니다.**
>
> `HousingService`, `RealEstateMarket`, 다수 테스트가 `sim.real_estate_units[index]` List 인덱싱을 사용합니다.
> Dict 전환 시 전수 조사가 필요하며, 메모리 절감 효과 대비 리스크가 큽니다.
> **우선순위**: Phase F (Engine Singleton) → Phase H-1 (선제 로딩 제거) → Phase H-2 (RealEstate 분리 검토)
