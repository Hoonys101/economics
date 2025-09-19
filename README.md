# 경제 시뮬레이션 프로젝트

## 프로젝트 개요

본 프로젝트는 인공지능(AI) 에이전트 기반의 경제 시뮬레이션 시스템입니다. 가계와 기업 주체들이 시장(상품 시장, 노동 시장, 대출 시장)에서 상호작용하며 경제 현상을 모의합니다. 시뮬레이션 결과는 웹 기반 대시보드를 통해 실시간으로 시각화되며, 다양한 경제 지표를 추적하고 분석할 수 있습니다.

## 주요 기능

*   **AI 기반 에이전트**: 가계 및 기업 에이전트가 AI 의사결정 엔진을 통해 행동을 결정합니다.
*   **다양한 시장**: 상품 시장, 노동 시장, 대출 시장 등 현실 경제의 주요 시장을 시뮬레이션합니다.
*   **웹 UI 대시보드**: Flask 기반의 웹 인터페이스를 통해 시뮬레이션 상태, 경제 지표, 시장 활동을 실시간으로 모니터링합니다.
*   **데이터 추적 및 분석**: 시뮬레이션 데이터를 기록하고, Python 스크립트를 통해 분석할 수 있습니다.
*   **확장 가능한 아키텍처**: 모듈화된 설계를 통해 향후 기능 확장 및 성능 개선이 용이합니다.

## 시작하기

### 필수 조건

*   Python 3.8 이상 (권장: Python 3.10+)
*   `pip` 패키지 관리자

### 설치

프로젝트 의존성을 설치하려면 다음 명령어를 실행하십시오:

```bash
pip install numpy scikit-learn pandas Flask pytest joblib
```

## 시뮬레이션 실행

### 기본 시뮬레이션 실행

`main.py` 스크립트를 실행하여 기본 시뮬레이션을 시작합니다. 시뮬레이션 결과는 `simulation_results.csv` 파일로 저장됩니다.

```bash
python main.py
```

### 실험 시뮬레이션 실행

`run_experiment.py` 스크립트는 기본 시뮬레이션과 함께 특정 파라미터(예: 식량 생산량)를 조정한 실험 시뮬레이션을 실행합니다. 결과는 `results_baseline.csv`와 `results_experiment.csv`로 저장됩니다.

```bash
python run_experiment.py
```

### 웹 UI 실행

Flask 웹 애플리케이션을 실행하여 웹 대시보드를 통해 시뮬레이션을 제어하고 모니터링할 수 있습니다. 애플리케이션은 기본적으로 `http://127.0.0.1:5001`에서 실행됩니다.

```bash
python app.py
```

## 테스트 실행

프로젝트의 단위 및 통합 테스트를 실행하려면 `pytest`를 사용하십시오. 프로젝트 루트 디렉토리가 Python 경로에 올바르게 설정되어 있는지 확인해야 합니다.

```bash
set PYTHONPATH=%cd% && python -m pytest
```

특정 테스트 파일만 실행하려면:

```bash
set PYTHONPATH=%cd% && python -m pytest tests/test_engine.py
set PYTHONPATH=%cd% && python -m pytest tests/test_order_book_market.py
set PYTHONPATH=%cd% && python -m pytest tests/test_firm_decision_engine_new.py
set PYTHONPATH=%cd% && python -m pytest tests/test_household_decision_engine_new.py
```

## 프로젝트 구조

```
. # 프로젝트 루트
├── app.py              # Flask 웹 애플리케이션
├── config.py           # 시뮬레이션 설정 파일
├── main.py             # 시뮬레이션 메인 실행 스크립트
├── run_experiment.py   # 실험 시뮬레이션 실행 스크립트
├── data/               # 시뮬레이션 초기 데이터 (예: goods.json)
├── logs/               # 시뮬레이션 로그 파일
├── simulation/         # 시뮬레이션 핵심 로직
│   ├── agents/         # 에이전트 정의 (예: Bank)
│   ├── ai/             # AI 모델 관련 로직 (예: ModelWrapper)
│   ├── decisions/      # 의사결정 엔진 (예: HouseholdDecisionEngine)
│   ├── markets/        # 시장 정의 (예: OrderBookMarket)
│   ├── core_agents.py  # 가계, 기업 등 핵심 에이전트 클래스
│   ├── engine.py       # 시뮬레이션 엔진
│   └── models.py       # 데이터 모델 (Order, Transaction)
├── tests/              # 단위 및 통합 테스트
│   └── ...
└── utils/              # 유틸리티 함수 (로깅, 데이터 분석)
```

## 향후 개선 사항

*   **웹소켓 기반 UI 통신**: 실시간 대시보드 효율성 및 반응성 개선.
*   **모듈화된 설정 관리**: `config.py`를 YAML/JSON 파일로 분리하여 유연성 확보.
*   **API 보안 강화**: UI 제어 및 설정 API에 기본 인증 추가.
*   **시뮬레이션 엔진 최적화**: 대규모 시뮬레이션의 성능 향상.
