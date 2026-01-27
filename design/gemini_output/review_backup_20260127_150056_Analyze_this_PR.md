# 🔍 Git Diff Review: Fractional Reserve Banking

## 🔍 Summary

이 변경은 프로젝트의 금융 시스템을 근본적으로 전환합니다. 기존의 "대출 가능 자금(Loanable Funds)" 모델에서 은행이 대출을 통해 새로운 화폐를 창조하는 현대적인 "신용 창조(Credit Creation)" 또는 부분 지급준비금(Fractional Reserve) 모델로 변경되었습니다. 이를 위해 `CreditScoringService`가 도입되어 대출 심사 프로세스를 자동화하고, 대출 승인 시 은행은 예금을 창조하여 시스템의 총 통화량을 동적으로 조절합니다.

## 🚨 Critical Issues

- 발견된 사항 없음.

## ⚠️ Logic & Spec Gaps

1.  **위험한 폴백 로직 (Brittle Fallback Logic)**
    - **위치**: `simulation/bank.py`, `void_loan` 함수
    - **문제**: 대출을 취소할 때, `loan.created_deposit_id`가 없는 경우, 금액과 소유주가 같은 예금을 찾아 삭제하는 폴백(fallback) 로직이 있습니다. 주석에도 "brittle but necessary"라고 명시되어 있듯이, 만약 한 대출자가 완전히 동일한 금액의 예금을 두 개 가지고 있다면, 잘못된 예금이 삭제되어 시스템에 통화 누수(Money Leak)를 유발할 수 있습니다.
    - **영향**: 제로섬(Zero-Sum) 원칙을 위반할 수 있는 잠재적 버그입니다.

2.  **자산 없는 대출자의 소득 0 처리**
    - **위치**: `modules/finance/credit_scoring.py`, `assess_creditworthiness` 함수
    - **분석**: 소득(`gross_income`)이 0이고 기존 부채(`existing_debt_payments`)도 0일 때, DTI를 `0.0`으로 설정합니다. 기술적으로는 맞지만, 소득이 없으면 어떤 부채도 상환할 수 없으므로 리스크가 무한대에 가깝습니다. 현재는 이후의 "담보 없는 대출 한도(Unsecured Cap)" 로직(`max_amount = profile["gross_income"] * max_unsecured_multiplier`가 0이 됨)에 의해 대출이 거절되므로 문제는 없습니다. 하지만 DTI 계산 로직 자체는 향후 리팩토링 시 오해를 유발할 수 있습니다.

## 💡 Suggestions

1.  **`void_loan`의 폴백 로직 강화**
    - `void_loan`의 폴백 로직은 매우 위험하므로, `CRITICAL` 로깅에 더해 예외(Exception)를 발생시켜 시뮬레이션을 중단시키거나, 해당 대출을 "부실채권(Bad Debt)"으로 즉시 분류하여 격리하는 등의 더 강력한 처리 방안을 고려해야 합니다. 이는 돈이 회수 불가능한 상태로 시스템에 남는 것을 방지합니다.

2.  **월별 부채 상환액 추정치 명확화**
    - **위치**: `simulation/decisions/corporate_manager.py`
    - `daily_burden * 30`으로 월별 부채 상환액을 추정하는 것은 합리적이나, 이는 가정에 기반한 값입니다. 향후 대출 상품에 명확한 상환 스케줄이 도입된다면, 이 부분을 실제 상환액을 사용하도록 개선해야 할 것입니다. 이는 현재 이슈는 아니지만, 기술 부채(Technical Debt)로 기록해두는 것을 제안합니다.

3.  **주택 구매 실패 시 롤백 로직**
    - **위치**: `simulation/systems/housing_system.py`
    - 주택 구매를 위해 대출을 받았으나, 대출금 인출(withdrawal)에 실패했을 때 `void_loan`을 호출하여 롤백하는 로직은 매우 훌륭합니다. 이는 "Settle-then-Record" 원칙을 잘 적용한 예시이며, 시스템 안정성을 크게 높입니다.

## 🧠 Manual Update Proposal

-   **Target File**: `design/manuals/ECONOMIC_INSIGHTS.md`
-   **Update Content**:
    -   Diff에 포함된 `Fractional Reserve Banking & Endogenous Money` 섹션은 새로운 신용 창조 메커니즘을 매우 정확하고 명확하게 설명하고 있습니다. 구현 내용(`grant_loan`의 자산 미차감, `CreditScoringService`의 역할)과 시스템에 미치는 영향(통화량의 동적 확장)까지 잘 정리되어 있어 그대로 반영하는 것이 적절합니다.

## ✅ Verdict

**REQUEST CHANGES**

전반적으로 매우 인상적인 리팩토링입니다. 특히 신용 창조와 부분 지급준비금 시스템의 핵심을 잘 구현했고, 테스트 코드까지 꼼꼼하게 추가한 점이 돋보입니다.

다만, `void_loan`의 폴백 로직은 시스템의 제로섬 원칙을 깰 수 있는 잠재적 위험을 내포하고 있으므로, 이 부분에 대한 보강(예: 예외 발생 또는 부실채권 처리)이 반드시 필요합니다. 해당 수정이 완료되면 `APPROVE` 할 수 있습니다.
