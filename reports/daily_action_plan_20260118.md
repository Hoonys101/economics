# 📋 2026-01-18 Daily Action Plan

**1. 🚦 System Health**
- **Architecture**: 🔴 Critical
- **Top Risks**:
  1. **Environment Failure**: `scripts/iron_test.py` 실행 불가로 인한 시뮬레이션 검증 중단.
  2. **High Coupling**: `core_agents.py`와 `engine.py`의 과도한 복잡도로 인한 유지보수성 저하.

**2. 🚨 Critical Alerts (Must Fix)**
- **Runtime Error**: `ModuleNotFoundError: No module named 'dotenv'` 발생. (`config.py` import 시점)
- **God Classes**:
  - `simulation/core_agents.py`: 1040 lines (유지보수 한계 초과)
  - `simulation/engine.py`: 885 lines (단일 책임 원칙 위배)

**3. 🚀 Proposed Action Plan (Jules' Proposal)**

#### **Proposal 1: Restore Environment Dependencies**
- **Why**: 현재 `python-dotenv` 등 필수 패키지 누락으로 시뮬레이션 및 테스트 실행이 불가능합니다.
- **Target**: Sandbox Environment
- **Plan**:
  - `requirements.txt` 확인 (이미 포함되어 있음).
  - `pip install -r requirements.txt` 실행하여 환경 재구축.
  - `scripts/iron_test.py` 재실행하여 정상 작동 검증.

#### **Proposal 2: Refactor `core_agents.py` (Separation of Concerns)**
- **Why**: `Household`와 `Firm` 클래스가 단일 파일에 혼재되어 코드 복잡도가 매우 높습니다(1040 lines).
- **Target**: `simulation/core_agents.py`
- **Plan**:
  - `simulation/agents/` 디렉토리 생성.
  - `Household` 클래스를 `simulation/agents/household.py`로 분리.
  - `Firm` 클래스를 `simulation/agents/firm.py`로 분리.
  - 기존 `core_agents.py`는 하위 호환성을 위해 import wrapper로 유지하거나 제거.

#### **Proposal 3: Decompose `Simulation` Engine**
- **Why**: `engine.py`가 시뮬레이션 루프, 데이터 수집, 시장 로직을 모두 포함하고 있어 테스트와 확장이 어렵습니다.
- **Target**: `simulation/engine.py`
- **Plan**:
  - **Runner**: 실행 루프(`run_simulation`) 분리.
  - **World**: 에이전트 및 객체 관리(`registry`) 분리.
  - **DataCollector**: 통계 및 로그 처리 분리.
