# Real Estate & Integration (Phase 20 Step 3)

## 1. 개요 (Overview)
본 작업은 Phase 20 "The Matrix"의 마지막 단계로, 인구 통계적 소멸 위기에 대응하는 **이민(Immigration)** 시스템을 구축하고, **부동산 시장(Real Estate)**의 비용을 에이전트의 인지 구조(System 2)에 연동하는 것을 목표로 합니다.

## 2. 핵심 구현 사항 (Core Requirements)

### 2.1. `ImmigrationManager` (New Module)
- **위치**: `simulation/systems/immigration_manager.py`
- **조건**: 
 - (노동 부족) `unemployment_rate < 0.05` AND (빈 일자리) `job_vacancies > 0`
 - (인구 소멸) `total_population < 80` (기본 설정값 시)
- **행동**: 매 틱 위 조건 충족 시 5명의 새로운 가계(Household) 에이전트를 생성하여 시스템에 투입.
- **에이전트 스펙**: 
 - 초기 자산: 3000.0 ~ 5000.0
 - 교육 수준: 0~1 (무작위)
 - 성별: 무작위 (50:50)

### 2.2. System 2 Planner 고도화 (System 2 Integration)
- **위치**: `simulation/ai/system2_planner.py`
- **로직**: `project_future` 연산 시 주거 비용 반영
 - **임차/노숙**: `agent.is_homeless`이거나 실거주 주택이 없는 경우, 시장 평균 임대료(`avg_rent_price`)를 일일 비용으로 차감.
 - **모기지**: 본인 소유 주택에 모기지가 걸려 있는 경우, `mortgage_payment`를 일일 비용으로 차감.
- **목표**: 높은 주거비가 장기 NPV를 낮추어 출산율 저하를 유도하는 피드백 루프 완성.

### 2.3. Engine 연동
- **위치**: `simulation/engine.py`
- `run_tick` 내에서 `ImmigrationManager`를 호출하여 인구 유입 처리.

## 3. 검증 계획 (Verification)

### 3.1. 단위 테스트: `tests/test_phase20_integration.py`
- **이민 테스트**: 노동 시장이 과열(저실업) 상태일 때 새로운 에이전트가 유입되는지 확인.
- **인지 연동 테스트**: 부동산 임대료가 상승할 때 System 2의 `npv_wealth`가 하락하는지 확인.

## 4. 지침 (Instructions for Jules)
- 기존 `RealEstateUnit` 및 `HousingManager` 인터페이스를 최대한 활용하세요.
- 이민자 생성 시 `Simulation.next_agent_id`를 적절히 관리해야 합니다.
- `System2Planner`의 `project_future`는 매번 연산하지 않고 캐싱을 사용하므로, 비용 변화가 반영되는지 확인하세요.
