# Work Order: WO-066 - High-Fidelity Sensory Architecture

**Phase:** 26 (Debt Liquidation)
**Priority:** **HIGH** (TD-010, TD-025 Liquidation)
**Assignee:** Jules Alpha (Available)

## 1. Problem Statement
정부 에이전트(AI)가 경제 상황을 인지할 때 두 가지 치명적인 결함이 있습니다.
1. **Sensory Lag (TD-010)**: 10틱 이동평균(SMA)에 의존하고 틱 업데이트 순서 문제로 인해, 급격한 쇼크(Shock) 발생 시 '한 발 늦게' 또는 '둔하게' 반응합니다.
2. **Blindness (TD-025)**: 거래량이 0인 시장의 가격이 0으로 인식되어, 디플레이션으로 오판하는 '환각' 증세가 있습니다.

## 2. Objective
정부의 감각 기관(Sensory System)을 수술하여 **'즉각적이고(Instant)' '절대 잊지 않는(Persistent)'** 고해상도 정보 수집 체계를 구축합니다.

## 3. Implementation Plan

### Task A: `EconomicIndicatorTracker` 보강 (TD-025)
- `simulation/metrics/economic_tracker.py`에 `price_memory` 딕셔너리를 추가하십시오.
- 거래량이 0일 때 0을 반환하지 말고, **Last Known Price (LKP)**를 반환하도록 로직을 수정하십시오.

### Task B: `Engine` 동기화 및 DTO 확장 (TD-010)
- `simulation/dtos.py`의 `GovernmentStateDTO` (또는 `SensoryInputDTO`)에 `instant_inflation`, `instant_gdp_growth` 필드를 추가하십시오.
- `simulation/engine.py`에서 `run_tick` 실행 순서를 조정하여, `tracker.track()` 호출 직후에 이 '순간 지표(Instant Metrics)'를 계산하고 정부에게 주입하십시오.

### Task C: Government Policy Logic 활용
- `simulation/agents/government.py`가 SMA뿐만 아니라 Instant 지표도 의사결정에 반영하도록(예: 가중치 7:3) 수정하십시오.

## 4. Verification
- `scripts/verify_monetary_policy.py` 또는 새로운 테스트 스크립트를 작성하여 다음을 검증하십시오.
    - **Shock Test**: 인위적 가격 폭등 시 `instant_inflation`이 즉시 반응하는가?
    - **LKP Test**: 10틱 동안 거래가 없어도 물가 지수가 0으로 추락하지 않고 유지되는가?

---
> [!IMPORTANT]
> 이 작업은 `Engine`의 실행 루프를 변경하므로, 다른 트랙(WO-062, WO-065)과의 병합 충돌에 유의하십시오.
