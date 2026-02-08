# 📋 2026-01-20 Daily Action Plan

**1. 🚦 System Health**
- **Architecture**: 🔴 Critical
- **Top Risks**:
  1. **Entry Point Corruption**: 루트 디렉토리의 `main.py`가 유실되고, 대신 Git Merge 메시지가 담긴 `main` 파일이 존재함. 이로 인해 시뮬레이션 생성 팩토리(`create_simulation`) 접근이 불가능하여 전체 시스템(테스트, 대시보드)이 마비됨.
  2. **God Class Complexity**: `simulation/core_agents.py`가 855라인으로 비대해져 유지보수 위험도가 높음.

**2. 🚨 Critical Alerts (Must Fix)**
- **`main.py` Missing**: `scripts/iron_test.py` 실행 시 `ModuleNotFoundError: No module named 'main'` 발생. 확인 결과 `main.py`는 없고 `main`이라는 이름의 파일에 Merge 충돌 메시지만 남아 있음.
- **Simulation Unrunnable**: 시뮬레이션 엔트리 포인트 소실로 인해 모든 기능 테스트 및 대시보드 연동 불가.

**3. 🚀 Proposed Action Plan (Jules' Proposal)**

#### **Proposal 1: Restore `main.py` & `create_simulation` Factory**
- **Why**: 현재 `main.py` 부재로 인해 `iron_test.py` 및 `dashboard_connector.py` 등 주요 도구가 작동하지 않음. 시스템 정상화를 위해 최우선 복구 필요.
- **Target**: `main.py` (Root Directory)
- **Plan**:
  1. 잘못 생성된 `main` 파일(텍스트) 삭제.
  2. `main.py`를 새로 생성하고, `simulation.initialization.initializer.SimulationInitializer`를 활용하여 표준 `create_simulation()` 함수 구현.
  3. `config` 및 로깅 설정을 포함한 표준 부트스트랩 로직 복원.

#### **Proposal 2: `simulation/core_agents.py` Decomposition (SoC)**
- **Why**: Observer Scan 리포트에서 복잡도 1순위(855 lines)로 지적됨. `Household` 클래스가 너무 많은 책임(생물학적, 경제적, 사회적)을 동시에 수행하고 있음.
- **Target**: `simulation/core_agents.py`
- **Plan**:
  1. `BioComponent`: 나이, 배고픔, 에너지 등 생물학적 상태 관리 분리.
  2. `EconomicComponent`: 자산, 인벤토리, 소비 등 경제 활동 관리 분리.
  3. `Household` 클래스는 각 컴포넌트의 Facade 역할만 수행하도록 구조 변경.

#### **Proposal 3: Fix `iron_test.py` Import Resilience**
- **Why**: 테스트 스크립트가 `main.py`에 강하게 결합되어 있어, 엔트리 포인트 변경 시 쉽게 파손됨.
- **Target**: `scripts/iron_test.py`
- **Plan**:
  1. `main.py` 의존성을 제거하고, `simulation.initialization` 패키지를 직접 사용하여 시뮬레이션을 생성하도록 변경 고려 (혹은 `main.py` 복구 후 경로 의존성 명확화).