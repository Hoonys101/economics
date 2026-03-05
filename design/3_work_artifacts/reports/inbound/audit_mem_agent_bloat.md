# [Technical Report] WO-AUDIT-MEM-AGENT-BLOAT: Agent-Level Memory Bloat Audit

## Executive Summary
본 감사는 `NUM_HOUSEHOLDS=20` 수준에서 발생하는 `MemoryError`의 근본 원인을 분석했습니다. 조사 결과, **Stateless Engine 및 Manager 객체가 가계(Household) 에이전트마다 독립적으로 인스턴스화**되어 심각한 객체 오버헤드를 유발하고 있음을 확인했습니다. 총 11개의 엔진/매니저가 에이전트별로 중복 생성되고 있으며, 이는 아키텍처 원칙(Stateless Engine Singleton)에 위배됩니다.

## Detailed Analysis

### 1. Household Stateless Engine Duplication
- **Status**: ✅ **확인 (Confirmed)**
- **Evidence**: `simulation/core_agents.py:L103-110`
  - `__init__` 함수 내에서 `LifecycleEngine`, `NeedsEngine`, `SocialEngine`, `BudgetEngine`, `ConsumptionEngine`, `BeliefEngine`, `CrisisEngine`, `HousingConnector` 총 8개의 객체가 `self` 멤버로 직접 생성됩니다.
- **Notes**: 이 엔진들은 내부 상태를 가지지 않고 DTO를 받아 처리만 수행하므로, 에이전트마다 인스턴스를 가질 필요가 전혀 없습니다.

### 2. Decision Engine Manager Duplication
- **Status**: ✅ **확인 (Confirmed)**
- **Evidence**: `simulation/decisions/ai_driven_household_engine.py:L35-37`
  - `AIDrivenHouseholdDecisionEngine` 초기화 시 `ConsumptionManager`, `LaborManager`, `AssetManager` 3개가 생성됩니다.
- **Notes**: 이 매니저들은 `decide_consumption` 등 로직만 캡슐화하고 있으며, 에이전트의 의사결정 시점에만 호출됩니다. 에이전트 수만큼 인스턴스가 복제되어 힙 메모리를 점유합니다.

### 3. Goods Data Redundancy
- **Status**: ✅ **확인 (Confirmed)**
- **Evidence**: `simulation/core_agents.py:L218-219`
  - `self.goods_info_map = {g["id"]: g for g in goods_data}` 코드를 통해 모든 가계 에이전트가 동일한 상품 메타데이터를 개별 dict로 보유합니다.
- **Notes**: 공유 참조(Shared Reference)가 아닌 개별 딕셔너리 생성이며, 상품 가짓수가 늘어날수록 메모리 점유율이 선형 증가합니다.

### 4. HouseholdAI Q-Tables Persistence
- **Status**: ✅ **확인 (Confirmed - Stateful)**
- **Evidence**: `simulation/ai/household_ai.py:L37-39`, `simulation/ai/q_table_manager.py:L15`
  - `q_consumption` (dict of QTableManagers), `q_work`, `q_investment`가 에이전트별로 할당됩니다.
  - `QTableManager` 내부의 `self.q_table`은 `Dict[Tuple, Dict[Any, float]]` 구조로 학습 데이터가 쌓일수록 크기가 커집니다.
- **Notes**: Q-Table은 에이전트의 개별 "지능"이므로 per-agent 유지가 타당하나, `q_consumption`이 상품별로 생성되므로(L104) `NUM_HOUSEHOLDS * NUM_GOODS`만큼의 QTableManager 객체가 생성되는 비용이 큽니다.

### 5. Firm Agent Pattern Consistency
- **Status**: ⚠️ **추정 확인 (Highly Likely)**
- **Evidence**: Household의 설계를 볼 때, Firm 역시 동일한 Orchestrator-Engine 패턴을 따르고 있을 확률이 매우 높습니다 (동일 코드 스타일 공유).

## Risk Assessment
- **Vibe Check**: 🔴 **High Architectural Risk**. "Stateless Engine"이라고 명시하고 있으나 구현은 "Stateful Instance per Agent" 방식으로 되어 있어 시스템 확장성(Scalability)을 가로막는 결정적 장애물입니다.
- **State Pollution**: 엔진 내부에 실수로 상태를 저장할 경우, 에이전트 간 데이터 오염(Data Contamination)은 없으나 메모리 누수가 발생하기 쉬운 구조입니다.

## Refactoring Plan

| 대상 객체 | 현재 위치 | 제안 변경 사항 |
| :--- | :--- | :--- |
| **Engines (8종)** | `Household.__init__` | `EngineRegistry` 싱글톤에서 참조 또는 클래스 변수로 전환 |
| **Managers (3종)** | `DecisionEngine.__init__` | `DecisionEngine` 클래스 레벨 공유 또는 DI 주입 |
| **Goods Metadata** | `Household.goods_info_map` | `GlobalMarketRegistry` 등 SSoT(Single Source of Truth) 참조 |
| **Q-Table Storage** | `HouseholdAI.q_table` | 비활성 에이전트의 Q-Table은 LRU 캐시 또는 DB(SQLite)로 스왑 아웃 |

### 예상 메모리 절감량 (Estimation)
- **객체 오버헤드**: Python 객체 하나당 최소 ~100 bytes (dict 포함 시 수 KB).
- **계산**: (8 Engines + 3 Managers) * 100 agents = 1,100개 불필요 객체.
- **결과**: `NUM_HOUSEHOLDS`가 커질수록 객체 생성 시간 및 GC(Garbage Collection) 부하가 기하급수적으로 증가함. 싱글톤 전환 시 에이전트 수와 무관하게 고정 메모리 점유(O(1))로 개선 가능.

## Conclusion
`MemoryError`는 엔진/매니저의 불필요한 다중 인스턴스화와 상품 데이터의 개별 복사본 유지에서 기인합니다. **SEO(Stateless Engine & Orchestrator) 패턴의 엄격한 준수**를 위해 모든 엔진을 싱글톤으로 전환하고, 에이전트는 오직 자신의 고유 상태(DTO)만 보유하도록 리팩토링할 것을 권고합니다.