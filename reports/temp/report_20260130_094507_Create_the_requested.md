I am unable to directly write or modify files. As a Technical Reporter, my role is to analyze information and generate reports.

Therefore, I will provide the complete, ready-to-use content for the requested files. You can then create or update the files with the provided text.

***

# Report: Insight Generation from PR Reviews

## 1. New File: `communications/insights/WO-996-Housing-System-Money-Leak-Fix.md`

**Instructions:** Create the following new file with the content below.

```markdown
# Insight Report: Housing System Money Leak Fix

### 현상 (Phenomenon)
- 주택 구매 트랜잭션에서 대출(`Mortgage`)이 실행될 때, 시스템의 총 화폐량이 비정상적으로 증가하는 '돈 복사(Magic Money Creation)' 버그가 식별됨.

### 원인 (Cause)
- 기존 로직은 은행의 대출 실행을 `bank.withdraw_for_customer()`와 `buyer._add_assets()`의 조합으로 처리했음.
- `withdraw_for_customer`는 은행의 부채(고객 예금) 항목만 감소시킬 뿐, 은행의 실제 자산(지급준비금)을 차감하지 않았음.
- 이 상태에서 `buyer._add_assets()`가 호출되자, 은행 자산은 그대로인 채 구매자의 자산만 일방적으로 증가하여 시스템에 없던 돈이 생성됨.

### 해결 (Resolution)
- 모든 화폐 이동을 중앙 `SettlementSystem.transfer(payer, payee, amount)`를 사용하도록 강제함.
1.  **대출금 지급**: `settlement.transfer(bank, buyer, loan_amount)`를 호출하여, 은행의 자산을 명시적으로 차감하고 구매자의 자산을 증가시켜 제로섬(Zero-Sum)을 보장함.
2.  **지급 실패 롤백**: 대출금 지급 또는 주택 대금 지급이 실패할 경우, 이전 트랜잭션을 모두 취소(대출 무효화, 자금 반환)하는 롤백 로직을 추가하여 데이터 정합성을 확보함.
3.  **테스트케이스 추가**: 지급 성공, 지급 실패, 롤백 등 모든 시나리오를 검증하는 유닛 테스트를 작성하여 재발을 방지함.

### 교훈 (Lesson Learned)
- 시스템 내 모든 가치(자산, 자원)의 이동은 반드시 거래의 양쪽(차변/대변)을 모두 포함하는 중앙화된 트랜잭션 함수를 통해 처리해야 한다.
- `_add_assets`, `_sub_assets`와 같이 자산을 일방적으로 조작하는 메서드는 제로섬 원칙을 깨뜨릴 위험이 매우 높으므로, 사용을 절대적으로 지양하고 `SettlementSystem` 사용을 강제해야 한다. 이는 시스템 경제의 무결성을 지키는 핵심 원칙이다.
```

## 2. Update File: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md`

**Instructions:** The file for `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md` was not found. Please create it with the following content.

```markdown
### [INSIGHT] 중앙 원장(SettlementSystem)을 통한 Zero-Sum 무결성 보장

*   **현상 (Phenomenon):**
    이전의 상속(inheritance)과 같은 자산 이전 로직은 개별 시스템이 각 주체의 자산을 직접 더하고 빼는 방식(`agent._add_assets`, `gov.collect_tax`)으로 구현되었습니다. 이로 인해 부동소수점 계산 오류나 로직의 복잡성으로 인해 시스템 전체의 화폐 총량이 미세하게 변하는 Zero-Sum 위반(돈 복사/누수) 위험에 노출되어 있었습니다.

*   **원인 (Cause):**
    자산 이전에 대한 책임이 여러 시스템에 분산되어 있었고, 모든 차변(debit)에 대응하는 대변(credit)이 원자적(atomic)으로 발생함을 보장하는 단일 주체가 없었습니다. 각 기능이 독립적으로 자산을 조작하면서 전체적인 일관성을 깨뜨릴 가능성이 컸습니다.

*   **해결 (Solution):**
    `SettlementSystem`이라는 중앙화된 원장 시스템을 도입했습니다. 모든 자산 이전(세금, 상속, 거래 등)은 반드시 `SettlementSystem.transfer(from, to, amount)`를 통해서만 이루어지도록 강제합니다. 이 `transfer` 메서드 내부에서 보내는 쪽의 자산을 차감하고 받는 쪽의 자산을 증가시키는 것을 하나의 트랜잭션으로 처리하여 Zero-Sum을 시스템 수준에서 보장합니다. 이번 커밋에서 상속 로직 전체가 이 시스템을 사용하도록 리팩토링되었습니다.

*   **교훈 (Lesson Learned):**
    화폐와 같이 시스템 내 총량이 불변해야 하는 자원은, 반드시 단일화되고 중앙화된 **원장(Ledger) 또는 결제(Settlement) 시스템**을 통해서만 이전되어야 합니다. 각 모듈이 자산을 직접 조작하는 것을 금지하고, 모든 흐름을 단일 시스템에 위임하는 것은 Zero-Sum 무결성을 보장하는 핵심 아키텍처 원칙입니다.
```

## 3. Unaddressed Request: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

- **Status**: ❌ Not Actioned
- **Reason**: The instruction requested an update regarding a "firm management fallback insight." This topic was not mentioned in the provided source PR review reports (`pr_review_housing-system-money-leak-*.md` and `pr_review_demographic-manager-zero-sum-*.md`). I cannot generate content that is not supported by the provided context.
