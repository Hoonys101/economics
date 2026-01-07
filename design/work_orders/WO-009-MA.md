# WORK ORDER: WO-009-MA (Mergers & Acquisitions)
**To**: Jules (Lead Developer)
**From**: Antigravity (Team Leader)
**Subject**: Implement Phase 9 - The Corporate Food Chain

## 1. Objective
경제 생태계의 건전성을 위해 "부실 기업 퇴출(Bankruptcy)"과 "우량 기업의 확장(M&A)" 메커니즘을 구현하십시오.

## 2. Core Implementation Tasks

### A. Firm Valuation & Logic (`simulation/firms.py`)
1.  **`calculate_valuation(self)`**:
    *   `Net Assets` (Cash + Inventory Value + Capital Value) + `(Avg Profit * VALUATION_PER_MULTIPLIER)`.
    *   단, Profit이 음수면 0으로 처리.
2.  **`receive_acquisition_offer(self, offer_price)`**:
    *   내부 평가 가치(`calculate_valuation`) 대비 10% 이상 높으면 `True` 반환.
3.  **`liquidate_assets(self)`**:
    *   재고와 자본재를 시장가에 매각(또는 소멸 처리 후 현금화)하되, `LIQUIDATION_DISCOUNT_RATE`(0.5)를 적용하여 현금 회수.

### B. M&A Manager (`simulation/systems/ma_manager.py`)
*   `MAManager` 클래스를 구현하고 `engine.py`에서 호출하십시오.
*   **Process**:
    1.  **Bankruptcy Check**: `cash < 0`인 기업 식별 -> 즉시 `liquidate_assets` 후 시뮬레이션에서 제거.
    2.  **M&A Matching**:
        *   **Hunter**: 현금 > (직원 월급 * 6개월치).
        *   **Target**: Valuation이 낮고, 현금이 부족한 기업.
        *   성공 시: Hunter 현금 차감 -> Target 자산/직원 흡수 -> Target 제거.

### C. Configuration (`config.py`)
*   `MA_ENABLED`, `VALUATION_PER_MULTIPLIER` 등 필요한 상수는 제가 `config.py`에 이미 추가해 두었습니다(예정). 해당 상수를 사용하십시오.

## 3. Constraints & Quality
*   **Employee Transfer**: 피인수 기업의 직원은 그대로 인수 기업의 직원 리스트(`employees`)로 이동해야 합니다. (해고 아님)
*   **Logging**: M&A 및 파산 발생 시 `INFO` 레벨로 로그를 남기십시오. (중요 이벤트임)
*   **Traceability**: M&A 발생 시 `Transaction`을 생성하여 DB에 기록하십시오 (Type: "M&A", "LIQUIDATION").

## 4. Verification
*   `scripts/verify_ma_bankruptcy.py`를 작성하여 시나리오를 검증하십시오.
    *   Scenario 1: 현금 고갈 기업의 파산 및 퇴출.
    *   Scenario 2: 부자 기업의 가난한 기업 인수 및 통합.
