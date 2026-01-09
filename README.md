# Project Apex: Economic Simulation Engine

## 🌍 프로젝트 개요
**Project Apex**는 고도로 정교한 **AI 에이전트 기반 거시경제 시뮬레이터**입니다.
단순한 수식 기반 모델링을 넘어, 각 경제 주체(가계, 기업, 정부, 은행)가 **AI 의사결정 엔진**과 **복잡계 알고리즘**을 통해 상호작용하며 창발적(Emergent)인 경제 현상을 만들어냅니다.

## 🚀 현재 상태: Phase 17.5 (The Leviathan)
시뮬레이션은 산업과 금융을 넘어 **사회적 허영(Vanity)**과 **정치적 선택(Politics)**의 단계로 진입했습니다.

### ✅ 최근 완료된 마일스톤 (Phase 17+)
1.  **시장 다양성 (Market Diversity)**: 부동산(임대/매매/모기지), 원자재, 서비스 시장 통합.
2.  **허영의 사회 (The Society of Vanity)**: `Social Rank`와 `Veblen Effect` 도입. 사회적 경쟁 심리 모델링.
3.  **정치 시스템 (The Leviathan)**: 지지율 기반 `Government AI` 및 정당 교체/선거 시스템 탑재.
4.  **자본 시장 (Capital Market)**: 주식 거래 알고리즘 및 배당/소각 로직 안정화.

### 🔜 향후 로드맵: Phase 19 (Population Dynamics)
-   **진화적 인구 역학**: 기대소득 불일치와 시간 빈곤에 따른 저출산 시뮬레이션 (WO-033).
-   **에이전트 이원론 (Dual-Process Theory)**: 단기 RL과 장기 계획 시스템의 분리.

---

## 🛠️ 기술 스택 및 아키텍처
*   **Core**: Python 3.10+ (Type Hinting, OOP)
*   **AI Engine**: Reinforcement Learning (Q-Learning) 기반 적응형 에이전트.
*   **Architecture**: SDD (Spec-Driven Development) 지향.

### 핵심 모듈
-   `simulation/core_agents.py`: 가계(Household)의 소비, 노동, 투자 로직.
-   `simulation/agents/government.py`: 재정 정책을 학습하는 지능형 정부.
-   `simulation/ai/government_ai.py`: 정치적 생존을 위한 강화학습 에이전트.
-   `simulation/engine.py`: 틱(Tick) 단위 시간 진행 및 인구/정치적 이벤트 조율.

---

## 📂 프로젝트 아키텍처 및 역사 (Documentation)
상세 설계 및 전체 히스토리는 `design/` 디렉토리에 집대성되어 있습니다.
-   [📜 프로젝트 역사 (PROJ_HISTORY)](design/PROJ_HISTORY.md): 탄생부터 현재까지의 기술적 이정표.
-   [🏺 유기 자산 인벤토리 (HERITAGE_ASSETS)](design/HERITAGE_ASSETS.md): 대시보드 v1, 분석 스크립트 등 레거시 자산 가이드.
-   [📍 현재 현황 브리핑 (CURRENT_BRIEFING)](design/CURRENT_BRIEFING.md): **가장 먼저 읽어야 할 현재 작업 상황.**

---

## 🚦 시작하기

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. 시뮬레이션 실행
```bash
python main.py
```

### 3. 검증 (Verification)
```bash
# 최신 정치 시스템 검증
python tests/verify_leviathan.py

# 부동산 및 모기지 시스템 검증
python tests/verify_real_estate_sales.py
```

---
*Last Updated: 2026-01-09 (Phase 17.5 Integration Completed)*
