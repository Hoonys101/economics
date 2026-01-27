# 🔍 Git Diff Review: Fractional Reserve Banking

---

### 1. 🔍 Summary
이 변경 사항은 프로젝트의 금융 모델을 근본적으로 전환합니다. 기존의 '대여 가능 자금' 모델에서 은행이 대출을 통해 새로운 예금을 창출하는 '신용 창출' 및 '부분 지급준비금' 모델로 변경되었습니다. 이 과정에서 신용도 평가를 위한 `CreditScoringService`가 도입되었고, 대출 승인 로직이 DTI 및 LTV와 같은 금융 지표에 기반하도록 리팩토링되었습니다.

### 2. 🚨 Critical Issues
- 발견되지 않았습니다. API 키, 시스템 절대 경로, 외부 저장소 URL과 같은 하드코딩된 보안 취약점은 없는 것으로 보입니다.

### 3. ⚠️ Logic & Spec Gaps

- **(Minor) 미처리된 에지 케이스**: `simulation/systems/housing_system.py`에서 대출금 인출 실패 시(`LOAN_WITHDRAW_FAIL`) 에러만 기록하고 넘어갑니다.
    ```python
    # simulation/systems/housing_system.py, line ~190
    else:
        # Withdrawal failed (Liquidity Crisis?), rollback loan?
        # For simplicity in this iteration, we assume success or log error.
        logger.error(f"LOAN_WITHDRAW_FAIL | Could not withdraw loan proceeds for {buyer.id}")
    ```
    은행의 유동성 위기로 대출 실행 후 즉시 인출이 실패하는 경우, 대출 자체를 롤백하는 로직이 필요합니다. 현재는 대출은 실행되었지만 구매자는 자금을 사용할 수 없는 상태가 되어 자금 불일치를 유발할 수 있습니다.

- **(Minor) DTI 계산 로직의 모호성**: `modules/finance/credit_scoring.py`에서 소득과 부채가 모두 0일 때 DTI를 0으로 계산합니다.
    ```python
    # modules/finance/credit_scoring.py, line ~32
    dti = float('inf')
    if profile["existing_debt_payments"] == 0:
         dti = 0.0 # Technically 0 debt, but 0 income is still risky.
    ```
    소득이 0인 경우 부채 상환 능력이 없으므로 DTI가 0이 되는 것은 논리적으로 모순될 수 있습니다. 이후의 무담보 대출 한도 계산(`max_amount = profile["gross_income"] * max_unsecured_multiplier`)에서 대출액이 0이 되어 결과적으로는 대출이 거절되지만, DTI 계산 자체의 명확성을 높일 필요가 있습니다.

### 4. 💡 Suggestions

- **(Refactoring) 레거시 인터페이스 정리**: `tests/test_firms.py`에서 `mock_bank.get_debt_summary`와 `mock_bank.get_debt_status`를 모두 모의(mocking)하고 있습니다. 이는 `get_debt_summary`가 레거시 인터페이스일 수 있음을 시사합니다. 코드베이스 전반에서 새 인터페이스(`get_debt_status`)만 사용하도록 통일하고 이전 인터페이스는 제거하는 것을 권장합니다.
- **(Clarity) Zero-Sum 명시적 추적**: `simulation/bank.py`의 `grant_loan` 함수에서 `self.government.total_money_issued += amount`를 통해 총 통화량 증가를 기록하는 것은 훌륭합니다. 이와 같은 시스템 전체의 재무 상태 변경은 별도의 `AccountingSystem`이나 `CentralBank` 모듈에서 트랜잭션으로 명시적으로 처리하여 중앙에서 관리하는 것을 고려해볼 수 있습니다.

### 5. 🧠 Manual Update Proposal
- **Target File**: `design/manuals/ECONOMIC_INSIGHTS.md`
- **Update Content**:
    - diff에 포함된 `Concept: Fractional Reserve Banking & Endogenous Money` 섹션은 이번 변경의 핵심 개념, 메커니즘, 구현, 그리고 통찰을 매우 잘 요약했습니다.
    - 해당 문서의 기존 형식과 일치하며, 프로젝트의 지식 자산을 풍부하게 하는 훌륭한 업데이트입니다. 이 변경 사항은 그대로 승인하는 것이 타당합니다.

### 6. ✅ Verdict
**REQUEST CHANGES**

**Reasoning**: 아키텍처 개선과 핵심 기능 구현은 매우 훌륭합니다. 크리티컬한 보안 이슈는 없으나, `Logic & Spec Gaps`에서 지적된 사소한 논리적 허점(대출금 인출 실패 처리)을 보완한 후 머지하는 것이 좋겠습니다. 제안된 사항들은 코드의 견고성을 더욱 높일 것입니다.
