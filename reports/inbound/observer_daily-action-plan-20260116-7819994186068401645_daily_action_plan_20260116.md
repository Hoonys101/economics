# 📋 2026-01-16 Daily Action Plan

**1. 🚦 System Health**
- **Architecture**: 🔴 Critical
- **Top Risks**:
  1. **Startup Failure**: 시뮬레이션 초기화 단계에서 `Household` 객체 생성 중 충돌 발생으로 실행 불가.
  2. **Environment Instability**: 주요 라이브러리(`numpy`, `pandas` 등) 누락으로 인한 테스트 스크립트 실행 실패.

**2. 🚨 Critical Alerts (Must Fix)**
- **Bug**: `AttributeError: property 'generation' of 'Household' object has no setter`
  - `BaseAgent.__init__`에서 `self.generation = 0`을 초기화하려 시도하나, `Household` 클래스에서 이를 `@property`로 오버라이드하고 setter를 구현하지 않아 충돌 발생.
- **Dependency**: `scripts/iron_test.py` 실행 시 `numpy`, `python-dotenv`, `PyYAML` 모듈 로드 실패.

**3. 🚀 Proposed Action Plan (Jules' Proposal)**
*Jules가 제안하는 금일 작업 목록입니다.*

#### **Proposal 1: Fix Household Generation Attribute Conflict**
- **Why**: 현재 시뮬레이션 엔진이 전혀 구동되지 않음. `BaseAgent`와 `Household` 간의 속성 정의 충돌 해결 필요.
- **Target**: `simulation/base_agent.py` 또는 `simulation/core_agents.py`
- **Plan**:
  - `Household` 클래스의 `generation` 프로퍼티에 setter를 추가하여 `self.demographics.generation`을 업데이트하도록 수정.
  - 또는 `BaseAgent`에서 `generation` 초기화를 제거하고 하위 클래스에 위임.
  - (권장) `Household` 클래스에 setter 추가.

#### **Proposal 2: Environment Stabilization**
- **Why**: 로컬/CI 환경에서 테스트 스크립트(`iron_test.py`)가 일관되게 실행되어야 함.
- **Target**: `requirements.txt`
- **Plan**:
  - 누락된 의존성(`numpy`, `pandas`, `scikit-learn`, `python-dotenv`, `PyYAML`)이 `requirements.txt`에 명시되어 있는지 확인하고, 설치 상태 동기화.

#### **Proposal 3: Restore PROJECT_STATUS.md**
- **Why**: 현재 프로젝트의 진행 상황과 Known Issues(WO-056 Money Leak 등)를 추적할 문서가 소실됨.
- **Target**: Root Directory
- **Plan**:
  - `PROJECT_STATUS.md` 파일을 재생성하고 현재 파악된 Critical Issue(WO-056, WO-058) 및 금일 발견된 Startup Crash를 기록.

#### **Proposal 4: Initiate God Class Refactoring (Household)**
- **Why**: `simulation/core_agents.py`가 1079줄에 달하며, 이번 `generation` 버그처럼 컴포넌트(Demographics)와 BaseAgent 간의 결합도가 높아 유지보수가 어려움.
- **Target**: `simulation/core_agents.py` -> `simulation/agents/household/` (Directory Split)
- **Plan**:
  - `Household` 클래스를 `HouseholdEconomy`, `HouseholdBiology` 등으로 분리하는 Refactoring Plan(WO-SoC) 수립 권고.