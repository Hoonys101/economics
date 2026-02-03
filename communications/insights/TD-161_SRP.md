# Insight: RealEstateUnit Dependency & SRP Violations (TD-161, TD-204, TD-205)

- **Date**: 2026-02-03
- **Status**: ACTIVE/IDENTIFIED
- **Category**: Architecture Design

## 1. 현상 (Observation)
- `RealEstateUnit`이 `is_under_contract` 상태 조회를 위해 서비스 계층(`IRealEstateRegistry`)을 직접 참조함. (TD-161)
- `BubbleObservatory`와 `Phase3_Transaction`이 너무 많은 책임을 보유한 "God Class" 형태를 띰.

## 2. 위험 (Risk)
- 데이터 객체가 무거워져 직렬화 및 테스트가 어려워짐.
- 모듈 간 결합도가 높아져 특정 기능 변경이 전체 시스템에 예기치 못한 영향을 미침.

## 3. 향후 계획 (Next Steps)
- `RealEstateUnit`의 행위 로직을 `HousingService`로 완전히 이전하여 순수 데이터 컨테이너로 리팩토링.
- `BubbleObservatory`의 측정(Tracker)과 알림(Alert) 로직 분리.
- `Phase3_Transaction`의 과다한 프로세싱 로직을 하위 전문 Phase로 분산 배치.
