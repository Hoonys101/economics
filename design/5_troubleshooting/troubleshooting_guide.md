# 트러블슈팅 가이드 (Troubleshooting Guide)

이 문서는 경제 시뮬레이션 개발 과정에서 발생한 주요 문제점과 해결 방법을 기록합니다. 반복적인 오류를 방지하고, 문제 해결 과정을 문서화하여 지식 기반을 구축하는 것을 목표로 합니다.

---

## 1. `AttributeError: module 'config' has no attribute 'FIRM_PRODUCTION_TARGETS'`

*   **문제 인식 (Problem Recognition):** `app.py`에서 `Firm` 클래스를 인스턴스화할 때 `config.FIRM_PRODUCTION_TARGETS`라는 존재하지 않는 속성을 참조하여 `AttributeError`가 발생했습니다.
*   **확인 방법 (Verification Method):** 시뮬레이션 실행 시 `app.py`의 `create_simulation` 함수 호출 중 `Firm` 생성자에서 오류가 발생했습니다.
*   **해결 방법 (Solution Method):** `app.py`의 `create_simulation` 함수 내 `Firm` 생성자 호출에서 `production_targets=config.FIRM_PRODUCTION_TARGETS` 인자를 제거했습니다. `Firm` 클래스 생성자는 `production_targets` 인자를 직접 받지 않고, `config_module.FIRM_MIN_PRODUCTION_TARGET`를 사용하여 `self.production_target`을 초기화합니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** 클래스 생성자의 인자 목록과 호출 시 전달하는 인자가 일치하는지 항상 확인해야 합니다. 특히 `config` 모듈의 속성명과 사용법을 정확히 이해해야 합니다.

---

## 2. `sqlite3.ProgrammingError: Cannot operate on a closed database.`

*   **문제 인식 (Problem Recognition):** 시뮬레이션 스레드 또는 API 엔드포인트에서 데이터베이스 작업을 시도할 때 `sqlite3.ProgrammingError`가 발생했습니다. 이는 데이터베이스 연결이 예상보다 일찍 닫혔기 때문입니다.
*   **확인 방법 (Verification Method):**
    *   **시뮬레이션 스레드:** `app.py`의 `run_simulation_loop`에서 `simulation_instance.run_tick()` 호출 중 `repository.save_simulation_run()`에서 오류 발생.
    *   **API 엔드포인트:** `/api/market/transactions`와 같은 API 호출 시 `get_repository()`에서 오류 발생.
*   **해결 방법 (Solution Method):**
    *   **시뮬레이션 스레드:** `app.py`의 `create_simulation` 함수 내에서 `SimulationRepository()` 인스턴스를 직접 생성하여 시뮬레이션 스레드가 독립적인 데이터베이스 연결을 가지도록 했습니다.
    *   **API 엔드포인트:** `app.py`에서 `@app.teardown_appcontext` 데코레이터와 `close_repository_on_teardown` 함수를 제거하여 Flask 요청 컨텍스트 종료 시 데이터베이스 연결이 닫히는 것을 방지했습니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** Flask의 애플리케이션 컨텍스트 및 요청 컨텍스트와 백그라운드 스레드 간의 데이터베이스 연결 관리 방식에 대한 이해가 중요합니다. 특히 장기 실행되는 스레드에서는 컨텍스트에 의존적인 리소스 관리를 피해야 합니다.

---

## 3. `NameError: name 'HouseholdAI' is not defined`

*   **문제 인식 (Problem Recognition):** `app.py`에서 `HouseholdAI` 및 `FirmAI` 클래스를 사용하려고 했으나, 해당 클래스들이 임포트되지 않아 `NameError`가 발생했습니다.
*   **확인 방법 (Verification Method):** 시뮬레이션 시작 시 `app.py`의 `create_simulation` 함수에서 `HouseholdAI` 또는 `FirmAI` 객체 생성 중 오류 발생.
*   **해결 방법 (Solution Method):** `app.py` 파일 상단에 `from simulation.ai.household_ai import HouseholdAI` 및 `from simulation.ai.firm_ai import FirmAI` 임포트 문을 추가했습니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** 새로운 클래스를 사용하거나 기존 클래스의 위치를 변경할 때는 항상 해당 파일에 올바른 임포트 문이 추가되었는지 확인해야 합니다.

---

## 4. `AttributeError: 'AIDecisionEngine' object has no attribute '_get_strategic_state'`

*   **문제 인식 (Problem Recognition):** `simulation/engine.py`에서 `firm.decision_engine.ai_engine._get_strategic_state()`를 호출할 때, `ai_engine`이 `AIDecisionEngine` 인스턴스여서 `_get_strategic_state` 메서드가 없어 `AttributeError`가 발생했습니다. `_get_strategic_state`는 `FirmAI` 및 `HouseholdAI`에 정의되어야 합니다.
*   **확인 방법 (Verification Method):** 시뮬레이션 실행 중 `run_tick` 함수에서 `Firm` 또는 `Household`의 AI 엔진으로부터 전략적 상태를 가져오는 부분에서 오류 발생.
*   **해결 방법 (Solution Method):** `app.py`의 `create_simulation` 함수에서 `AIDrivenFirmDecisionEngine` 및 `AIDrivenHouseholdDecisionEngine`을 인스턴스화할 때, `ai_engine` 인자로 `ai_manager.get_engine()`이 반환하는 `AIDecisionEngine`이 아닌, `FirmAI` 또는 `HouseholdAI` 인스턴스를 직접 생성하여 전달하도록 수정했습니다. 또한 `HouseholdAI` 생성자도 `FirmAI`와 동일하게 `ai_decision_engine` 인자를 받도록 수정했습니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** 계층적 AI 구조에서 각 계층의 역할과 책임, 그리고 인스턴스 간의 올바른 관계 설정이 중요합니다. 특히 `BaseAIEngine`을 상속받는 구체적인 AI 클래스(`FirmAI`, `HouseholdAI`)와 이들을 관리하는 `AIDecisionEngine` 간의 관계를 명확히 해야 합니다.

---

## 5. `AttributeError: 'FirmAI' object has no attribute '_discretize'`

*   **문제 인식 (Problem Recognition):** `FirmAI` 클래스의 `_get_strategic_state` 메서드에서 `self._discretize()`를 호출했으나, `FirmAI`에 해당 메서드가 정의되어 있지 않아 `AttributeError`가 발생했습니다. `_discretize` 메서드는 `HouseholdAI`에만 정의되어 있었습니다.
*   **확인 방법 (Verification Method):** 시뮬레이션 실행 중 `FirmAI`의 `_get_strategic_state` 호출 시 오류 발생.
*   **해결 방법 (Solution Method):** `_discretize` 메서드를 `HouseholdAI`에서 `BaseAIEngine` (부모 클래스)으로 이동시키고, `HouseholdAI`에서는 해당 메서드를 제거했습니다. 이로써 `FirmAI`와 `HouseholdAI` 모두 `BaseAIEngine`으로부터 `_discretize` 메서드를 상속받아 사용할 수 있게 되었습니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** 공통으로 사용되는 유틸리티 메서드는 상속 계층 구조의 적절한 위치(예: 추상 기본 클래스)에 정의하여 코드 중복을 피하고 일관성을 유지해야 합니다.

---

## 6. `NameError: name 'Aggressiveness' is not defined`

*   **문제 인식 (Problem Recognition):** `simulation/ai/firm_ai.py` 파일에서 `Aggressiveness` Enum을 사용했으나, 해당 Enum이 임포트되지 않아 `NameError`가 발생했습니다.
*   **확인 방법 (Verification Method):** `firm_ai.py` 파일 로드 시 또는 `_get_tactical_actions` 메서드 호출 시 오류 발생.
*   **해결 방법 (Solution Method):** `simulation/ai/firm_ai.py` 파일 상단에 `from .enums import Aggressiveness` 임포트 문을 추가했습니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** 임포트 누락은 흔한 오류이므로, 새로운 클래스나 Enum을 사용할 때는 항상 임포트 여부를 확인해야 합니다.

---

## 7. `AttributeError: 'tuple' object has no attribute 'name'`

*   **문제 인식 (Problem Recognition):** `simulation/decisions/ai_driven_firm_engine.py`의 `_execute_tactic` 메서드에서 `tactic.name`을 호출할 때, `tactic` 변수가 `(Tactic, Aggressiveness)` 튜플이어서 `AttributeError`가 발생했습니다. `decide_and_learn` 메서드는 튜플을 반환하지만, `_execute_tactic`은 `Tactic` Enum 단일 객체를 기대했습니다.
*   **확인 방법 (Verification Method):** 시뮬레이션 실행 중 `Firm`의 의사결정 과정에서 `_execute_tactic` 로깅 부분에서 오류 발생.
*   **해결 방법 (Solution Method):** `AIDrivenFirmDecisionEngine.make_decisions`에서 `self.ai_engine.decide_and_learn`의 반환값을 `chosen_tactic_tuple`로 받고, 이를 `tactic, aggressiveness = chosen_tactic_tuple`과 같이 언팩하도록 수정했습니다. 또한 `_execute_tactic` 메서드의 시그니처를 `(tactic: Tactic, aggressiveness: Aggressiveness, ...)`로 변경하고, 로깅 시 `tactic.name`을 사용하도록 수정했습니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** 함수나 메서드의 반환 타입과 이를 사용하는 코드의 기대 타입이 일치하는지 항상 확인해야 합니다. 특히 튜플 언팩킹 시 변수 개수를 정확히 맞춰야 합니다.

---

## 8. `AttributeError: 'OrderBookMarket' object has no attribute 'place_place_order'`

*   **문제 인식 (Problem Recognition):** `simulation/engine.py`의 `run_tick` 메서드에서 `market.place_place_order()`라는 오타로 인해 `AttributeError`가 발생했습니다.
*   **확인 방법 (Verification Method):** 시뮬레이션 실행 중 `Household`의 주문을 시장에 제출하는 부분에서 오류 발생.
*   **해결 방법 (Solution Method):** `simulation/engine.py` 파일에서 `market.place_place_order`를 올바른 메서드명인 `market.place_order`로 수정했습니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** 코드 작성 시 오타에 주의하고, 메서드 호출 전에 해당 객체가 해당 메서드를 가지고 있는지 확인하는 습관을 들여야 합니다.

---

## 9. `TypeError: AIDrivenFirmDecisionEngine.make_decisions() missing 2 required positional arguments: 'market_data' and 'current_time'`

*   **문제 인식 (Problem Recognition):** `simulation/firms.py`의 `Firm.make_decision` 메서드에서 `self.decision_engine.make_decisions`를 호출할 때, `markets`와 `goods_data` 인자를 전달하지 않아 `TypeError`가 발생했습니다.
*   **확인 방법 (Verification Method):** 시뮬레이션 실행 중 `Firm`의 의사결정 과정에서 `AIDrivenFirmDecisionEngine.make_decisions` 호출 시 오류 발생.
*   **해결 방법 (Solution Method):** `simulation/firms.py` 파일의 `Firm.make_decision` 메서드에서 `self.decision_engine.make_decisions`를 호출할 때 `markets=self.decision_engine.markets`와 `goods_data=self.decision_engine.goods_data` 인자를 추가하여 모든 필수 인자를 전달하도록 수정했습니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** 메서드 시그니처를 변경하거나 호출하는 쪽에서 인자를 누락하지 않도록 주의해야 합니다. 특히 `TYPE_CHECKING`을 사용하는 경우 런타임 오류를 방지하기 위해 더욱 꼼꼼한 확인이 필요합니다.

---

## 10. `AttributeError: 'float' object has no attribute 'values'`

*   **문제 인식 (Problem Recognition):** `simulation/metrics/economic_tracker.py`의 `track` 메서드에서 `total_production`을 계산할 때 `f.current_production.values()`를 호출했으나, `Firm.current_production`이 `float` 타입이어서 `AttributeError`가 발생했습니다.
*   **확인 방법 (Verification Method):** 시뮬레이션 실행 중 경제 지표 추적 부분에서 오류 발생.
*   **해결 방법 (Solution Method):** `simulation/metrics/economic_tracker.py` 파일에서 `total_production` 계산 로직을 `sum(f.current_production for f in firms if getattr(f, "is_active", False))`로 수정하여 `float` 값을 직접 합산하도록 변경했습니다.
*   **인사이트/교훈 (Insight/Lesson Learned):** 객체의 속성 타입과 그 속성을 사용하는 방식이 일치하는지 확인해야 합니다. 특히 집계 함수를 사용할 때는 데이터의 구조를 정확히 이해하고 적용해야 합니다.
