# 🔍 PR Review: TD-274 Bank Class Decomposition

## 🔍 Summary

`Bank` 클래스가 단일 책임 원칙(SRP)을 위반하는 거대 객체(God Class)에서, 새로운 `LoanManager`와 `DepositManager`를 조율하는 퍼사드(Facade) 패턴으로 성공적으로 리팩토링되었습니다. 이번 변경을 통해 금융 로직의 모듈성이 크게 향상되었으며, 새로운 프로토콜 인터페이스, DTO, 그리고 단위 테스트가 추가되어 코드의 안정성과 확장성이 개선되었습니다.

## 🚨 Critical Issues

**None.**
보안 위반, 자산/부채 불일치(Zero-Sum) 버그, 또는 심각한 수준의 하드코딩은 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps

**None.**
기존 `Bank` 클래스가 가지고 있던 복잡한 로직(대출 생성, 상환, 이자 수집, 예금 관리, 부도 처리)이 각 관리자 모듈로 충실하게 분해 및 이전되었음을 확인했습니다. 특히, 자금 인출 실패 시 지갑 상태를 롤백하는 로직(`withdraw_for_customer`)이 포함되어 자산 누수(money leak)를 방지한 점이 돋보입니다.

## 💡 Suggestions

- **`modules/finance/managers/loan_manager.py`의 하드코딩된 이자율:**
  - `submit_loan_application` 함수 내에 `interest_rate=0.05`가 하드코딩되어 있습니다. 주석(`# Default?`)으로 인지하고 있는 점은 좋으나, 향후 혼란을 방지하기 위해 이 값을 `config`에서 가져오도록 수정하는 것을 권장합니다.

## 🧠 Implementation Insight Evaluation

- **Original Insight**:
  ```markdown
  # Technical Insight Report: TD-274 Bank Class Decomposition

  ## 1. Problem Phenomenon (Stack traces, symptoms)
  The `Bank` class in `simulation/bank.py` had grown into a "God Class", violating the Single Responsibility Principle (SRP). It managed:
  -   Reserves and liquidity (Wallet).
  -   Loan lifecycle (creation, interest, default, repayment).
  -   Deposit lifecycle (creation, interest, withdrawal).
  -   Central Banking functions (Lender of Last Resort, OMO - partially).
  -   Direct agent manipulation (modifying `shares_owned`, `education_xp` on default), violating "No Raw Agent Access" rules.
  This resulted in:
  -   High coupling: Changes to loan logic risked breaking deposit logic.
  -   Abstraction Leaks: `Bank` accessed agent internals directly instead of using protocols.
  -   Protocol Bypass: `SettlementSystem` was often bypassed for direct asset manipulation (`agent.assets -= x`).

  ## 2. Root Cause Analysis
  -   **Organic Growth**: Features were added to `Bank` over time without architectural boundaries.
  -   **Lack of dedicated Managers**: Financial instruments (Loans, Deposits) were treated as simple data structures (`Dict[str, Loan]`) rather than domains requiring their own logic.
  -   **Legacy Patterns**: Code relied on direct dictionary manipulation and attribute access (`hasattr`) instead of `IFinancialEntity` protocols.

  ## 3. Solution Implementation Details
  The `Bank` class was refactored into a **Facade** that orchestrates two new managers:
  1.  **LoanManager (`modules/finance/managers/loan_manager.py`)**:
      -   Implements `ILoanManager`.
      -   Manages `_Loan` lifecycle.
      -   Calculates interest and defaults purely based on logic (no agent access).
      -   Uses a callback mechanism to request payments, keeping it decoupled from the payment execution system.

  2.  **DepositManager (`modules/finance/managers/deposit_manager.py`)**:
      -   Implements `IDepositManager`.
      -   Manages `_Deposit` accounts.
      -   Calculates interest payouts.
      -   Provides `withdraw` functionality for the Bank.

  3.  **Bank Facade (`simulation/bank.py`)**:
      -   Holds `self.loan_manager` and `self.deposit_manager`.
      -   Delegates business logic to managers.
      -   Acts as the **Context Root** for `SettlementSystem` interactions.
      -   Injects callbacks into `LoanManager.service_loans` that bridge the gap between `borrower_id` and the `Agent` object required by `SettlementSystem`.
      -   Handles the "consequences" of default (e.g., penalties) since it has access to the `agents_dict`, respecting the boundary that Managers should not touch Agents.

  ## 4. Lessons Learned & Technical Debt Identified
  -   **Facade Pattern**: Effective for breaking down God Classes while maintaining the existing public API (`IBankService`), minimizing disruption to consumers (`Household`, `Firm`).
  -   **Callback Injection**: Passing a `payment_callback` to `LoanManager` allowed the manager to remain "Pure" (operating on IDs and Math) while the "Impure" side (Database/Agent lookups/Settlement) remained in the Facade.
  -   **Tech Debt**: The `Bank` still handles `process_default` consequences (XP penalty, credit freeze) which feels like it belongs in a `CreditBureau` or `JudicialSystem`. Moving this logic out would further purify `Bank`.
  -   **Tech Debt**: `DepositManager` does not natively support reserve ratio checks; the `Bank` currently approximates or skips strict reserve enforcement based on aggregated data. This should be formalized.
  ```
- **Reviewer Evaluation**:
  - **Excellent.** 이 인사이트 보고서는 문제 현상, 근본 원인, 해결책을 매우 명확하고 정확하게 기술하고 있습니다.
  - 특히, 리팩토링 과정에서 새로 식별된 기술 부채(부도 처리 책임 소재, 예금 준비율 로직 부재)를 명시한 점은 매우 훌륭합니다. 이는 단순히 코드를 변경하는 것을 넘어, 시스템 아키텍처의 발전에 기여하는 높은 수준의 통찰력을 보여줍니다.
  - 'Callback Injection'과 같은 디자인 패턴의 장점을 명확히 이해하고 문서화한 점은 다른 개발자들에게 좋은 학습 자료가 될 것입니다.

## 📚 Manual Update Proposal

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**: Diff에 포함된 `TECH_DEBT_LEDGER.md`의 업데이트 내용은 인사이트 보고서에서 식별된 기술 부채를 정확하게 요약하고 있으며, 소스 파일 링크까지 포함하여 올바르게 작성되었습니다. **제안된 변경안을 그대로 반영하는 것에 동의합니다.**

## ✅ Verdict

**APPROVE**

이번 PR은 복잡한 리팩토링을 매우 높은 품질로 수행한 모범적인 사례입니다. 아키텍처 개선, 충실한 문서화, 그리고 새로운 단위 테스트 추가까지 모든 요구사항을 완벽하게 충족했습니다. 즉시 병합하는 것을 승인합니다.