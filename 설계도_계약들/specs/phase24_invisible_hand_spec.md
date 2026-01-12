# [SPEC] WO-056: The Invisible Hand (Market Auto-Balancer)

## 1. 개요
*   **목적**: 하드코딩된 경제 가드레일을 제거하고, 가격/임금/금리가 시장 신호(수요와 공급)에 따라 자율적으로 균형을 찾도록 고도화.
*   **배경**: WO-055를 통해 엔진의 물리적 정합성(통화량 보존)이 확보됨에 따라, 이제 동적 밸런싱을 시장 기능에 위임할 수 있는 토대 마련.

## 2. 설계 핵심 메커니즘

### 2.1. 가격 발견 (Price Discovery 2.0)
*   **메커니즘**: 초과 수요(Excess Demand) 기반 가격 조정 및 평활화(Smoothing).
*   **로직**:
    *   `Candidate_Price = Price_t * (1 + Sensitivity * (Demand - Supply) / Supply)`
    *   **Smoothing 적용**: `Price_t+1 = (Candidate_Price * 0.2) + (Price_t * 0.8)`
    *   *Rationale*: 거미줄 현상(Cobweb Theorem) 방지 및 경제 주체의 적응 시간 확보.

### 2.2. 임금 자율 결정 (Self-Correcting Labor Market)
*   **메커니즘**: 예약 임금(Reservation Wage)의 비대칭적 유연화 (Sticky Wage).
*   **로직**:
    *   **Wage Increase**: 취업 시 또는 시장 임금 상승 시 빠르게 상향 (`Wage_Increase_Rate`).
    *   **Wage Decay**: 실업 시 보수적으로 하향 (`Wage_Decay_Rate`).
    *   **Constraint**: `Wage_Increase_Rate > Wage_Decay_Rate` (하방 경직성 구현).
*   **Economic Barrier**: `Pop / 15` 하드 캡 제거 대신, **창업 비용 연동** 도입.
    *   `Startup_Cost = Avg_Wage_last_30_ticks * 6`
    *   *Rationale*: 임금 상승이 창업 장벽으로 작용하여 노동력 과분산을 자연스럽게 억제.

### 2.3. 금리 정책 자동화 (Adaptive Taylor Rule)
*   **메커니즘**: 실질 성장률과 연동된 테일러 준칙.
*   **로직**:
    *   `Neutral_Rate = Real_GDP_Growth_Rate` (실질 경제 성장률)
    *   `Target_Rate = Neutral_Rate + Inflation + 0.5 * (Inflation - Target_Inf) + 0.5 * (GDP_Gap)`
    *   *Rationale*: 성장이 멈춘 상태에서의 고금리로 인한 경제 질식 방지.

## 3. 구현 단계 (Proposed Stages)
1.  **Stage 1**: `config.py`의 하드 캡(`LABOR_GUARD`) 비활성화 및 시장 신호 모니터링 로깅 강화.
2.  **Stage 2**: 가계의 예약 임금 동적 조정 로직 구현 (`simulation/core_agents.py`).
3.  **Stage 3**: 기업의 초과 수요 기반 가격 책정 엔진 고도화 (`simulation/firms.py`).
4.  **Stage 4**: 스트레스 테스트 및 Golden Sample 생성.

## 4. 검증 계획
*   **Scenario 1: Productivity Shock**: 기술 혁신(P23)으로 인한 가격 하락과 실질 임금 상승이 자동으로 일어나는지 확인.
*   **Scenario 2: Labor Scarcity**: 고의적으로 노동력을 줄이었을 때, 임금이 상승하고 저효율 기업이 파산하는 '창조적 파괴' 확인.
