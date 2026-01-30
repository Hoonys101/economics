# Insight Report: Attribute Error in Stress Test

## 현상 (Phenomenon)
- `scripts/stress_test_perfect_storm.py` 스크립트 실행 중 `AttributeError: 'dict' object has no attribute 'gdp'` 오류가 발생하며 시뮬레이션이 비정상적으로 중단되었습니다.

## 원인 (Cause)
- `Simulation.get_market_snapshot()` 함수는 `TypedDict`, 즉 딕셔너리 객체를 반환합니다.
- 하지만 호출부(stress test 스크립트 및 `Simulation.log_tick` 메서드)에서는 반환된 객체를 클래스 인스턴스처럼 취급하여 속성 접근(`snapshot.gdp`)을 시도했습니다.
- 이 데이터 접근 방식의 불일치가 `AttributeError`의 직접적인 원인이었습니다.

## 해결 (Solution)
- `get_market_snapshot()`이 반환한 딕셔너리 객체에 접근하는 모든 코드를 속성 접근(`snapshot.gdp`)에서 키 기반 접근(`snapshot['gdp']`)으로 수정했습니다.

## 교훈 (Lesson Learned)
- **Data Contract 준수**: 모듈 간 데이터 구조(Data Contract)에 대한 명확한 정의와 준수가 필수적입니다. 함수가 딕셔너리를 반환한다면, 모든 호출부 역시 이를 딕셔너리로 다루어야 합니다.
- **방어적 코딩**: 이번 수정에서 추가된 `try-except` 블록, DB 테이블 사전 생성 로직, `exc_info=True` 로깅과 같이 잠재적 오류를 미리 방지하고 디버깅을 용이하게 하는 방어적 코딩 스타일을 적극적으로 적용해야 합니다.
