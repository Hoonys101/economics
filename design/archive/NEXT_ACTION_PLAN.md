# 향후 행동 계획 및 프레임워크 활용 가이드

이 문서는 현재 프로젝트 상태 분석을 기반으로 향후 진행할 핵심 과제를 정의하고, Gemini CLI의 도구와 SuperGemini 프레임워크를 효과적으로 활용하여 각 과제를 해결하는 구체적인 실행 계획을 제시합니다.

---

## 1. 현황 분석 (Current Status Analysis)

- **프로젝트 목표**: AI 에이전트(가계, 기업) 기반의 복잡계 경제 시뮬레이션 구축.
- **현재 상태**:
    - AI 의사결정 엔진이 가계 에이전트에 통합되었으나, 실제 의사결정 로직(`HouseholdDecisionEngine`)에는 아직 연결되지 않음.
    - 시뮬레이션은 실행 가능하지만, 기업이 직원을 유지하지 못해 생산량이 0이 되는 심각한 버그 존재.
    - `ImportError` 등 구조적인 문제가 최근 해결되었음.
- **주요 과제**: 핵심 경제 순환 로직(고용-생산-소비)을 안정화하고, AI 의사결정 모델을 실제 시뮬레이션에 완전히 통합하여 그 효과를 검증하는 것.

---

## 2. 향후 핵심 과제 (Key Future Tasks)

1.  **[P0] 기업 생산량 0 버그 수정**: 시뮬레이션의 기본 경제 순환을 복구.
2.  **[P1] AI 의사결정 엔진 통합**: `HouseholdDecisionEngine`이 AI 엔진을 사용하도록 로직 수정.
3.  **[P2] 수요-공급 법칙 검증**: 모델의 경제적 타당성 확인.
4.  **[P3] UI 개선 및 테스트 코드 작성**: 사용성 및 안정성 확보.

---

## 3. 세부 실행 계획 및 도구 활용법 (Detailed Action Plan & Tool Usage)

각 과제를 해결하기 위한 단계별 실행 계획과 도구 활용법은 다음과 같습니다.

### 과제 1: [P0] 기업 생산량 0 버그 수정

- **목표**: 기업이 직원을 유지하고 정상적으로 생산 활동을 하도록 `simulation/engine.py` 수정.

1.  **문제 코드 분석**:
    - **방법**: `search_file_content`를 사용해 `engine.py` 내에서 'employment', 'reset', 'fire' 등의 키워드로 직원 상태가 변경되는 부분을 찾습니다.
    - **명령어 예시**:
      ```
      search_file_content(pattern="employment", include="simulation/engine.py")
      ```

2.  **파일 읽기 및 컨텍스트 파악**:
    - **방법**: `read_file`로 `simulation/engine.py` 전체를 읽어 문제의 원인이 되는 로직(매 틱마다 고용 상태를 초기화하는 부분)을 정확히 파악합니다.
    - **명령어 예시**:
      ```
      read_file(absolute_path="C:\\coding\\economics\\simulation\\engine.py")
      ```

3.  **코드 수정**:
    - **방법**: `replace` 도구를 사용하여 문제의 로직을 수정하거나 주석 처리합니다. `old_string`은 정확한 컨텍스트를 포함해야 합니다.
    - **명령어 예시**:
      ```
      replace(
          file_path="C:\\coding\\economics\\simulation\\engine.py",
          old_string="""# 문제가 되는 코드 블록 (3줄 이상)""",
          new_string="""# 수정된 코드 블록"""
      )
      ```
    - **팁**: `replace` 실패 시, `desktop-commander.edit_block`을 사용하거나 `read_file` -> 내용 수정 -> `write_file`의 수동 패턴을 따릅니다.

4.  **검증**:
    - **방법**: `run_shell_command`로 시뮬레이션을 실행하고, `results_experiment.csv` 파일에서 기업 생산량이 0이 아닌지 확인합니다.
    - **명령어 예시**:
      ```
      run_shell_command(command="python main.py")
      read_file(absolute_path="C:\\coding\\economics\\results_experiment.csv", offset=-10) # 마지막 10줄 확인
      ```

### 과제 2: [P1] AI 의사결정 엔진 통합

- **목표**: `HouseholdDecisionEngine`이 AI 모델의 결정을 사용하도록 `simulation/decisions/household_decision_engine.py` 수정.

1.  **관련 파일 분석**:
    - **방법**: `read_many_files`를 사용하여 AI 엔진, 가계 의사결정 엔진, 핵심 에이전트 파일을 한 번에 읽어 전체 구조를 파악합니다.
    - **명령어 예시**:
      ```
      read_many_files(paths=[
          "C:\\coding\\economics\\simulation\\decisions\\household_decision_engine.py",
          "C:\\coding\\economics\\simulation\\decisions\\ai_decision_engine.py",
          "C:\\coding\\economics\\simulation\\core_agents.py"
      ])
      ```

2.  **임시 코드 변경 및 테스트**:
    - **방법**: `GEMINI.md`에 정의된 `GEMINI_TEMP_CHANGE` 주석 블록을 사용하여 기존 룰 기반 로직을 보존하면서 AI 엔진을 호출하는 코드를 임시로 추가합니다.
    - **팁**: `write_file`을 사용하여 이 변경사항을 적용합니다.

3.  **로그 기반 디버깅**:
    - **방법**: `run_shell_command`로 시뮬레이션을 실행한 후, `read_file`로 `logs/debug_custom.log`를 확인하여 `predicted_reward`와 같은 AI 관련 로그가 정상적으로 기록되는지 확인합니다.
    - **명령어 예시**:
      ```
      run_shell_command(command="python main.py")
      read_file(absolute_path="C:\\coding\\economics\\logs\\debug_custom.log", limit=500)
      ```

### 과제 3: [P2] 수요-공급 법칙 검증

- **목표**: 'food' 공급량을 늘렸을 때 가격이 하락하는지 실험하고 검증.

1.  **실험 코드 작성**:
    - **방법**: `run_experiment.py`와 같은 실험용 스크립트를 `write_file`로 생성하거나 수정하여 특정 기업의 'food' 생산량을 강제로 늘리는 로직을 추가합니다.

2.  **실험 실행 및 결과 분석**:
    - **방법**: `run_shell_command`로 실험 스크립트를 실행하고, 생성된 `experiment_timeseries.csv` 파일을 `pandas`를 이용해 분석합니다.
    - **명령어 예시 (터미널 내 Python 사용)**:
      ```
      run_shell_command(command="python -c \"import pandas as pd; df = pd.read_csv('experiment_timeseries.csv'); print(df[['tick', 'market_price_food']].tail())\"" )
      ```

---

## 4. SuperGemini 프레임워크 활용 (/sg:)

- **목표**: 반복적인 작업을 자동화하고 개발 속도를 향상.

- **코드 분석 (`/sg:analyze`)**:
    - **설명**: 특정 디렉토리나 파일의 구조, 의존성, 복잡도를 분석하여 보고서를 생성합니다. 복잡한 레거시 코드를 이해할 때 유용합니다.
    - **사용 예시**: `AI 모듈 고도화` 전, `/sg:analyze simulation/decisions/` 명령으로 의사결정 관련 모듈들의 관계를 파악할 수 있습니다.

- **기능 구현 (`/sg:implement`)**:
    - **설명**: 자연어 요구사항(예: "user authentication")을 바탕으로 필요한 파일 생성, 코드 작성, 테스트 추가까지 제안합니다.
    - **사용 예시**: `/sg:implement government agent with tax policy` 와 같이 새로운 에이전트 구현을 지시할 수 있습니다.

- **테스트 생성 (`/sg:test`)**:
    - **설명**: 특정 파일의 함수나 클래스에 대한 `pytest` 테스트 케이스를 자동으로 생성합니다.
    - **사용 예시**: `/sg:test simulation/core_markets.py` 명령으로 시장 모듈의 테스트 커버리지를 높일 수 있습니다.

---

## 5. 협업 및 보고 (Collaboration & Reporting)

- **질문 및 요청**: `GEMINI.md`에 따라, PL에게 질문이나 코드 리뷰를 요청할 때는 `communications/requests/` 디렉토리에 `[To_PL_From_Gemini]_<topic>.md` 형식의 파일을 생성합니다.
- **도구**: `write_file`을 사용하여 요청 문서를 작성합니다.

```
