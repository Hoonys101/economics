# 시스템 아키텍처 (V2)

**작성일**: 2025-12-29
**분석 대상 코드**: `simulation/engine.py`, `app.py`, `simulation/db/repository.py`

## 1. 개요

본 시뮬레이션은 Python 기반의 **이산 사건 시뮬레이션(Discrete Event Simulation)** 엔진과 Flask 기반의 **웹 대시보드**로 구성됩니다. 에이전트(가계, 기업, 정부)는 AI 모델(Q-Learning)을 통해 의사결정을 내리며, 모든 데이터는 SQLite 데이터베이스에 기록됩니다.

## 2. 핵심 컴포넌트

### 2.1. Simulation Engine (`simulation/engine.py`)
- **역할**: 시뮬레이션의 시간(`tick`)을 진행시키고 에이전트와 시장의 상호작용을 조율합니다.
- **주요 루프**:
    1. `run_tick()` 시작
    2. 시장 초기화 (`clear_orders`)
    3. 에이전트 의사결정 (`make_decision`) -> 주문 생성
    4. 시장 매칭 (`match_orders`) -> 거래 생성
    5. 거래 처리 및 상태 업데이트 (`process_transactions`)
    6. 소비 및 생산 활동 (`consume`, `produce`)
    7. 지표 추적 및 DB 저장 (`tracker.track`, `_save_state_to_db`)
    8. 소비 카운터 리셋

### 2.2. Agents
- **Household**: 소비, 노동 공급, 투자 주체. `HouseholdAI`를 통해 적극성 벡터를 결정합니다.
- **Firm**: 생산, 고용, 판매 주체. `FirmAI`를 통해 가격, 임금, 배당 등을 결정합니다.
- **Government**: 세금 징수 및 재분배(UBI, 보조금) 담당.
- **Bank**: 대출 및 예금 관리 (초기 단계).

### 2.3. AI Engine (`simulation/ai/`)
- **구조**: Multi-Channel Aggressiveness Vector 방식.
- **학습**: Q-Table 기반 강화학습. `AITrainingManager`를 통해 주기적으로 우수 에이전트의 전략을 복제/변이(Evolutionary Learning)합니다.

### 2.4. Data Persistence (`simulation/db/`)
- **SQLite**: 시뮬레이션의 모든 상태(거래, 에이전트 상태, 지표)를 저장합니다.
- **Repository Pattern**: `SimulationRepository`를 통해 DB 접근을 추상화했습니다.
- **Batch Processing**: 성능을 위해 `BATCH_SAVE_INTERVAL`마다 일괄 저장합니다.

## 3. 웹 인터페이스 (`app.py`, `static/`)
- **Backend**: Flask API (`/api/simulation/tick`, `/api/simulation/update`).
- **Frontend**: Vanilla JS + Chart.js.
- **통신**: `API.js`를 통해 백엔드와 통신하며, `ui.js`가 대시보드를 렌더링합니다.
