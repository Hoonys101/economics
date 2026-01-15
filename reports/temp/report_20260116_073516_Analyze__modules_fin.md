# 재무 시스템 복식부기 원칙 준수 분석 보고서

## Executive Summary
`service_debt` 메서드는 복식부기 원칙을 준수하여 자금 이전이 명확합니다. 그러나 `issue_treasury_bonds` 메서드는 양적완화(QE) 시나리오에서 대응 차변 없이 화폐를 창출하며, `grant_bailout_loan` 메서드는 자금이 대변으로 이전되지 않아 화폐가 소멸되는 문제를 가지고 있어 복식부기 원칙을 부분적으로 위반합니다.

## Detailed Analysis

### 1. `issue_treasury_bonds` (국채 발행)
- **Status**: ⚠️ 부분 준수
- **Notes**: 메서드는 두 가지 시나리오로 나뉘며, 하나는 원칙을 준수하고 다른 하나는 위반합니다.

- **시나리오 1: 일반 시장 매각**
    - **차변 (Debtor)**: 상업 은행 (`Bank`)
    - **대변 (Creditor)**: 정부 (`Government`)
    - **Evidence**: `modules/finance/system.py:L76-L77`
      - 은행 자산 감소: `self.bank.assets -= amount`
      - 정부 자산 증가: `self.government.assets += amount`
    - **Verification**: 차변과 대변이 일치하는 제로섬(Zero-Sum) 거래로, 복식부기 원칙을 준수합니다.

- **시나리오 2: 중앙은행 개입 (양적완화, QE)**
    - **차변 (Debtor)**: ❌ **없음**
    - **대변 (Creditor)**: 정부 (`Government`)
    - **Evidence**: `modules/finance/system.py:L70-L73`, `modules/finance/system.py:L84`
      - 중앙은행이 채권을 매입하지만(`self.central_bank.purchase_bonds(new_bond)`), 현금 자산이 감소하는 로직이 없습니다.
      - 정부의 자산은 증가합니다: `self.government.assets += amount`
    - **Verification**: 🔴 **원칙 위반.** 정부의 자산이 증가하는 동안 대응하는 자산 감소 주체가 없어 시스템 내에서 화폐가 창출됩니다. 주석(`Money is created here`)은 이를 의도된 동작으로 명시하고 있으나, 회계적으로는 불일치합니다.

### 2. `grant_bailout_loan` (구제금융 대출)
- **Status**: ❌ 위반
- **차변 (Debtor)**: 정부 (`Government`)
- **대변 (Creditor)**: ❌ **없음**
- **Evidence**: `modules/finance/system.py:L100-L101`
  - 정부 자산 감소: `self.government.assets -= amount`
  - 기업 부채 추가: `firm.finance.add_liability(amount, loan.interest_rate)`
- **Verification**: 🔴 **원칙 위반.** 정부의 자산이 `amount`만큼 감소하지만, 대출을 받는 기업(`Firm`)의 현금 자산(`assets`)이 해당 함수 내에서 명시적으로 증가하지 않습니다. 이로 인해 시스템에서 화폐가 소멸됩니다.

### 3. `service_debt` (채무 상환)
- **Status**: ✅ 준수
- **차변 (Debtor)**: 정부 (`Government`)
- **대변 (Creditor)**: 채권 보유자 (중앙은행 또는 상업 은행)
- **Evidence**: `modules/finance/system.py:L117-L131`
  - 정부 자산 감소: `self.government.assets -= total_repayment`
  - 채권 보유자 자산 증가:
    - 중앙은행: `self.central_bank.assets["cash"] = ... + total_repayment`
    - 또는 상업 은행: `self.bank.assets += total_repayment`
- **Verification**: 정부의 자산 감소분이 채권 보유자에게 정확히 이전되는 제로섬 거래로, 복식부기 원칙을 완벽히 준수합니다. 주석(`BUG FIX`)은 이러한 정확성을 의도했음을 보여줍니다.

## Risk Assessment
- **화폐량 왜곡**: QE 시나리오에서의 화폐 창출과 구제금융에서의 화폐 소멸은 시뮬레이션의 총 통화량을 왜곡하여, 인플레이션 및 기타 거시 경제 지표의 신뢰성을 저해할 수 있습니다.
- **디버깅 어려움**: 자금 흐름이 명확하지 않은 로직은 추후 시스템에서 예기치 않은 버그가 발생했을 때 원인 추적을 어렵게 만듭니다.

## Conclusion
`issue_treasury_bonds`의 QE 로직과 `grant_bailout_loan` 함수는 복식부기 원칙을 준수하도록 수정이 필요합니다. 특히, `grant_bailout_loan` 함수는 대출받는 기업의 현금 자산을 명시적으로 증가시키는 로직을 추가하여 화폐 소멸 문제를 해결해야 합니다.
