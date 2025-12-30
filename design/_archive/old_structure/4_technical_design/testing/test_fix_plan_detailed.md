# 테스트 스위트 복구: 상세 해결 계획

이 문서는 `pytest` 실행 시 발생하는 25개의 실패와 17개의 오류를 해결하기 위한 구체적인 기술 계획을 정의합니다.

## 1. `tests/test_engine.py`의 데이터베이스 연동 오류 (9개 오류)

- **원인:** `Simulation` 클래스 생성자(`__init__`)가 `repository.save_simulation_run`을 호출하지만, 테스트에 사용되는 모의(mock) `repository` 객체에 이 메서드가 정의되어 있지 않아 `AttributeError`가 발생합니다.
- **대상 파일:** `tests/test_engine.py`
- **해결 전략:** `unittest.mock.MagicMock`을 사용하여 모의 `repository` 객체에 `save_simulation_run` 메서드를 추가합니다.

- **수정 예시 (`tests/test_engine.py`의 `setup_method` 또는 각 테스트 함수 내):**
  ```python
  # 기존 코드
  self.mock_repo = MagicMock()

  # 수정 후
  self.mock_repo = MagicMock()
  self.mock_repo.save_simulation_run = MagicMock(return_value=1)
  # 또는 특정 테스트에 따라 필요한 반환값 설정
  ```

## 2. `tests/test_firm_decision_engine_new.py`의 로거 모의 오류 (16개 실패)

- **원인:** 로거 자체를 모의 객체로 만들었으나, 실제 코드에서는 `logger.debug(f"...")`와 같이 f-string 포매팅을 사용합니다. 모의 객체는 문자열화될 수 없으므로 `TypeError: __str__ returned non-string`가 발생합니다.
- **대상 파일:** `tests/test_firm_decision_engine_new.py`
- **해결 전략:** 로거 객체 전체가 아닌, `debug`, `info`, `warning`, `error` 등 실제 호출되는 메서드를 각각 모의(mock)하도록 수정합니다.

- **수정 예시 (`tests/test_firm_decision_engine_new.py`의 `setup_method`):**
  ```python
  # 기존 코드
  self.mock_logger = MagicMock()

  # 수정 후
  # 각 메서드를 개별적으로 모의 처리
  mock_logger = MagicMock()
  mock_logger.debug = MagicMock()
  mock_logger.info = MagicMock()
  mock_logger.warning = MagicMock()
  mock_logger.error = MagicMock()
  self.mock_logger = mock_logger
  ```

## 3. AI 의사결정 API 변경 미반영 (다수 `AttributeError`, `NameError`)

- **원인:** `HouseholdAI`의 핵심 의사결정 메서드가 `make_decisions`에서 `decide_and_learn`으로 변경되었고, `HouseholdDecisionEngine`의 생성자 및 관련 로직이 변경되었으나 테스트 코드가 이를 반영하지 못하고 있습니다.
- **대상 파일:** `tests/test_household_ai.py`, `tests/test_household_decision_engine.py`, `tests/test_household_decision_engine_new.py`
- **해결 전략:**
    1.  `HouseholdDecisionEngine`의 생성자 호출 부분을 현재 구현에 맞게 수정합니다. (필요한 인자 전달)
    2.  테스트 내에서 `make_decisions`를 호출하는 모든 부분을 `decide_and_learn` 호출로 변경하고, 새로운 API의 시그니처에 맞게 인자를 수정합니다.

## 4. 시장 거래 로직 테스트 오류 (`test_markets_v2.py`, `test_order_book_market.py`)

- **원인:** `OrderBookMarket.match_and_execute_orders` 메서드 내부에서 거래 매칭 후 `clear_market_for_next_tick`을 호출하여 오더북을 즉시 초기화합니다. 이로 인해 부분 체결 후 오더북에 남아있어야 할 주문을 검증하는 테스트가 실패합니다.
- **대상 파일:** `simulation/core_markets.py`, `tests/test_markets_v2.py`, `tests/test_order_book_market.py`
- **해결 전략:** `simulation/core_markets.py`의 `match_and_execute_orders` 메서드 내에서 `self.clear_market_for_next_tick()` 호출을 제거하거나 주석 처리합니다. 오더북 초기화는 `Simulation.run_tick`과 같은 상위 레벨에서 틱의 경계를 관리하며 명시적으로 호출하는 것이 올바른 설계입니다.

- **수정 예시 (`simulation/core_markets.py`):**
  ```python
  def match_and_execute_orders(self):
      # ... (매칭 로직) ...
      # self.clear_market_for_next_tick() # 이 라인을 제거 또는 주석 처리
      return transactions
  ```

## 5. `tests/test_logger.py`의 자체 테스트 오류

- **원인:** 테스트 간 상태가 공유되어, 특정 테스트에서 생성된 로그 파일이나 로거 핸들러가 다른 테스트에 영향을 미쳐 "파일이 존재하지 않음" 등의 오류를 유발합니다.
- **대상 파일:** `tests/test_logger.py`
- **해결 전략:** 각 테스트 함수가 실행되기 전(`setUp`)과 후(`tearDown`)에 로거를 완전히 새로운 상태로 리셋하고, 생성된 로그 파일을 삭제하는 등 정리 로직을 강화하여 테스트의 독립성을 보장합니다.

- **수정 예시 (`tests/test_logger.py`):**
  ```python
  import os
  import logging

  def tearDown(self):
      # 모든 핸들러 제거
      for handler in logging.getLogger().handlers[:]:
          logging.getLogger().removeHandler(handler)
      # 로그 파일 삭제
      if os.path.exists(self.log_file):
          os.remove(self.log_file)
  ```

## 실행 순서

1.  `test_engine.py` 수정 및 검증
2.  `test_firm_decision_engine_new.py` 수정 및 검증
3.  `test_household_*.py` 파일들 수정 및 검증
4.  `core_markets.py` 수정 및 관련 테스트 검증
5.  `test_logger.py` 수정 및 검증
6.  전체 `pytest` 실행으로 최종 확인
