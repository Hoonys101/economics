# Code Review Report: WO-FINAL-MACRO-REPAIR

## 🔍 Summary
이번 PR은 OMO(공개시장조작)의 수량 계산 오류(Dimensional Correction)를 수정하고, 자산이 충분한 기업이 연속 적자로 인해 파산하는 문제(Solvency-First Lifecycle)를 해결했습니다. 또한 OMO 트랜잭션 시 M2 통화량 추적 로직이 추가되었습니다.

## 🚨 Critical Issues
*발견된 Critical Issue 없음* (직각적인 보안 위반이나 시스템 파괴 버그는 없음)

## ⚠️ Logic & Spec Gaps
1. **Stateless Engine/Handler Purity 위반 (Architecture Violation)**
   - `simulation/systems/handlers/monetary_handler.py` 파일의 `MonetaryTransactionHandler` 내부에서 `context.central_bank.total_money_issued`를 직접 조작하여 상태를 변경하고 있습니다.
   - 기존 주석(`This aligns with the new "Settle-then-Record" architecture where handlers do not mutate agents.`)을 제거하고 핸들러 내부에서 Agent의 상태를 직접 수정하는 것은 아키텍처 규칙("모든 상태 변경이 오직 Agent/Orchestrator 내부에서만 일어나야 함")에 정면으로 위배됩니다.
   - 동일한 로직이 `simulation/systems/central_bank_system.py`의 `process_omo_settlement`에도 중복으로 추가되어 있습니다.
2. **Magic Numbers 하드코딩 (Hardcoding)**
   - `CentralBankSystem.execute_open_market_operation` 내에 `par_value_pennies = 10000`, `limit_price_pennies = 11000`, `limit_price = 110.0` 등의 매직 넘버가 시스템 절대값으로 하드코딩되어 있습니다. 환경 설정(Config)을 통해 주입받아야 합니다.

## 💡 Suggestions
- **Settle-then-Record 원칙 복구**: `MonetaryTransactionHandler` 및 `CentralBankSystem` 내부의 `total_money_issued` 직접 수정 로직을 롤백하십시오. 대신 생성된 OMO `Transaction`을 Orchestrator나 전용 Ledger 모듈(`MonetaryLedger` 등)이 사후(Post-Sequence)에 취합하여 Agent의 상태를 안전하게 업데이트하도록 리팩토링하십시오.
- **Config 의존성 강화**: 채권의 액면가(Par Value) 및 OMO 프리미엄/할인율을 `config` 객체를 통해 참조하도록 변경하여 확장성을 확보하십시오.

## 🧠 Implementation Insight Evaluation
- **Original Insight**:
  > "- **Automated M2 Tracking**: `MonetaryTransactionHandler` was updated to automatically track `total_money_issued` and `total_money_destroyed` on the Central Bank agent during OMO, closing a significant M2 leak in audit logs."
- **Reviewer Evaluation**:
  - **평가**: 해당 인사이트는 기능적 버그(M2 누수)를 수정했다는 점에서는 의미가 있으나, 아키텍처 관점에서는 치명적인 기술 부채를 '개선(Automated)'으로 잘못 인식하고 있습니다.
  - 핸들러(Handler)가 도메인 모델(Agent)의 속성을 직접 조작하게 함으로써 Stateless 원칙을 파괴했습니다. 이는 향후 병렬 처리나 트랜잭션 롤백 시 상태 불일치를 유발할 수 있는 잠재적 위험 요소입니다. 따라서 이 조치는 롤백되어야 하며, 올바른 설계에 대한 교훈으로 기록되어야 합니다.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

**Draft Content**:
```markdown
### [WO-FINAL-MACRO-REPAIR] Handler 내 State Mutation 금지 및 Settle-then-Record 원칙
- **현상 (Symptom)**: `MonetaryTransactionHandler` 내부에서 OMO 통화량 조절을 위해 `context.central_bank.total_money_issued` 값을 직접 수정(Mutation)함.
- **원인 (Cause)**: M2 Audit 과정에서의 누수(Leak)를 빠르게 틀어막기 위해, 상태 변경 로직을 가장 접근하기 쉬운 핸들러 단계에 하드코딩함.
- **해결/권장 (Resolution)**: Handler와 Engine은 무조건 Stateless여야 하며 Transaction DTO만 생성해야 함. M2 등 메타 상태의 변경은 생성된 Transaction을 기반으로 Orchestrator의 Post-Sequence 단계나 전용 Ledger에서 일괄 처리(Settle-then-Record)해야 함.
- **교훈 (Lesson)**: 데이터 정합성을 맞추기 위해 아키텍처 경계를 허무는 코드를 작성하면 안 됨. 무상태성(Stateless)을 위반하는 로직은 일시적인 버그 픽스처럼 보일 수 있으나 결국 시스템의 신뢰성과 테스트 안정성을 파괴함.
```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**
- 보안 위반은 없으나, "Settle-then-Record" 아키텍처 원칙을 파괴하고 Handler가 Agent 상태를 직접 수정(Stateless Purity 위반)하도록 변경한 것은 시스템 무결성에 치명적이므로 수정을 요구합니다. 매직 넘버 하드코딩 제거와 함께 처리 바랍니다.