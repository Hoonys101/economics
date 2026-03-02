I need to read the PR diff file to analyze the changes. I will start by checking the `pr_diff.patch` file.
# 🐙 Gemini CLI System Prompt: Git Reviewer - Code Review Report

## 🔍 Summary
*   **Ledger Sync**: 주입형 패턴(Transaction Injection Pattern)을 도입하여, Central Bank 등의 시스템 동작으로 발생한 트랜잭션이 누락 없이 전역 큐에 기록되도록 수정 (M2 누수 해결).
*   **M2 Perimeter**: 시중 통화량(M2) 계산 시 행정적 목적의 에이전트(`ID_PUBLIC_MANAGER`, `ID_SYSTEM`)를 명시적으로 제외하여 통화량 집계의 정확도를 높임.
*   **Bond Repayment Accuracy**: 채권 상환 시 전체 금액이 아닌 원금(Principal)만을 통화량 수축으로 인식하도록 `MonetaryLedger` 회계 로직 개선.

## 🚨 Critical Issues
*   없음 (None). 하드코딩된 경로, 외부 API Key 위반, 혹은 자의적인 돈 복사(Magic Creation) 등 시스템 파괴 로직은 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps
*   없음 (None). `Phase_MonetaryProcessing` 단계를 삭제하고 관련된 처리 로직을 `Phase3_Transaction`으로 일원화한 것은 레이스 컨디션을 방지하고 Zero-Sum 무결성을 강화하는 긍정적인 변경점입니다.

## 💡 Suggestions
*   **Type Hint Inconsistency**: `simulation/systems/central_bank_system.py`의 `CentralBankSystem.mint` 및 `transfer_and_burn` 시그니처에서 `amount: float` 타입을 사용하고 있습니다. 반면, 이번 변경 사항의 주석에서 확인된 `SettlementSystem.transfer`는 파라미터가 `float`일 경우 `FloatIncursionError`를 강제로 발생시킵니다. 현재 호출 컨텍스트상에서 버그를 일으키지 않더라도, 향후 타입 관련 혼동을 피하기 위해 `CentralBankSystem`의 `amount` 파라미터 타입 힌트도 `int`로 일치시키는 것을 권장합니다.

## 🧠 Implementation Insight Evaluation
**Original Insight**:
> "The root cause of the M2 leakage was identified as 'ghost money' creation during implicit system operations... To fix this, we implemented a Transaction Injection Pattern for the CentralBankSystem... We refined the definition of M2... The PublicManager (ID 4) and System Agent (ID 5) are now explicitly excluded... We enhanced the MonetaryLedger to respect the split between Principal and Interest during bond repayments."

**Reviewer Evaluation**:
매우 우수한 수준의 통찰(Insight)입니다. 시스템 에이전트의 내부 동작으로 생성된 트랜잭션이 전역 원장(`WorldState`)으로 버블링되지 않아 발생하는 'Ghost Money' 현상의 원인을 정확히 짚어냈습니다. 기존 의존성을 복잡하게 얽지 않고 `transactions` 리스트 객체를 주입(Injection)하여 원장을 동기화한 해결책은 매우 실용적이며 SSoT(Single Source of Truth) 원칙을 깔끔하게 준수합니다. 아울러 채권의 원금과 이자를 분리하여 통화량 수축을 정확히 집계한 점은 Financial Integrity 측면에서 훌륭한 진전입니다.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (또는 중앙 지식/에러 베이스 파일)

**Draft Content**:
```markdown
### [WO-WAVE5-MONETARY-FIX] Ghost Money 현상 방지 및 System Sinks 처리 원칙
*   **현상 (Symptom)**: Central Bank(LLR 등)와 같은 시스템 에이전트의 암시적 동작으로 생성된 통화가 전역 트랜잭션 큐에 기록되지 않아, M2(총 통화량) 집계 시 누수(Ghost Money)가 발생하는 현상.
*   **원인 (Cause)**: `SettlementSystem`을 직접 호출하는 시스템 계층의 동작 결과가 `WorldState.transactions`로 버블링되지 않음. 추가로 행정 계좌(Public Manager, System 등)의 보유 잔고가 시중 유통 통화량에 오분류됨.
*   **해결 (Resolution)**: 
    1. **Transaction Injection**: 시스템 에이전트(`CentralBankSystem` 등) 초기화 시 전역 `transactions` 리스트를 주입받아, 자체 발생한 사이드 이펙트 트랜잭션을 직접 기록하도록 아키텍처 개선.
    2. **System Sink Exclusion**: `WorldState.calculate_total_money` 로직에서 M2 산출 시 `ID_PUBLIC_MANAGER`, `ID_SYSTEM` 계좌를 명시적인 'System Sink'로 판단하여 제외 처리.
    3. **Principal/Interest Split**: 채권 상환(bond_repayment) 트랜잭션 발생 시, `MonetaryLedger`에서 메타데이터를 확인하여 이자가 아닌 원금(Principal)에 해당하는 금액만 통화량 수축(Destruction)으로 계산.
*   **교훈 (Lesson Learned)**: 금융 무결성(Financial Integrity)을 보장하기 위해서는 시스템의 모든 가치 이동이 예외 없이 하나의 전역 큐(SSoT)를 거치도록 설계해야 하며, 화폐의 종착점인 'System Sinks'는 시중 유동성 계산에서 철저하게 분리되어야 한다.
```

## ✅ Verdict
**APPROVE**
(모든 변경 사항이 명세와 SSoT 원칙에 부합하게 구현되었으며, 보안/위생 점검 및 인사이트 보고 요건을 완벽히 충족했습니다.)