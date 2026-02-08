# 📋 2026-01-17 Daily Action Plan

**1. 🚦 System Health**
- **Architecture**: **Degrading** (God Classes detected, Maintenance High Risk)
- **Top Risks**:
    1. **Context Vacuum**: `PROJECT_STATUS.md` 유실로 인한 프로젝트 진행 상황 추적 불가.
    2. **Monolithic Complexity**: `simulation/core_agents.py` (1078 lines) 및 `simulation/engine.py` (1042 lines)의 비대화로 인한 수정 영향도 예측 어려움.

**2. 🚨 Critical Alerts (Must Fix)**
- **Missing Documentation**: Root 경로에 필수 파일인 `PROJECT_STATUS.md`가 존재하지 않습니다.
- **Scanner Noise**: `scan_codebase.py`가 문서 파일(`.md`) 내의 `WO-XXX` 같은 텍스트를 Tech Debt로 오탐지하고 있어 분석 효율을 저하시킵니다.

**3. 🚀 Proposed Action Plan (Jules' Proposal)**

#### **Proposal 1: Restore Project Status Tracking**
- **Why**: 프로젝트의 현재 상태, 진행 중인 작업(Work Orders), 알려진 버그를 추적하는 기준점이 사라져 협업 효율이 저하됨.
- **Target**: `PROJECT_STATUS.md` (New File)
- **Plan**:
    1. 루트 디렉토리에 `PROJECT_STATUS.md` 생성.
    2. [Active Tasks], [Backlog], [Known Issues] 섹션 구성.
    3. 현재 확인된 God Class 리팩토링 건을 Backlog에 등록.

#### **Proposal 2: Decompose `core_agents.py` (SoC Refactoring)**
- **Why**: `core_agents.py`가 1000줄을 초과하며 `Household`와 `Firm` 로직이 혼재되거나 비대해짐. 유지보수성 악화.
- **Target**: `simulation/core_agents.py`
- **Plan**:
    1. `Household` 클래스의 경제/생물학/사회 로직을 분리.
    2. `HouseholdEconomy`, `HouseholdBiology` 컴포넌트로 추출하는 리팩토링 계획 수립 (기존 Refactoring Proposal 참조).

#### **Proposal 3: Optimize Observer Scanner**
- **Why**: 문서 파일(`.md`)에 포함된 예시용 태그(WO-XXX, FIXME in docs)가 Tech Debt로 집계되어 리포트의 신뢰도를 떨어뜨림.
- **Target**: `scripts/observer/scan_codebase.py`
- **Plan**:
    1. 스캔 대상 파일 확장자 필터링 강화 (Code file만 스캔).
    2. 또는 `design/` 디렉토리를 태그 검색 대상에서 제외.