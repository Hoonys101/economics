# Insight Report: WO-138 - Architectural Shift to Settlement System

## 현상 (Observation)
- Government와 TaxAgency 관련 테스트에서 자산(assets)의 최종 값을 직접 검증하던 로직이 실패하기 시작했습니다.
- 기존에는 `government.provide_household_support`와 같은 함수가 호출되면, 해당 함수 내에서 직접 대상의 자산을 변경했습니다.

## 원인 (Cause)
- 시스템의 아키텍처가 변경되었습니다. 이제 금융 관련 행위는 직접적인 자산 변경을 유발하는 대신, 중앙 `TransactionProcessor`가 처리할 `Transaction` 객체를 생성하여 반환합니다.
- 자금의 실제 이동은 `SettlementSystem`을 통해 이루어지며, 모든 자금 흐름을 명확하게 추적하고 Zero-Sum 원칙을 강제합니다.

## 해결 (Resolution)
- `test_government.py`와 `test_tax_agency.py`의 테스트 코드를 리팩토링했습니다.
- 이제 테스트는 자산의 최종 값을 검증하는 대신, 올바른 파라미터(금액, 수신자 등)를 가진 `Transaction` 객체가 반환되는지와 `SettlementSystem`의 `transfer` 메소드가 정확히 호출되는지를 검증합니다.

## 교훈 (Lesson Learned)
- **책임 분리 원칙(SoC)**: 행위(Action)를 정의하는 모듈과 그 결과를 시스템 상태에 반영(State Mutation)하는 모듈을 분리하면 시스템의 테스트 용이성과 예측 가능성이 크게 향상됩니다.
- **테스트는 명세다**: 테스트는 시스템의 현재 동작 방식을 보여주는 가장 정확한 명세서입니다. 아키텍처 변경 시, 실패하는 테스트는 변경되어야 할 로직의 범위를 알려주는 중요한 지표입니다.
