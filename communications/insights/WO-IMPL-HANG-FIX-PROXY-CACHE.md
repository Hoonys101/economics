# Insight Report: WO-IMPL-HANG-FIX-PROXY-CACHE

### [PERFORMANCE] God Class Proxy Lookup Overhead in Deep Loops

- **현상 (Symptoms)**: 시뮬레이션 초기화 중 대량의 에이전트(Households, Firms)를 순회하며 등록할 때 심각한 부트스트랩 지연(Hang) 현상이 발생합니다.
- **원인 (Causes)**: `Simulation` God Class의 `__getattr__`가 `WorldState`로의 프록시 맵핑을 담당하는데, 에이전트 생성 루프 내부에서 `sim.bank`, `sim.agents`, `sim.demographic_manager` 등을 반복 호출하여 10,000회 이상의 불필요한 프록시 탐색 오버헤드를 유발했습니다. 또한, 루프 이전에 객체가 초기화되지 않았을 경우의 예외 처리가 기존 코드의 느슨한 호출에 묻혀있었습니다.
- **해결 (Solution)**: 반복문 진입 전에 필요한 의존성 객체들을 식별하고, 로컬 변수(Local Reference)로 캐싱(`agents_local = sim.agents`, `bank_id_local = sim.bank.id if getattr(sim, 'bank', None) else None` 등)하여 프록시 조회를 각 속성당 1회로 제한했습니다. `demographic_manager`의 경우 기존의 엄격한 참조 에러(Strict bypass failure)가 누락되지 않도록 로컬 캐시를 활용하되 없으면 원본 속성에 접근해 에러를 던지도록 보완했습니다.
- **교훈 (Lessons Learned)**: 대규모 루프 연산이 발생하는 영역에서는 God Class 및 Proxy 인스턴스의 직접적인 속성 조회를 피하고, 반드시 로컬 참조 캐싱 패턴을 강제해야 합니다. 캐싱 리팩토링 중에는 에러가 발생하던 위치와 누락 시 조용히 넘어가는(silent fallback) 로직 변경의 뉘앙스를 철저히 파악해 원래의 스펙(Contract)을 보존해야 합니다.

## Regression Analysis & Test Evidence
모든 `tests/initialization/` 및 `tests/simulation/test_initializer.py` 테스트가 성공적으로 통과하며 기존 코드의 기능을 손상하지 않음을 검증했습니다. `SimulationInitializer`의 `Phase 4` 로직 내 DTO와 속성 서명이 완전히 동일하게 유지됩니다.

```text
tests/simulation/test_initializer.py::TestSimulationInitializer::test_registry_linked_before_bootstrap
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_registry_linked_before_bootstrap | Total Objects: 166769
PASSED                                                                   [100%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_registry_linked_before_bootstrap | Total Objects: 167563
...
============================== 1 passed in 2.34s ===============================

tests/initialization/test_atomic_startup.py::TestAtomicStartup::test_atomic_startup_phase_validation
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_atomic_startup_phase_validation | Total Objects: 166791
PASSED                                                                   [100%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_atomic_startup_phase_validation | Total Objects: 167500
...
============================== 1 passed in 3.33s ===============================
```