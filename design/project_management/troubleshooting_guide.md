## 5. 기업 생산량 0 및 고용 문제

### 문제인식
시뮬레이션 초기 설정 후 기업이 직원을 유지하지 못하고 생산량이 0이 되는 문제. `MASTER_PLAN.md`에 P0 블로커로 명시됨.

### 확인방법
1.  시뮬레이션 로그에서 기업의 `employees` 리스트가 비어 있는지 확인.
2.  `simulation/engine.py`의 `_handle_agent_lifecycle` 메서드에서 비활성 에이전트 처리 로직 확인.
3.  가계가 노동 시장에 `SELL` 주문을 제출하는지 확인.

### 해결방법
1.  **가계의 노동 공급 로직 부재**: `simulation/decisions/household_decision_engine.py`의 `make_decisions` 메서드에 실업 상태이고 노동 욕구가 높은 가계가 노동 시장에 `SELL` 주문을 제출하는 규칙 기반 로직을 추가합니다.
    *   `config.LABOR_NEED_THRESHOLD` 및 `config.HOUSEHOLD_MIN_WAGE_DEMAND` 값을 활용합니다.
2.  **`Household` 객체의 `active` 속성 오류**: `simulation/engine.py`의 `_handle_agent_lifecycle` 메서드에서 `h.active`를 `h.is_active`로 수정합니다.
    *   **예방**: `tests/test_engine.py`에 `test_handle_agent_lifecycle_removes_inactive_agents` 단위 테스트를 추가하여 `_handle_agent_lifecycle`의 정확한 동작을 검증합니다.

## 6. `OrderBookMarket`의 `KeyError` 및 내부 상태 불일치

### 문제인식
`test_decision_engine_integration.py` 테스트에서 `OrderBookMarket` 인스턴스의 `buy_orders` 또는 `sell_orders` 딕셔너리에 `KeyError`가 발생하거나, `place_order` 호출 후에도 딕셔너리가 비어 있는 현상. `_add_order`가 호출되었음에도 내부 상태가 변경되지 않는 것처럼 보임.

### 확인방법
1.  `OrderBookMarket.place_order` 및 `_add_order` 메서드 내부에 디버그 `print` 문을 추가하여 `order_book` 매개변수와 `self.buy_orders`, `self.sell_orders`의 객체 ID를 비교합니다.
2.  `pytest -s`로 테스트를 실행하여 디버그 출력을 확인합니다.

### 해결방법
1.  **`OrderBookMarket.place_order`의 `transactions` 초기화 누락**: `simulation/markets/order_book_market.py`의 `place_order` 메서드 시작 부분에 `self.transactions = []`를 추가하여 이전 호출의 트랜잭션이 누적되지 않도록 합니다.
2.  **`_add_order`의 매개변수 별칭 문제**: `simulation/markets/order_book_market.py`의 `_add_order` 메서드를 리팩토링하여 `order_book` 매개변수를 제거하고, `order.order_type`에 따라 `self.buy_orders` 또는 `self.sell_orders`를 직접 수정하도록 변경합니다.
    *   `place_order`에서 `_add_order`를 호출할 때 `self._add_order(order)` 형태로 변경합니다.
3.  **테스트 단언문 조정**: `tests/test_decision_engine_integration.py`의 관련 테스트에서 `KeyError`가 발생하지 않도록 단언문을 조정합니다. (예: `assert 'food' in goods_market.sell_orders` 대신 `assert len(goods_market.sell_orders.get('food', [])) == 1`과 같이 안전하게 접근하거나, 매칭 후에는 `assert not goods_market.sell_orders.get('food')`와 같이 비어 있음을 확인).

## 7. `LoanMarket`의 알 수 없는 주문 유형 처리 문제

### 문제인식
`tests/test_loan_market.py`의 `test_place_order_unknown_type_logs_warning` 테스트가 실패하며, `LoanMarket.place_order`가 알 수 없는 주문 유형에 대해 경고를 로깅하지 않거나 예상과 다르게 로깅함.

### 확인방법
1.  `simulation/loan_market.py`의 `LoanMarket.place_order` 메서드 로직을 확인하여 알 수 없는 `order.order_type`에 대한 처리 방식과 로깅 여부를 확인합니다.
2.  `tests/test_loan_market.py`의 해당 테스트에서 `mock_logger.warning.assert_called_once_with`의 기대값과 실제 로깅 메시지를 비교합니다.

### 해결방법
1.  **`LoanMarket.place_order`에 경고 로깅 추가**: `simulation/loan_market.py`의 `LoanMarket.place_order` 메서드에 `if/elif` 블록의 `else` 절을 추가하여 알 수 없는 `order.order_type`에 대해 `logger.warning`를 명시적으로 호출하도록 합니다.
2.  **테스트 단언문 조정**: `tests/test_order_book_market.py`의 `test_place_order_unknown_type_logs_warning` 테스트에서 `_add_order`와 `place_order` 모두에서 경고가 발생할 수 있으므로, `mock_logger.warning.assert_called_once_with` 대신 `mock_logger.warning.assert_called_with`를 사용하고 `mock_logger.warning.call_count`를 확인하여 예상되는 호출 횟수(예: 2회)를 검증합니다.

## 8. `simulation/engine.py`의 `SyntaxError`

### 문제인식
`run_experiment.py` 실행 중 `simulation/engine.py` 파일의 `self.db_manager.save_ai_decision(` 호출 부분에서 괄호가 닫히지 않은 `SyntaxError`가 발생했습니다. 이는 파일 끝에 불완전한 코드가 중복으로 포함되어 발생한 것으로 확인되었습니다.

### 확인방법
`run_experiment.py` 실행 시 발생하는 `SyntaxError`의 스택 트레이스를 통해 `simulation/engine.py`의 특정 라인에서 문법 오류를 확인했습니다.

### 해결방법
`simulation/engine.py` 파일 전체를 다시 읽어와, 파일 끝에 중복으로 포함된 불완전한 코드 블록을 제거하고 올바른 내용으로 파일을 덮어썼습니다.

### 인사이트
코드 편집 과정에서 발생할 수 있는 복사-붙여넣기 오류나 불완전한 코드 조각이 파일에 남아있을 경우, 예상치 못한 문법 오류를 유발할 수 있습니다. 특히 `replace`와 같은 자동화된 도구를 사용할 때, `old_string`이 너무 일반적이면 의도치 않은 위치까지 수정되거나, 파일이 손상될 수 있으므로 주의해야 합니다.

## 9. 로깅 시스템 설정 오류

### 문제인식
`run_experiment.py` 실행 시 `DEBUG` 레벨의 상세 로그가 `logs/simulation_log_StandardLog.csv` 파일에 제대로 기록되지 않고, 오래된 단위 테스트 로그만 남아있었습니다. 이는 로깅 설정이 올바르게 적용되지 않았음을 의미합니다.

### 확인방법
1.  `logs/simulation_log_StandardLog.csv` 파일의 내용을 확인하여 `run_experiment.py` 실행과 관련된 상세 로그가 누락되었음을 확인했습니다.
2.  `main.py` 및 `config.py` 파일을 검토하여 로깅 설정 초기화 로직을 분석했습니다.

### 해결방법
1.  **로깅 설정 중앙화:** `utils/logging_manager.py` 파일을 새로 생성하여 로깅 설정을 중앙에서 관리하는 `setup_logging` 함수를 구현했습니다. 이 함수는 `config.ROOT_LOGGER_LEVEL`을 읽어와 파일 핸들러와 스트림 핸들러를 설정하고, 모든 로그를 지정된 CSV 파일과 콘솔에 출력하도록 구성합니다.
2.  **`main.py` 수정:** `main.py` 시작 부분에서 `logging_manager.setup_logging()`을 호출하여 전역 로깅 설정을 적용하고, `custom_logger`와 `main_logger`를 `logging.getLogger(__name__)`으로 통일하여 일관성을 확보했습니다.

### 인사이트
복잡한 시뮬레이션 환경에서는 로깅 설정이 매우 중요합니다. 특히 여러 모듈에서 로거를 사용할 경우, 중앙 집중식 로깅 관리자를 통해 일관된 설정과 출력을 보장하는 것이 디버깅 효율성을 극대화하는 데 필수적입니다.

## 10. 시장 거래 미발생 (수요-공급 테스트 실패의 근본 원인)

### 문제인식
수요-공급 법칙 검증 실험 결과, 모든 시나리오에서 'food'의 평균 가격과 거래량이 모두 0으로 기록되었습니다. 이는 시뮬레이션 내에서 'food' 거래가 전혀 이루어지지 않았음을 의미합니다.

### 확인방법
1.  `analyze_supply_demand.py` 실행 결과 `food_avg_price`와 `food_trade_volume`이 0으로 나타나는 것을 확인했습니다.
2.  `simulation_data.db`의 `transactions` 테이블을 직접 조회하여 거래 기록이 전혀 없음을 확인했습니다.
3.  `DEBUG` 레벨로 시뮬레이션을 실행하여 생성된 로그(`logs/simulation_log_StandardLog.csv`)를 분석했습니다.

### 근본 원인 및 해결방법
1.  **가계의 잘못된 주문 타입:**
    *   **문제:** 가계 에이전트가 상품 구매 주문을 낼 때, `Order` 객체의 `order_type`을 소문자 `'buy'`로 생성했습니다. `OrderBookMarket`은 대문자 `'BUY'`만 유효한 주문 타입으로 인식하여 이 주문들을 무시했습니다. 노동 시장 판매 주문도 소문자 `'sell'`로 생성되었습니다.
    *   **해결:** `simulation/decisions/household_decision_engine.py` 파일에서 `_execute_tactic` 메서드 내의 모든 주문 타입(`'buy'`, `'sell'`)을 대문자(`'BUY'`, `'SELL'`)로 수정하여 시장이 올바르게 인식하도록 했습니다.
2.  **가계의 초기 'food' 재고 부족:**
    *   **문제:** 시뮬레이션 시작 시 가계 에이전트가 'food' 재고를 전혀 가지고 있지 않아, 생존 욕구가 높아져도 소비할 'food'가 없어 소비에 실패했습니다.
    *   **해결:** `main.py` 파일에서 가계 에이전트를 초기화할 때, `config.INITIAL_HOUSEHOLD_FOOD_INVENTORY` 설정값을 사용하여 모든 가계에 초기 'food' 재고를 지급하도록 수정했습니다.

### 인사이트
시뮬레이션의 기본 경제 순환이 작동하기 위해서는 에이전트의 의사결정(주문 생성)과 시장 메커니즘(주문 처리) 간의 인터페이스가 정확히 일치해야 합니다. 또한, 에이전트가 초기부터 기본적인 활동을 수행할 수 있도록 적절한 초기 자원(재고)을 제공하는 것이 중요합니다.

---

## 11. 장기 TODO: 재래시장 모델 도입 (시장 설계 다변화)

### 문제인식
현재 시뮬레이션의 시장 모델은 모든 참가자에게 모든 계약이 공개되고 순차적으로 정렬되어 거래가 실행되는 '오더북' 방식입니다. 이는 효율적이지만, 현실 세계의 다양한 시장 형태를 모두 반영하지 못합니다. 특히, 비공식적이고 비정형적인 거래가 이루어지는 '재래시장'과 같은 모델을 도입하여 시장 메커니즘의 다양성을 확보하고 싶습니다.

### 목표
기존 오더북 시장 모델과 병행하여, 재래시장과 유사한 새로운 시장 모델을 구현하여 시뮬레이션의 현실성과 복잡성을 증대시킵니다. 이를 통해 시장 구조가 에이전트의 행동과 거시 경제 지표에 미치는 영향을 분석할 수 있는 기반을 마련합니다.

### 재래시장 모델 상세 설계 (장기 TODO)
*   **시장 개장 및 폐장:** 각 시뮬레이션 틱(tick)은 시장이 열리고 닫히는 하나의 '장'으로 간주합니다.
*   **공급자의 행동:**
    *   시장이 열리면, 공급자(기업)는 자신의 인벤토리에서 판매할 물품의 종류와 양을 결정하여 시장에 나옵니다.
    *   공급자는 시장이 폐장되기 전까지 물품을 판매해야 하므로, 시간이 지남에 따라 가격을 낮출 유인이 생깁니다.
*   **수요자의 행동:**
    *   수요자(가계)는 시장에서 `window` 수만큼의 공급자를 무작위 또는 특정 기준으로 탐색합니다.
    *   탐색한 공급자들의 제시 가격을 확인하고, 자신의 구매 의사 가격과 비교하여 거래를 시도합니다.
    *   **거래 성립 조건:** 공급자의 제시 가격이 수요자의 구매 의사 가격보다 낮거나 같으면 거래가 성립됩니다.
    *   **가격 결정:** 거래가 성립되면, 공급자 가격과 수요자 가격의 중간 가격으로 거래가 체결됩니다.
    *   **시장 이탈:** 수요자는 사고자 하는 물품을 모두 구매하면 시장에서 제외됩니다.
*   **시장 폐장 및 재고 소각:**
    *   정해진 시간(틱)이 지나 시장이 폐장되면, 공급자가 가져온 물품 중 판매되지 않고 남은 물품은 모두 소각됩니다.
    *   이는 공급자에게 재고 부담을 주어 가격 인하 유인을 강화합니다.

### 기대 효과
*   보다 현실적인 시장 환경 조성: 가격 협상, 정보 비대칭, 재고 소각 등의 요소를 통해 시장의 동적인 특성을 강화합니다.
*   에이전트 행동의 복잡성 증대: 공급자와 수요자는 시장 상황과 자신의 목표에 따라 가격 전략을 더욱 정교하게 수립해야 합니다.
*   시장 구조가 경제에 미치는 영향 분석: 오더북 시장과 재래시장 모델 간의 비교 분석을 통해 시장 구조가 가격 형성, 거래량, 에이전트의 이윤 등에 미치는 영향을 연구할 수 있습니다.

### 구현 방향 (향후 논의 필요)
*   `OrderBookMarket`과 별도의 `TraditionalMarket` 클래스 구현.
*   `HouseholdDecisionEngine` 및 `FirmDecisionEngine`에 재래시장 환경에 맞는 의사결정 로직 추가.
*   `window` 크기, 탐색 전략, 가격 협상 로직 등 세부 메커니즘 정의.