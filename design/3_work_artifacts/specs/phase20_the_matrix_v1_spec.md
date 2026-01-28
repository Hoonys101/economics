# Phase 20: The Matrix v1 - Cognitive & Environmental Evolution

## 1. 개요 (Overview)
Phase 20은 에이션트의 의사결정 지능을 **이중 프로세스 이론(Dual-Process Theory)** 기반으로 혁신하고, 인구 역학을 가속화시키는 **물리적(부동산)/제도적(성별/기술) 환경**을 구축하는 단계입니다. 이를 통해 단순한 반응형 에이전트에서 '계획하는 주체'로의 진화를 목표로 합니다.

## 2. 기술 명세 (Technical Specification)

### 2.1 The Matrix: System 1 & System 2
*   **System 1 (Fast/RL)**: 기존의 Q-Learning 기반 엔진. 틱 단위의 즉각적인 노동/소비 대응.
*   **System 2 (Slow/Planner)**: **Internal World Model** 도입.
    *   **Calculation Cycle (`SYSTEM2_TICKS_PER_CALC`)**: 10 틱마다 1회 실행(연산 비용 최적화).
    *   **Forward Projection**: 현재 자산, 기대 임금, 시장 가격(이동 평균)을 기반으로 미래 `SYSTEM2_HORIZON`(100틱) 시뮬레이션.
    *   **NPV (Net Present Value)**: `SYSTEM2_DISCOUNT_RATE`(0.98/tick) 적용. 미래 100틱 시점의 예상 자산 및 생존 유무를 현재 가치로 환산.
    *   **Constraint Injection**: 
        - 미래 생존율 < 50% 일 경우: "Survival Mode" 강제 주입 → System 1의 사치품 소비 Aggressiveness 강제 0.
        - 미래 자산 > 10,000 일 경우: "Investment Mode" 강제 주입 → 주식/부동산 투자 Aggressiveness 하한선 설정.

### 2.2 Social Missing Links (Socio-Tech Dynamics)
*   **수유 의존성 (Lactation Dependency)**:
    *   `gender` 속성 도입 (M/F).
    *   신생아(0-10틱)는 `Lactation_Factor`가 높을 때 어머니(F) 에이전트의 시간만을 강제로 소비.
    *   `Formula_Tech` (분유 기술) 해금 시 `Lactation_Factor` → 0으로 감쇄.
*   **교육 ROI (Return on Investment)**:
    *   시장 접근성 필터 도입. 초기에는 F 에이전트의 고임금 직종 접근 차단 → 합리적 교육 투자 기피 유도.
*   **가정 환경 점수 (Home Environment Score)**:
    *   가사 노동 시간이 부족할 경우 `Health` 및 `Social_Status`에 페널티 부여.
    *   맞벌이 시 이 점수를 유지하기 위해 '가전제품(Durable)'이나 '가사 서비스' 소비 강제.

### 2.3 Real Estate Market Expansion (Option A Integration)
*   **Immigration/Supply Logic**: 인구 변화에 따른 주택 공급 탄력성 조절.
*   **Legacy Assets**: 상속된 주택이 가계의 'Reservation Standard'를 높여, 무주택 가계와의 격차 및 출산 기피 심화.

## 3. 데이터 구조 변경

### Household (simulation/core_agents.py)
*   `gender`: "M" | "F"
*   `home_quality_score`: float
*   `system2_planner`: Internal Model Reference

### Config (config.py)
*   `FORMULA_TECH_LEVEL`: 0.0 ~ 1.0
*   `HOMEWORK_QUALITY_COEFF`: float
*   `SYSTEM2_HORIZON`: 100 (Ticks)

## 4. 검증 계획
*   **시나리오 실험**: "분유 보급 전/후 여성 노동 참여도 및 교육 수준 변화" 관찰.
*   **주거비 압박 테스트**: 집값 상승 시 System 2가 출산을 '비합리적 투자'로 판단하여 출산율이 급락하는지 확인.
