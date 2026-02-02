# 🔍 Summary
본 변경 사항은 주택 구매 프로세스에서 발생하던 심각한 화폐 누수(Money Leak) 버그를 해결합니다. `grant_loan` 호출 시 생성되던 임시 예금을 즉시 회수(Neutralize)하고, 대출금이 은행의 보유금(Reserves)에서 에스크로로 직접 이체되도록 흐름을 수정하여 Zero-Sum 원칙을 복원합니다. 또한, 이와 관련된 실패한 유닛 테스트들을 개선된 Mocking 기법을 사용하여 모두 수정하였습니다.

# 🚨 Critical Issues
- **없음**: 하드코딩된 경로, API 키, 또는 기타 보안 취약점이 발견되지 않았습니다. 수정의 핵심 목적인 화폐 복사 버그가 성공적으로 해결되었습니다.

# ⚠️ Logic & Spec Gaps
- **없음**: 기존에 존재하던 구현과 명세 간의 불일치 문제를 해결했습니다. 자금 이체 흐름(Saga)과 실패 시 보상(Compensation) 로직이 명확하고 견고하게 개선되었습니다.
  - 대출 실행(Disbursement) 실패 시, 예금 생성 후 회수가 일어났으므로 `void_loan` 대신 `terminate_loan`을 호출하여 대출 기록을 종료하는 로직이 정확합니다.
  - 최종 정산(Settlement) 실패 시, 대출 원금은 은행(Bank)으로, 계약금(Down Payment)은 구매자(Buyer)에게 각각 반환하는 보상 로직이 자금의 출처에 맞게 정확하게 구현되었습니다.

# 💡 Suggestions
- **장기적 리팩토링 제안**: 현재 해결책은 기존 `Bank.grant_loan`의 동작을 변경할 수 없다는 제약 하에서 매우 훌륭합니다. 하지만 장기적으로는 `Bank.grant_loan` 함수가 "대출금 즉시 예금" 또는 "에스크로 직접 지급" 옵션을 선택할 수 있도록 리팩토링한다면, 이번에 추가된 "예금 생성 후 즉시 회수(Neutralization)" 단계를 제거하여 코드를 더욱 단순화할 수 있을 것입니다.

# 🧠 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/FINANCIAL_INTEGRITY_PATTERNS.md` (신규 또는 기존 시스템 설계 원칙 문서)
- **Update Content**: 이번 수정 과정에서 발견된 중요한 교훈을 중앙 지식 베이스에 추가할 것을 제안합니다.

```markdown
# Financial Integrity Patterns & Lessons

## 1. 금융 거래의 원자성 (Financial Atomicity)
*   **교훈**: 부분 준비금 시스템에서 "대출(Loan)"은 곧 "신규 예금(New Deposit)"의 생성을 의미합니다. 만약 특정 트랜잭션이 "은행 -> 판매자"로 직접 자금을 이체하는 시나리오를 요구한다면, 대출 과정에서 차용자에게 임시로 생성된 신규 예금을 명시적으로 처리(예: 즉시 회수)하여 광의통화(Broad Money) 추적 시 이중 계산이나 누수를 방지해야 합니다.

## 2. 복잡한 객체 Mocking 전략
*   **교훈 1 (Properties Mocking)**: `@property`를 사용하여 내부 상태에 접근하는 복잡한 도메인 객체(예: `Household`)를 Mocking할 때, `MagicMock(spec=Class)`만으로는 속성 접근을 처리할 수 없습니다. 반드시 `type(mock).prop = PropertyMock(...)` 구문을 사용하여 속성 자체를 `PropertyMock`으로 지정해야 합니다.
*   **교훈 2 (Config Mocking)**: 코드에서 `getattr(config, "housing", {}).get(...)`와 같이 중첩된 `get`을 사용하여 설정값을 가져오는 경우, 설정 Mock 객체의 하위 속성을 명시적으로 `config.housing = {}`와 같이 실제 딕셔너리로 설정해야 합니다. 그렇지 않으면 내부 `get` 호출이 또 다른 Mock 객체를 반환하여 미묘한 타입 에러를 유발할 수 있습니다.
```

# ✅ Verdict
**APPROVE**

- **사유**: 치명적인 Zero-Sum 위반 버그를 성공적으로 수정했으며, 관련 단위 테스트를 모두 복구했습니다. 무엇보다 **규정에 따라 `communications/insights/FIX_HOUSING_LEAK_AND_TESTS.md` 인사이트 보고서가 정확한 형식으로 작성 및 제출**되었습니다. 모든 기준을 완벽하게 충족합니다.
