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

## 9. 기업 생산량 0 버그 수정 (P0 Blocker)

### 문제인식
시뮬레이션 초기 설정 후 기업이 직원을 유지하지 못하고 생산량이 0이 되는 문제. `MASTER_PLAN.md`에 P0 블로커로 명시됨. 로그 분석 결과, 초기 고용된 가계의 `is_employed` 플래그가 `False`로 유지되어 `_handle_agent_lifecycle`에서 기업의 직원 목록에서 제거되는 것이 확인됨.

### 근본 원인
`main.py`에서 시뮬레이션 초기 에이전트 설정 시, 가계를 기업에 고용하는 로직(`firm.employees.append(household_to_hire)`)에서 `household_to_hire.employer_id`는 설정되었으나, 해당 가계의 `household_to_hire.is_employed` 플래그가 명시적으로 `True`로 설정되지 않았음. 이로 인해 가계는 고용된 상태임에도 불구하고 `is_employed`가 `False`로 남아있었고, 다음 틱의 `simulation/engine.py` 내 `_handle_agent_lifecycle` 메서드에서 `is_employed` 상태를 확인하는 필터링 로직에 의해 기업의 직원 목록에서 제거됨.

### 해결방법
`main.py`의 초기 고용 로직에서 `household_to_hire.employer_id`를 설정한 직후 `household_to_hire.is_employed = True`를 명시적으로 추가하여 가계의 고용 상태를 올바르게 반영하도록 수정.

**수정 코드 (`main.py`):**
```python
# 기존 코드
# household_to_hire.employer_id = firm.id
# logging.info(f"Firm {firm.id} initially hired Household {household_to_hire.id}.", extra={'tick': 0, 'agent_id': firm.id, 'tags': ['hiring', 'init']})

# 수정된 코드
household_to_hire.employer_id = firm.id
household_to_hire.is_employed = True # Explicitly set is_employed to True
logging.info(f"Firm {firm.id} initially hired Household {household_to_hire.id}.", extra={'tick': 0, 'agent_id': firm.id, 'tags': ['hiring', 'init']})
```

### 검증
수정 후 시뮬레이션을 실행하고 로그(`logs/debug_custom.log`)를 분석한 결과, 가계가 기업에 의해 올바르게 고용 상태를 유지하고, 기업의 `employees` 목록에서 제거되지 않으며, 생산 활동을 정상적으로 수행하는 것이 확인됨.

### 인사이트
초기 설정 또는 데이터 주입 단계에서 에이전트의 핵심 상태(예: `is_employed`)가 올바르게 초기화되지 않으면, 이후 시뮬레이션 로직(예: `_handle_agent_lifecycle`의 필터링)에서 예상치 못한 부작용을 초래할 수 있음. 특히, 상태 변경이 여러 모듈에 걸쳐 발생할 경우, 모든 관련 상태가 일관되게 업데이트되는지 주의 깊게 확인해야 함.
