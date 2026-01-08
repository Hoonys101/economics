# Project Apex: Economic Simulation Engine

## 🌍 프로젝트 개요
**Project Apex**는 고도로 정교한 **AI 에이전트 기반 거시경제 시뮬레이터**입니다.
단순한 수식 기반 모델링을 넘어, 각 경제 주체(가계, 기업, 정부, 은행)가 **AI 의사결정 엔진**과 **복잡계 알고리즘**을 통해 상호작용하며 창발적(Emergent)인 경제 현상을 만들어냅니다.

## 🚀 현재 상태: Phase 14 (The Industrial Revolution)
현재 시뮬레이션은 농업 중심의 단순 경제를 넘어 **산업화, 금융 고도화, 혁신**의 단계로 진입했습니다.

### ✅ 최근 달성된 마일스톤 (Phase 14)
1.  **산업의 분화 (Innovation)**: 식량(Survival)에서 소비재(Quality)로 산업이 확장되었습니다. (Maslow Hierarchy 적용)
2.  **인적 자본 (Human Capital)**: "모든 노동은 같다"는 전제를 폐기하고, **Talent(재능) + Education(노력) = Skill(숙련도)** 공식을 도입했습니다. 고숙련 노동자는 더 높은 생산성과 임금을 가집니다.
3.  **금융 시스템 (Banking)**: 부분지급준비제도(Fractional Reserve Banking)가 도입되었습니다. 기업은 대출을 통해 레버리지 투자를 하고, 가계는 예금을 통해 이자 소득을 얻습니다. (구현 완료, 검증 단계)
4.  **주주 자본주의 (Shareholder Logic)**: 기업의 이익은 배당을 통해 주주(가계)에게 환원되며, 자본 소득과 노동 소득의 분배를 추적합니다.

### 🔜 향후 로드맵: Phase 15 (Materiality)
-   **내구재(Durables) 도입**: 소비재가 즉시 소멸하지 않고 자산화되어 감가상각됩니다.
-   **경기 변동(Business Cycle)**: 내구재 교체 주기에 따른 호황과 불황의 파동을 시뮬레이션합니다.

---

## 🛠️ 기술 스택 및 아키텍처
*   **Core**: Python 3.10+ (Type Hinting, OOP)
*   **Performance**: Agent-based Modeling optimized for data locality.
*   **Frontend**: React + TypeScript (Real-time Dashboard)
*   **Visualization**: Recharts, D3.js

### 핵심 모듈
-   `simulation/core_agents.py`: 가계(Household)의 소비, 노동, 투자 로직. (Human Capital 적용됨)
-   `simulation/firms.py`: 기업(Firm)의 생산, 고용, 재무 로직. (Cobb-Douglas 생산함수)
-   `simulation/agents/bank.py`: 상업은행의 여수신 및 신용창조 로직.
-   `simulation/engine.py`: 틱(Tick) 단위 시간 진행 및 에이전트 생명주기 관리.

---

## 🚦 시작하기

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. 시뮬레이션 실행
기본 시나리오 실행 (데이터 생성):
```bash
python main.py
```

### 3. 검증 스크립트 실행
특정 경제 메커니즘 검증:
```bash
# 은행 시스템 검증
python scripts/verify_banking.py

# 혁신 및 산업 구조 변화 검증
python scripts/verify_wo23.py
```

### 4. 대시보드 실행
```bash
python app.py
# 접속: http://127.0.0.1:5001
```

---

## 📂 문서 (Documentation)
상세 설계 및 작업 지시서는 `design/` 디렉토리에 있습니다.
-   `design/JULES_MASTER_DIRECTIVE.md`: 현재 개발팀(Jules)을 위한 통합 지침서.
-   `design/work_orders/`: 각 Phase별 상세 작업 명세서.
    -   `WO-023`: Innovation Strategy
    -   `WO-024`: Banking System
    -   `WO-025`: Materiality (Durables)

---
*Last Updated: 2026-01-08 (Phase 14-3 Verification)*
