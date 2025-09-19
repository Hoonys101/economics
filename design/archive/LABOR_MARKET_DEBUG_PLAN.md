### **TODO: 노동 시장 활성화 및 안정화 계획**

**목표:** 기업의 구인과 가계의 구직이 정상적으로 발생하여, 실업률과 평균 임금 등 주요 경제 지표가 유의미한 값을 갖도록 시뮬레이션을 정상화한다.

**Phase 1: "최소 고용" 로직 검증 및 활성화 (가장 시급)**

*   [ ] **1-1. 디버깅 로그 실행 및 수집**
    *   **작업:** `firm_decision_engine.py`에 디버깅 로그가 추가된 현재 상태에서, `run_experiment.py`를 실행하여 로그를 생성한다. (`SIMULATION_TICKS`는 10으로 설정됨)
    *   **목표:** `make_decisions` 함수가 각 기업에 대해 호출되는지, `len(firm.employees)`의 실제 값이 얼마인지 로그를 통해 확인한다.
    *   **현재 상황 (로그 기록 문제):** `debug_log.log` 파일이 20MB를 초과하여 `read_file` 및 `search_file_content`로 내용 확인 불가. `findstr`로 "Checking minimum employees" 검색 시도했으나 로그가 전혀 발견되지 않음. `InitialEmployment` 로그만 출력됨. 이는 `DEBUG` 레벨 로그가 `debug_log.log`에 기록되지 않고 있음을 의미.

*   [ ] **1-2. 로그 분석 및 1차 원인 진단**
    *   **작업:** 생성된 로그 파일을 분석하여 `if len(firm.employees) < FIRM_MIN_EMPLOYEES:` 조건문이 실패하는 이유를 명확히 밝혀낸다.
    *   **목표:** "기업의 `employees` 리스트가 초기부터 비어있지 않다", "특정 기업의 `make_decisions` 함수가 호출되지 않는다" 등 정확한 원인을 특정한다.
    *   **현재 인지 내용:**
        *   `simulation/engine.py`에서 `firm.employees = []` 라인이 매 틱마다 직원 리스트를 초기화하는 논리적 오류 발견 및 **수정 완료**. (이전 시뮬레이션 실행 시 이 수정이 적용됨)
        *   `utils/logger.py`의 `__setstate__` 메서드 내 `if not self.root_logger.handlers:` 조건문이 `Logger` 인스턴스 unpickle 시 `DEBUG` 레벨 로그를 `debug_log.log`에 기록하는 `FileHandler` 재설정을 방해하는 것으로 진단.
    *   **다음 해야 할 일:**
        *   [ ] **`utils/logger.py`의 `__setstate__` 메서드 수정:** `root_logger`의 기존 핸들러를 모두 제거한 후, `FileHandler`와 `StreamHandler`를 항상 다시 추가하도록 강제.
        *   [ ] **시뮬레이션 재실행:** 수정된 로거로 시뮬레이션을 다시 실행하여 `HiringCheck` 로그가 제대로 기록되는지 확인.
        *   [ ] **로그 분석:** `findstr`을 사용하여 `HiringCheck` 로그를 검색하고, `Current:` 및 `Min:` 값을 분석하여 기업의 고용 결정 로직이 예상대로 작동하는지 최종 확인.

**Phase 2: 노동 시장 선순환 구조 확립**
*   [ ] **2-1. 가계 구직 조건 완화 (필요시)**
    *   **작업:** 1단계 조치 후에도 고용이 원활하지 않을 경우, `config.py`에서 `LABOR_NEED_THRESHOLD` 값을 낮추거나 가계의 초기 `labor_need` 값을 상향 조정한다.
    *   **목표:** 가계가 더 쉽게 구직 활동에 나서도록 하여 노동 공급을 늘린다.

*   [ ] **2-2. 장기 시뮬레이션 및 지표 확인**
    *   **작업:** `SIMULATION_TICKS`를 100 이상으로 설정하고 시뮬레이션을 실행한다.
    *   **목표:** `unemployment_rate`가 100%에서 벗어나고, `avg_wage`가 0 이상으로 유지되는 등 노동 시장이 지속적으로 작동하는지 확인한다.

**Phase 3: 결과 분석 및 장기 과제 전환**
*   [ ] **3-1. 최종 결과 분석**
    *   **작업:** `analyze_results.py`를 실행하여 안정화된 시뮬레이션의 전반적인 경제 지표를 분석하고 문서화한다.
    *   **목표:** 노동 시장 외 다른 부분(상품 시장 등)이 정상적으로 작동하는지 종합적으로 검토한다.

*   [ ] **3-2. 기존 TODO 리스트와 병합**
    *   **작업:** 이 디버깅 계획이 완료되면, 기존의 `TODO_LIST.md`에 명시된 장기 리팩토링 과제를 계속 진행한다.
    *   **목표:** 프로젝트의 원래 개발 로드맵으로 복귀한다.
