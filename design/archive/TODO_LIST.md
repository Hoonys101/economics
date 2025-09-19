# 경제 시뮬레이션 개발 TODO 리스트

---

## **Phase 1: 시뮬레이션 안정화 및 결과 분석**

*   **목표:** 안정적으로 실행되는 시뮬레이션의 결과를 분석하여 시스템의 거시적 특징을 파악하고, AI의 행동을 검증한다.

### 1.1. 시뮬레이션 데이터 분석
- [ ] **(실행)** `python run_experiment.py`를 실행하여 `baseline_timeseries.csv`와 `experiment_timeseries.csv` 최신 데이터 생성
- [ ] **(분석)** `analyze_results.py` 스크립트를 사용하거나, Jupyter Notebook 환경에서 위 CSV 파일들을 로드하여 주요 경제 지표(실업률, 평균 임금, 재화 가격 및 거래량, 총 생산량, 총 소비량 등)의 시계열 추이를 시각화하고 분석
- [ ] **(해석)** 분석 결과를 바탕으로 현재 시뮬레이션 경제의 특징(예: 경기 순환 주기, 인플레이션/디플레이션 경향, 특정 정책의 효과)을 문서화

### 1.2. AI 행동 검증
- [ ] **(로그 분석)** `simulation_results.csv` 파일에서 `AIDecision` 관련 로그, 특히 `is_trained`, `predicted_reward`, `exploration/exploitation` 분기 기록을 분석
- [ ] **(검증)** AI가 시간이 지남에 따라 `exploitation`(활용) 단계로 넘어가고 있는지, 예측 보상(`predicted_reward`)이 의미 있는 패턴을 보이는지 확인
- [ ] **(개선점 도출)** AI의 의사결정이 비합리적이거나 특정 상태에 고착되는 경우, 원인을 파악하고 보상 함수(`_calculate_reward`) 또는 상태 벡터(`_get_agent_state`)의 개선 방향을 모색

### 1.3. 장기 안정성 테스트
- [ ] **(설정 변경)** `config.py` 파일에서 `SIMULATION_TICKS`를 1000 이상으로 설정
- [ ] **(실행)** `python run_experiment.py`를 실행하여 장시간 시뮬레이션 구동
- [ ] **(모니터링)** 시뮬레이션 실행 중 오류가 발생하지 않는지, 메모리 사용량이 비정상적으로 증가하지 않는지 확인
- [ ] **(결과 확인)** 장기 실행 결과 데이터에서 특정 지표가 발산하거나, 시스템이 비정상적으로 정체되는 현상이 없는지 분석

---

## **Phase 2: 코드 리팩토링 및 구조 개선**

*   **목표:** 코드의 유지보수성, 확장성, 가독성을 높인다.

### 2.1. `BaseAgent` 추상화
- [x] **(완료)** `simulation/base_agent.py` 파일 생성 및 `BaseAgent` 클래스 구현
- [x] **(완료)** `Household`와 `Firm` 클래스가 `BaseAgent`를 상속받도록 수정
- [ ] **(개선)** 상속 관계를 검증하는 테스트 케이스 보강 (`tests/test_base_agent.py`)

### 2.2. 의사결정 로직 분리
- [ ] **(검토)** `Household` 클래스에 남아있는 의사결정 관련 코드를 식별
- [ ] **(리팩토링)** 식별된 코드를 `simulation/decisions/household_decision_engine.py`로 이동
- [ ] **(검토)** `Firm` 클래스에 남아있는 의사결정 관련 코드를 식별
- [ ] **(리팩토링)** 식별된 코드를 `simulation/decisions/firm_decision_engine.py`로 이동
- [ ] **(테스트)** 기존 의사결정 엔진 테스트(`tests/test_*_decision_engine.py`)를 보강하고 `pytest`로 통과 확인

### 2.3. 시장 API 개선
- [ ] **(검토)** `simulation/markets.py`의 주문 관련 메서드 검토
- [ ] **(리팩토링)** `place_buy_order`, `place_sell_order` 등의 메서드 시그니처를 일관성 있게 개선
- [ ] **(리팩토링)** `HouseholdDecisionEngine`과 `FirmDecisionEngine`이 개선된 시장 API를 사용하도록 수정
- [ ] **(테스트)** `tests/test_markets.py`를 수정된 API에 맞게 업데이트하고 `pytest`로 통과 확인

### 2.4. 최종 통합 검증
- [ ] **(실행)** `pytest`로 모든 테스트가 통과하는지 확인 (회귀 테스트)
- [ ] **(실행)** `python run_experiment.py` 및 `python analyze_results.py`를 다시 실행하여 리팩토링 이후에도 시뮬레이션 전체가 정상 작동하는지 최종 확인

### 2.5. 추가 리팩토링 대상 파일

*   **300줄 초과 파일 (길이로 인한 복잡성)**
    *   `simulation/engine.py`
    *   `simulation/agents.py`
    *   `simulation/decisions/household_decision_engine.py`
    *   `simulation/markets_v2.py`
    *   `simulation/ai_model.py`

*   **핵심 로직/잦은 수정/버그 발생으로 인한 리팩토링 필요 파일 (길이와 무관)**
    *   `main.py`
    *   `utils/logger.py`
    *   `simulation/firms.py`
    *   `simulation/decisions/firm_decision_engine.py`
    *   `analyze_results.py`

### 2.6. 로깅 시스템 최적화

*   **목표:** 과도한 로그 파일 생성 문제를 해결하고, 필요한 정보만 효율적으로 기록하도록 로깅 시스템을 최적화합니다.
*   **세부 계획:**
    *   [ ] 로깅 레벨 및 샘플링 레이트 재검토: `config.py` 또는 `utils/logger.py`에서 각 로그 타입의 중요도에 따라 로깅 레벨(DEBUG, INFO 등) 및 샘플링 레이트를 조정합니다.
    *   [ ] 불필요한 상세 로그 제거: 디버깅 목적으로만 사용되던 과도하게 상세한 로그 메시지를 정리하거나, 필요한 경우에만 활성화되도록 변경합니다.
    *   [ ] 로그 파일 관리 전략 수립: 로그 로테이션(log rotation) 또는 일정 기간/크기 초과 시 자동 삭제와 같은 로그 파일 관리 방안을 고려합니다.
    *   [ ] 로그 저장 방식 효율화: CSV 외에 더 효율적인 로그 저장 방식(예: SQLite, Parquet 등)을 검토합니다.