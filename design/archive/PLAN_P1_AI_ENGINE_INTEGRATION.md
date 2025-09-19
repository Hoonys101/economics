# [P1] AI 의사결정 엔진 통합 실행 계획

**목표:** 가계(`Household`)의 의사결정을 기존의 규칙 기반 로직에서 학습 가능한 `AIDecisionEngine`으로 전환하여, 동적이고 최적화된 행동을 유도한다.

---

## 1. 분석 (Analyze)

- **대상 파일:**
    - `simulation/core_agents.py`: `Household` 클래스가 의사결정 엔진을 어떻게 호출하는지 확인.
    - `simulation/decisions/household_decision_engine.py`: 현재 규칙 기반 로직 파악.
    - `simulation/ai_model.py`: 통합 대상인 `AIDecisionEngine`의 인터페이스 및 `make_decisions` 메소드 분석.
- **분석 도구:** `read_many_files`를 사용하여 관련 파일들의 내용을 한 번에 파악한다.

## 2. 계획 (Plan)

1.  `simulation/decisions/household_decision_engine.py`의 `make_decisions` 메소드 내용을 수정한다.
2.  기존의 복잡한 규칙 기반 로직을 제거하거나 주석 처리한다.
3.  `self.ai_engine.make_decisions()`를 호출하여 AI의 결정을 반환하도록 로직을 변경한다.
4.  `Household` 객체 생성 시 `AIDecisionEngine` 인스턴스가 `HouseholdDecisionEngine`에 정상적으로 주입되는지 `main.py`의 코드를 통해 다시 한번 확인한다.

## 3. 실행 (Execute)

- **수정 도구:** `replace` 또는 `write_file`을 사용하여 `household_decision_engine.py`의 `make_decisions` 메소드를 수정한다.

## 4. 검증 (Verify)

1.  **로그 추가:** `household_decision_engine.py`의 `make_decisions` 메소드에 AI 엔진이 호출되었음을 명확히 나타내는 로그를 추가한다.
2.  **테스트 실행:** `pytest tests/test_household_decision_engine.py`를 실행하여 기존 기능에 회귀 오류가 없는지 확인한다.
3.  **시뮬레이션 실행:** `python main.py`를 실행하고, 추가한 로그가 정상적으로 출력되는지 확인하여 AI 엔진이 실제로 의사결정에 사용되고 있는지 검증한다.
