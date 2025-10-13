# 테스트 실패 및 오류 해결 계획 (v2)

## 1. 문제 상황 요약

`pytest` 실행 결과, 총 101개 테스트 중 **25개 실패, 17개 오류**가 발생했습니다.

오류의 대부분은 최근 진행된 주요 아키텍처 변경 사항(데이터베이스 연동, AI 의사결정 로직 수정, 시장 매칭 로직 분리 등)을 테스트 코드가 따라가지 못해 발생하는 문제입니다.

## 2. 주요 문제 및 해결책

### 문제 1: 데이터베이스 연동 오류 (`tests/test_engine.py`)
- **현상:** `Simulation` 클래스가 생성될 때 데이터베이스에 시뮬레이션 실행 기록을 남기는 `save_simulation_run` 메서드를 호출하지만, 테스트에 사용되는 모의(mock) 데이터베이스 객체에 해당 메서드가 없어 9개의 테스트에서 오류가 발생합니다.
- **해결책:** `tests/test_engine.py`의 모의 `repository` 객체에 `save_simulation_run` 메서드를 명시적으로 추가하여, `Simulation` 클래스가 정상적으로 초기화될 수 있도록 수정합니다.

### 문제 2: 잘못된 로거(Logger) 모의(Mocking) 방식 (`tests/test_firm_decision_engine_new.py`)
- **현상:** 로거를 모의(mocking)하는 방식이 잘못되어, 로그 메시지 포매팅 과정에서 `TypeError`가 발생하며 16개 테스트가 실패합니다.
- **해결책:** 로거의 `debug`와 같은 메서드 자체를 모의(mock)하도록 `MagicMock` 설정을 수정하여, f-string 포매팅 관련 오류를 근본적으로 해결합니다.

### 문제 3: AI 의사결정 API 변경 미반영 (`tests/test_household_*.py`)
- **현상:** AI의 의사결정 메서드가 `make_decisions`에서 `decide_and_learn`으로 변경되었으나, 여러 테스트 파일에서 여전히 이전 메서드를 호출하려 하여 `AttributeError` 또는 `NameError`가 발생합니다.
- **해결책:** `HouseholdDecisionEngine`의 생성자 로직을 수정하고, 관련 테스트들이 새로운 AI 의사결정 흐름을 따르도록 수정합니다.

### 문제 4: 시장(Market) 거래 로직 테스트 오류 (`tests/test_markets_v2.py`, `tests/test_order_book_market.py`)
- **현상:** 거래 체결 후, 부분 체결되어 오더북에 남아있어야 할 주문이 사라져 테스트가 실패합니다.
- **해결책:** `OrderBookMarket`의 `match_and_execute_orders` 메서드에서 거래 후 오더북을 즉시 초기화하는 로직(`clear_market_for_next_tick`)을 제거합니다. 오더북 초기화는 시뮬레이션 엔진의 틱(tick) 시작/종료 시점에서 관리하는 것이 더 올바른 설계입니다.

### 문제 5: 로거(Logger) 자체의 테스트 오류 (`tests/test_logger.py`)
- **현상:** 로그 파일이 생성될 것으로 예상하는 테스트에서 파일이 존재하지 않아 실패합니다.
- **해결책:** 테스트 간의 상태 간섭을 막기 위해, 각 테스트 시작(`setUp`) 시 로거를 완전히 재초기화하고, 종료(`tearDown`) 시 정리하는 로직을 강화하여 테스트의 독립성을 보장합니다.