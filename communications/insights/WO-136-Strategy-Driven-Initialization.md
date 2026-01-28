# Insight Report: WO-136 - Strategy-Driven Initialization

## 현상 (Phenomenon)
기존에는 시뮬레이션의 핵심 초기 변수(세율, 이자율, 에이전트 AI 타입 등)가 각기 다른 `config` 파일이나 모듈의 기본값으로 흩어져 있었습니다. 이로 인해 새로운 경제 시나리오를 적용하거나 테스트하기 위해 여러 파일을 수정해야 했고, 설정의 일관성을 유지하기 어려웠습니다.

## 원인 (Cause)
시스템에 시뮬레이션 시나리오의 전체 설정을 정의하고 주입할 수 있는 중앙화된 데이터 객체(DTO)가 부재했습니다. 각 컴포넌트가 개별적으로 자신의 설정을 조회하는 분산된 구조가 문제의 원인이었습니다.

## 해결 (Solution)
`simulation/dtos/strategy.py`에 `ScenarioStrategy` DTO를 확장하여 시나리오별 초기화 파라미터를 모두 포함시켰습니다. `SimulationInitializer`는 시뮬레이션 시작 시 이 DTO를 생성하고, `CentralBank`, `Government`, `DemographicManager`, `FirmSystem` 등 핵심 에이전트와 시스템에 이 DTO를 주입합니다. 각 컴포넌트는 주입받은 `strategy` 객체의 값을 자신의 기본값보다 우선하여 사용하도록 로직을 수정했습니다.

## 교훈 (Lesson Learned)
시나리오별 설정을 하나의 데이터 클래스(`ScenarioStrategy` DTO)로 중앙화함으로써, 시뮬레이션 로직과 정적 설정을 분리(decoupling)할 수 있었습니다. 이는 시스템의 유연성을 극대화하고, 다양한 조건에서의 테스트를 용이하게 하며, 설정 불일치로 인한 리스크를 줄입니다. 이 DTO는 특정 시뮬레이션 실행 환경의 '단일 진실 공급원(Single Source of Truth)' 역할을 수행하여 코드의 예측 가능성과 유지보수성을 크게 향상시킵니다.
