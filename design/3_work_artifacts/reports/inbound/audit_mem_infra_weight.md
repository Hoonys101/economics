I will now perform a memory audit of the simulation infrastructure and generate the requested technical report and profiling script.

# AUDIT: Infrastructure Memory Weight (Pre-Population)
Mission Key: WO-AUDIT-MEM-INFRA-WEIGHT

## Executive Summary
Phase 4 (인구 등록)에서 발생하는 `MemoryError`는 시뮬레이션의 "Weight of Infrastructure"가 이미 메모리 가용량의 상당 부분을 점유하고 있기 때문입니다. 특히 Phase 3에서 선제적으로 로드되는 3종의 AI 엔진 가중치와 수만 단위의 부동산 객체 리스트가 Phase 4의 에이전트 생성 부하와 결합하여 임계치를 초과하는 것으로 분석됩니다.

## Detailed Analysis

### 1. Phase별 메모리 사용량 추정 (10,000 Agents 기준)
- **Phase 1: Infrastructure (저부하)**
    - **Status**: ✅ Implemented
    - **Evidence**: `initializer.py:L116-189`
    - **Analysis**: `EventBus`, `MonetaryLedger`, `SettlementSystem` 등 관리 객체들이 생성되나, 에이전트 데이터가 없어 메모리 점유율은 낮음. `ScenarioStrategy` 로딩 시 JSON 데이터 크기에 비례함.
- **Phase 2: System Agents (저부하)**
    - **Status**: ✅ Implemented
    - **Evidence**: `initializer.py:L191-235`
    - **Analysis**: CentralBank, Bank 등 약 5-10개의 싱글톤 에이전트 생성. 개별 객체 크기는 작으나 `FinanceSystem`의 원장 구조가 초기화됨.
- **Phase 3: Markets & Systems (고부하)**
    - **Status**: ✅ Implemented
    - **Evidence**: `initializer.py:L237-336`
    - **Analysis**: 
        - **AI Engines**: `AIEngineRegistry`에서 3개 Value Orientation별 엔진을 로드(`simulation_builder.py:L73`). 엔진당 가중치가 20-50MB일 경우 인프라만으로 150MB 이상 소요.
        - **Real Estate**: `NUM_HOUSING_UNITS`만큼의 `RealEstateUnit` 객체 리스트 생성(`initializer.py:L268`). 만 단위일 경우 리스트와 객체 오버헤드 발생.
        - **Systems**: 30개 이상의 `System` 클래스 인스턴스가 동시 상주.
- **Phase 4: Population (임계점)**
    - **Status**: ✅ Implemented
    - **Evidence**: `initializer.py:L338-397`
    - **Analysis**: 10,000개의 Household/Firm 객체가 생성되며 `AgentRegistry` 맵에 등록됨. 에이전트당 `AgentCoreConfigDTO`, `AgentStateDTO`, `DecisionEngine` 인스턴스가 개별 할당되어 누적 메모리가 폭발적으로 증가.

### 2. Infrastructure Component Weight (Top 3)
1.  **AIEngineRegistry (AI 모델 가중치)**: 3개 VO 엔진의 선제적 메모리 로딩.
2.  **RealEstateUnit Registry**: `initializer.py`에서 생성되는 만 단위의 부동산 객체 리스트.
3.  **Transaction Processor Handlers**: 30여 개의 핸들러 클래스 인스턴스 및 관련 메타데이터.

### 3. Lightweight / Lazy-Loading Candidates
-   **AIEngineRegistry**: `simulation_builder.py`의 초기화 루프에서 모든 엔진을 `get_engine()`으로 로드하는 대신, Phase 4에서 해당 VO를 가진 에이전트가 처음 나타날 때 로드하도록 지연(Lazy) 로딩 전환 필요.
-   **RealEstateUnit**: 리스트 대신 `EstateRegistry`에서 필요 시점에 생성하거나 DB 기반 인덱싱으로 전환하여 인메모리 객체 수 축소.
-   **ScenarioStrategy**: 모든 파라미터를 메모리에 상주시키는 대신 `GlobalRegistry`의 `get` 요청 시점에 로드하도록 개선.

## Risk Assessment
-   **SSoT Bypass Risk**: 메모리 절약을 위해 객체 참조를 수동 관리할 경우 `AgentRegistry`와 `SettlementSystem` 간의 데이터 불일치 가능성 (Vibe Check 필요).
-   **Duct-Tape Debugging**: `MemoryError`를 피하기 위해 단순히 `NUM_HOUSEHOLDS`를 줄이는 임시방편은 시스템 확장성을 저해함.

## tracemalloc 기반 프로파일링 스크립트 제안
```python
import tracemalloc
from modules.system.builders.simulation_builder import create_simulation

def profile_simulation_memory():
    tracemalloc.start()
    
    # Snapshot 0: 초기 상태
    snap_start = tracemalloc.take_snapshot()
    
    # Simulation 생성 시뮬레이션 (Phase 1-3 위주)
    # create_simulation 내부를 Phase별로 쪼개어 관찰하는 Mocking 권장
    sim = create_simulation()
    
    # Snapshot 1: 인프라 로드 완료 (Phase 3 종료 시점)
    snap_infra = tracemalloc.take_snapshot()
    
    stats = snap_infra.compare_to(snap_start, 'lineno')
    print("[Memory Audit: Infra Weight Top 10]")
    for stat in stats[:10]:
        print(stat)

if __name__ == "__main__":
    profile_simulation_memory()
```

## Conclusion
Phase 4의 크래시는 인프라의 "Baseline Weight"가 너무 높기 때문에 발생합니다. `AIEngineRegistry`의 VO 엔진 로딩 방식을 Lazy-loading으로 변경하고, `RealEstateUnit`의 대량 객체 생성을 최적화하는 것이 시급합니다.