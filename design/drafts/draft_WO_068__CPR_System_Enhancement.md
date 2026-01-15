WO-068 (CPR 시스템 강화)에 대한 상세 설계 초안 및 API 명세서입니다.
기존의 무조건적인 '헬리콥터 머니' 방식을 폐기하고, **좀비 기업 선별(Screening)** 및 **대출 전환(Conversion to Loan)** 로직을 도입하여 재정 건전성을 확보하도록 설계했습니다.

---

### 1. `modules/cpr/api.py` (초안)

```python
"""
modules/cpr/api.py

CPR (Corporate Preservation & Recovery) System API Contract.
Defines strict protocols for bailouts, solvency checks, and government loan management.
"""

from typing import TypedDict, Optional, List, Protocol, runtime_checkable
from dataclasses import dataclass
from enum import Enum

# --- Constants & Enums ---

class BailoutStatus(Enum):
    APPROVED = "APPROVED"
    REJECTED_ZOMBIE = "REJECTED_ZOMBIE"     # 회생 가능성 없음
    REJECTED_MORAL_HAZARD = "REJECTED_MORAL_HAZARD" # 자산 충분함
    PENDING_FUNDS = "PENDING_FUNDS"         # 정부 예산 부족

# --- DTO Definitions ---

@dataclass
class BailoutRequestDTO:
    """
    기업이 구제금융을 요청할 때 제출하는 데이터 명세
    """
    firm_id: str
    tick: int
    current_assets: float
    current_liabilities: float
    avg_profit_last_10_ticks: float
    inventory_valuation: float  # 재고 자산 가치 (Liquidity Check용)
    market_share: float         # 'Too big to fail' 판별용

@dataclass
class LoanContractDTO:
    """
    정부 대출 계약서 (Grant 대신 발행)
    """
    contract_id: str
    lender_id: str          # Government ID
    borrower_id: str        # Firm ID
    principal_amount: float
    interest_rate: float    # Annual Rate
    start_tick: int
    duration_ticks: int
    monthly_payment: float  # Principal + Interest
    remaining_balance: float
    status: str = "ACTIVE"  # ACTIVE, DEFAULTED, PAID_OFF

@dataclass
class BailoutJudgementDTO:
    """
    CPR 시스템의 심사 결과
    """
    request_id: str
    status: BailoutStatus
    approved_amount: float = 0.0
    loan_terms: Optional[LoanContractDTO] = None
    rejection_reason: str = ""
    viability_score: float = 0.0  # 0.0 ~ 1.0

# --- Interface Definitions ---

@runtime_checkable
class IBailoutManager(Protocol):
    """
    CPR 시스템의 핵심 인터페이스
    """
    def evaluate_eligibility(self, request: BailoutRequestDTO) -> BailoutJudgementDTO:
        """
        좀비 기업 여부와 회생 가능성을 판단합니다.
        """
        ...

    def execute_bailout(self, judgement: BailoutJudgementDTO, government_agent: 'Any') -> bool:
        """
        승인된 구제금융을 집행하고, 정부 자산 차감 및 대출 계약을 생성합니다.
        """
        ...

    def process_repayments(self, active_loans: List[LoanContractDTO], current_tick: int) -> float:
        """
        매 틱 대출 상환을 처리하고, 정부 수입(이자+원금)을 반환합니다.
        """
        ...

# --- Exceptions ---

class ZombieFirmDetectedError(Exception):
    """회생 불가능한 좀비 기업으로 판별됨"""
    pass

class FiscalCliffError(Exception):
    """정부 재정 고갈로 구제금융 불가"""
    pass
```

---

### 2. `design/specs/cpr_enhancement_spec.md` (상세 설계서)

```markdown
# Spec: CPR System Enhancement (WO-068)

**Author:** Gemini (Administrative Assistant)
**Date:** 2026-01-15
**Related WO:** WO-068
**Status:** DRAFT (Ready for Review)

## 1. 개요 (Overview)
기존의 `Bootstrapper`는 자산이 음수인 기업에게 무조건적인 무상 지원(Grant)을 수행하여 "좀비 기업"의 생명을 인위적으로 연장하고 정부 재정을 악화시킴(TD-008, TD-009).
본 명세는 이를 **선별적 대출(Selective Loan)** 시스템으로 전환하여 경제의 자정 작용을 복구하고 재정 규율을 확립하는 것을 목표로 한다.

## 2. 핵심 변경 사항 (Key Changes)
1.  **Grant → Loan**: 공짜 점심은 없다. 모든 지원금은 원리금 상환 의무가 있는 대출로 전환된다.
2.  **Zombie Filtering**: 과거 수익성과 자산 회전율을 기반으로 회생 가능성을 평가한다.
3.  **Fiscal Integration**: 대출금 지급은 정부의 `Assets` 감소와 `Claims`(채권) 증가로 기록되며, 상환 불이행 시 `Debt`으로 확정된다.

## 3. 상세 로직 (Detailed Logic)

### 3.1. 적격성 심사 (Eligibility Check) - `evaluate_eligibility`
CPR 매니저는 다음 알고리즘에 따라 기업을 평가한다.

```python
# Pseudo-code
def evaluate_eligibility(request: BailoutRequestDTO) -> BailoutJudgementDTO:
    # 1. 도덕적 해이 체크 (Moral Hazard Check)
    if request.current_assets > 0:
        return REJECTED_MORAL_HAZARD ("자산이 남아있는데 지원 요청함")

    # 2. 좀비 기업 판별 (Zombie Detection)
    # 기준 A: 최근 10틱 평균 순이익이 지속적 적자인가?
    profit_condition = request.avg_profit_last_10_ticks > -50.0 
    
    # 기준 B: 부채가 재고 가치의 2배를 초과하는가? (자산 건전성)
    insolvency_depth = abs(request.current_assets) # 현재 자산이 음수이므로 절대값은 부채 갭
    asset_condition = insolvency_depth < (request.inventory_valuation * 2.0)

    # 기준 C: 대마불사 (Systemic Importance)
    is_too_big = request.market_share > 0.3

    if (profit_condition and asset_condition) or is_too_big:
        # 회생 가능
        amount_needed = insolvency_depth + SAFETY_BUFFER
        loan = create_loan_contract(amount_needed)
        return APPROVED(loan)
    else:
        # 회생 불가능 -> 시장 퇴출 유도 (M&A or Liquidation)
        return REJECTED_ZOMBIE
```

### 3.2. 대출 집행 및 재정 영향 (Execution & Fiscal Impact)

*   **대출 실행 시:**
    *   `Government.assets` -= `principal_amount`
    *   `Firm.assets` += `principal_amount`
    *   `Firm.liabilities` += `principal_amount` (대출금)
    *   **Note**: 이 시점에서 정부의 `total_debt`는 증가하지 않음 (자산 교환). 단, 정부 현금이 마이너스가 될 경우 Deficit Spending 트리거됨.

*   **상환 (Repayment) 매 틱:**
    *   기업은 `monthly_payment`를 지불.
    *   `Government.assets` += payment
    *   상환 실패 시: `Default` 처리 -> 기업 파산 절차(Autopsy)로 이관.

### 3.3. 금리 결정 (Interest Rate Pricing)
*   **Base Rate**: 중앙은행 기준금리 (Config 참조)
*   **Spread**: 신용 위험 스프레드 (기본 5.0% - 고위험 대출임)
*   **Penalty**: 상환 지연 시 1.5배 가산 금리.

## 4. 데이터 승격 및 테스트 계획 (Data Promotion & Verification)

### 4.1. Fixture Data (`tests/fixtures/cpr_cases.json`)
*   **Case A (Normal)**: 일시적 유동성 위기 (이익 흑자, 현금 부족). -> **Expected: APPROVED**
*   **Case B (Zombie)**: 만성 적자, 재고 가치 없음. -> **Expected: REJECTED_ZOMBIE**
*   **Case C (Big Fail)**: 만성 적자이나 시장 점유율 40%. -> **Expected: APPROVED (Too Big To Fail)**

### 4.2. Golden Sample (`tests/goldens/cpr_audit.json`)
*   승인된 대출 계약의 상세 내역과 상환 스케줄을 검증.

## 5. 기술 부채 및 제약 사항 (Constraints)
*   **DB Migration**: 기존에 `Grants`로 처리된 내역은 소급 적용하지 않음.
*   **Circular Dependency**: `Government` 모듈이 `CPR` 모듈을 참조하므로, 타입 힌팅 시 `TYPE_CHECKING` 가드를 철저히 사용할 것.

---

**[Routine] Mandatory Reporting**
Jules는 구현 과정에서 다음 항목을 발견 시 `communications/insights/`에 보고해야 함:
1. 좀비 기업 기준(임계값)이 너무 엄격하여 연쇄 파산을 유발하는지 여부.
2. 대출 이자 상환 부담으로 인한 2차 유동성 위기 발생 빈도.
```

---

### 3. Action Request

**팀장(Antigravity)님**, 위 명세와 API 초안을 검토해 주십시오.
승인 시 `simulation/systems/cpr/` 폴더 구조를 생성하고 구현자(Jules)에게 할당하겠습니다.
(현재 `modules` 폴더 대신 기존 구조와의 정합성을 위해 `simulation/systems` 하위를 제안드립니다. 만약 `modules/cpr`을 고수해야 한다면 지시해 주십시오.)
