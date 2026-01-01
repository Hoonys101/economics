# W-1 Spec: Phase 9 - M&A & Bankruptcy (The Corporate Food Chain)

## 1. 개요 (Overview)
*   **목표**: 경제 생태계의 신진대사(Metabolism) 구현. 부실 기업은 도태(Bankruptcy/Acquisition)되고, 우량 기업은 자산과 시장 지배력을 흡수하여 성장하는 "적자생존" 메커니즘 도입.
*   **핵심 기능**:
    1.  **기업 가치 평가 (Valuation)**: 기업의 적정 인수가격 산정.
    2.  **M&A 거래 (Acquisition)**: 현금 보유고가 풍부한 기업이 부실 기업을 인수.
    3.  **파산 처리 (Liquidation)**: 인수되지 못한 부실 기업의 자산 매각 및 퇴출.

## 2. 상세 설계 (Detailed Design)

### 2.1. 데이터 및 인터페이스 (Data & Interface)

#### 2.1.1. Config 추가 (`config.py`)
```python
# Phase 9: M&A Parameters
MA_ENABLED = True
VALUATION_PER_MULTIPLIER = 10.0   # 주가수익비율(PER) 유사 계수 (이익 * 10)
MIN_ACQUISITION_CASH_RATIO = 1.5  # 인수가 대비 1.5배 현금 보유 시에만 시도
BANKRUPTCY_CONSECUTIVE_LOSS_TICKS = 20 # 20틱 연속 적자 시 파산 위험
LIQUIDATION_DISCOUNT_RATE = 0.5   # 청산 시 자산 가치 50% 할인 매각
```

#### 2.1.2. Firm 메서드 확장 (`simulation/firms.py`)
*   `calculate_valuation(self) -> float`: 기업 가치 계산.
    *   Formula: `Net Assets + (Max(0, Avg_Profit_Last_10_Ticks) * VALUATION_PER_MULTIPLIER)`
*   `receive_acquisition_offer(self, offer_price: float) -> bool`: 인수 제안 수락 여부 결정.
    *   Logic: 제안 가격 > (자체 평가 가치 * 1.1) 이면 수락 (10% 프리미엄).

### 2.2. 로직 및 알고리즘 (Logic & Algorithm)

#### 2.2.1. M&A Manager (`simulation/systems/ma_manager.py`)
*   시뮬레이션 루프(`engine.py`)에서 주기적(예: 매 10틱)으로 실행.
*   **Prey Identification (피인수 대상 식별)**:
    *   현금 부족 (< 월급 지급 가능액의 2배) OR 연속 적자 기록 중.
    *   Valuation이 낮음.
*   **Predator Identification (인수 주체 식별)**:
    *   현금 풍부 (> 전체 기업 평균의 2배).
    *   이익 잉여 상태.
    *   **동일 업종(Horizontal M&A)** 우선. (기술 흡수 및 시장 점유율 확대 목적)
*   **Transaction**:
    1.  `Predator`가 `Prey`에게 `Valuation` 기반 오퍼 전송.
    2.  `Prey` 수락 시:
        *   `Predator.cash -= Offer Price`.
        *   `Prey`의 주주(Households)에게 현금 분배.
        *   `Prey`의 **자산(Inventory, Capital)**을 `Predator`로 이동.
        *   `Prey`의 **직원(Employees)**은 `Predator`로 고용 승계되거나 해고(확률 50%).
        *   `Prey` 객체 소멸 (Exit).

#### 2.2.2. Bankruptcy Manager (파산)
*   M&A 대상이 되지 못했으나, `Cash < 0` (지급 불능) 상태인 기업.
*   **Liquidation**:
    *   재고/자본재를 시장가/장부가 대비 50%(`LIQUIDATION_DISCOUNT_RATE`)로 강제 매각하여 채권자(Bank/Employees) 변제.
    *   잔여 자산 0, 직원 전원 해고.
    *   기업 소멸.

### 2.3. 충격 및 파급 효과
*   **실업 급증**: 파산/인수 과정에서 구조조정 발생 -> 노동 시장 공급 과잉 -> 임금 하락 압력.
*   **독과점**: 소수 기업이 시장 장악 -> 가격 결정권 강화 -> 인플레이션 압력.

## 3. 구현 단계 (Implementation Steps)
1.  **Step 1**: `Firm.calculate_valuation` 및 상태 진단 로직 구현.
2.  **Step 2**: `MAManager` 클래스 구현 (매칭 알고리즘).
3.  **Step 3**: `Engine`에 M&A/Bankruptcy 파이프라인 통합.
4.  **Step 4**: `verify_ma_bankruptcy.py` 검증 스크립트 작성.

## 4. 검증 계획 (Verification Plan)
*   **시나리오**:
    *   기업 A를 강제로 적자 상태(현금 고갈)로 만듦.
    *   기업 B(현금 부자)가 A를 인수하는지 확인.
    *   인수 실패 시 A가 파산하고 직원이 해고되는지 확인.
