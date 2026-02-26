I will search for the string `money_creation` to identify its source and find where it is missing a handler, and then I will examine the `calculate_total_money` logic and its interaction with `MonetaryLedger` to understand the M2 discrepancy.

I will read the `simulation/systems/settlement_system.py` file to understand how `money_creation` transactions are generated, and also examine `simulation/systems/transaction_processor.py` to determine why it lacks a handler for this transaction type.

I've identified that `SettlementSystem` generates `money_creation` transactions in `create_and_transfer`, and the `diagnostic_refined.md` error suggests a missing handler in `TransactionProcessor`. I will now examine `simulation/systems/transaction_processor.py` to confirm.

In `TransactionProcessor.execute`, `money_creation` transactions log a warning due to a missing handler. The M2 discrepancy, where `Current` exceeds `Expected`, suggests money is being added to agent balances without being recorded in `MonetaryLedger`. While `SettlementSystem` appears to record expansions, I suspect `Bootstrapper` or other systems might be bypassing this. I'll now check `simulation/systems/bootstrapper.py` to see how initial wealth is distributed and if it's properly recorded.

`Bootstrapper` uses `create_and_transfer`, which should record expansions in `MonetaryLedger`. In `initializer.py`, `baseline_money_supply` is set to `calculate_total_money()` *after* `Bootstrapper` runs, and `expected_m2` is initialized to this value. However, `calculate_total_money` reads from `monetary_ledger.get_total_m2_pennies`, which in turn calls `settlement_system.get_total_m2_pennies`. I'll now examine `simulation/systems/settlement_system.py` to understand how it calculates the total M2 and if this circularity is problematic.

I'll look for `get_total_m2_pennies` in `simulation/systems/settlement_system.py`.

I'll examine `simulation/systems/settlement_system.py` starting at line 192.

The M2 calculation appears correct, but a significant drift exists. `SettlementSystem.create_and_transfer` records expansions if the deposit succeeds, and since it involves minting, "insufficient funds" shouldn't occur. I suspect the discrepancy might lie in loan-related deposit creations, so I'll investigate where `record_credit_expansion` is invoked.

I've noticed `record_credit_expansion` is only mentioned in tests, specs, and insights, suggesting it's not being called. I'll now check for calls to `create_and_transfer` and `record_monetary_expansion` to see how money expansion is actually handled.

The M2 delta arises because transfers between excluded (CB, Bank) and included (HH, Firm, Gov) agents aren't being tracked as expansions/contractions in `MonetaryLedger`, even though they change the actual M2. Additionally, `SettlementSystem.create_and_transfer` generates `money_creation` transactions that `TransactionProcessor` can't handle because they're not marked as `executed`, unlike the `monetary_expansion` transactions from `MonetaryLedger`. I'll now further examine `simulation/systems/settlement_system.py` to see if these `money_creation` transactions are being added to `state.transactions`.

I haven't found where `create_and_transfer` or `mint_and_distribute` add transactions to the state. `SettlementSystem` doesn't have access to `SimulationState`, but it is used by handlers. I suspect handlers call these methods and add the returned transaction to `context.transaction_queue`, which is later added to `state.transactions`. I'll examine `modules/finance/system.py` to see how it uses `create_and_transfer`.

In `FinanceSystem.py`, `record_monetary_expansion` is called during `issue_treasury_bonds` if the buyer is a system agent. However, for `process_loan_application`, the code suggests that `Bank.grant_loan` handles the expansion to avoid double counting. I'll now examine `simulation/bank.py` to verify this.

`Bank.grant_loan` and `Bank.repay_loan` call `record_monetary_expansion` and `record_monetary_contraction`, respectively. However, `Bank.run_tick` calls `FinanceSystem.service_debt`, which uses `debt_servicing_engine.service_all_debt` to generate transactions. I suspect these transactions, like `interest_payment`, might increase M2 without being recorded in the `MonetaryLedger`, causing a delta. I'll check `simulation/systems/handlers/financial_handler.py` to see how these transactions are handled.

`FinancialTransactionHandler` uses `transfer` without notifying `MonetaryLedger`. This causes an M2 discrepancy when a `Bank` (excluded from M2) pays interest to a `Household` (included in M2), as the actual M2 increases but the expected value remains unchanged. While Firm-to-Household transfers like dividends are M2-neutral, I need to verify if the Government is included in M2 and confirm which agents are excluded. I'll check `modules/system/constants.py` to clarify `NON_M2_SYSTEM_AGENT_IDS` and if `ID_BANK` is among them.

`ID_GOVERNMENT` is excluded from M2, making taxes a contraction and welfare an expansion. Massive M2 drift occurs because `SettlementSystem.transfer` doesn't track these boundary crossings, and handlers for tax, welfare, and interest payments fail to notify `MonetaryLedger`. Additionally, `money_creation` transactions, generated as logs by `SettlementSystem.create_and_transfer`, lack a handler in `TransactionProcessor`. I'll mark these as `executed` to avoid warnings. Now, I'll examine `simulation/systems/central_bank_system.py` to see how it uses `create_and_transfer` and why these transactions end up in `state.transactions`.

`CentralBankSystem.mint_and_transfer` correctly records expansions in the `MonetaryLedger` via `create_and_transfer`, but adding the resulting `money_creation` transaction to `self.transactions` without an `executed: True` flag causes `TransactionProcessor` to log warnings. To investigate the M2 drift, I'll now examine `SettlementSystem.transfer` to see if routine transfers are failing to account for expansions.

I'll search for `def transfer` in `SettlementSystem.py`.

I'll read `simulation/systems/settlement_system.py` starting at line 550.

`SettlementSystem.transfer` fails to record expansions, causing routine M2-boundary-crossing transfers, like Bank-to-Household interest, to go untracked. This explains the ~1.6B delta at Tick 22, as cumulative unrecorded expansions (interest, government spending) outweigh contractions (taxes). I must now verify if the Taxation System, Welfare Manager, and Bank (for interest) are explicitly calling `record_monetary_expansion` or `contraction`, as suggested by insight reports. I'll start by checking `modules/government/taxation/system.py`.

I'll read `modules/government/taxation/system.py`.

`TaxationSystem` calculates intents without ledger recording, and `FinancialTransactionHandler` fails to call `record_monetary_contraction` for tax transactions. I'll now search for `record_monetary_expansion` in `modules/government` to see how welfare payments are handled.

# Technical Report: Monetary Anomaly Deep Dive (Phase 33)

## Executive Summary
최근 `diagnostic_refined.md` 분석 결과, 통화 시스템의 무결성이 두 가지 요인에 의해 훼손되고 있음을 확인했습니다. 첫째, `SettlementSystem`에서 생성하는 화폐 발행 영수증(`money_creation`)에 대한 핸들러가 누락되어 불필요한 경고가 발생하고 있습니다. 둘째, M2 통화량 경계(Boundary)를 넘나드는 일상적인 이체(이자 지급, 복지 지출, 세금 징수)가 `MonetaryLedger`에 기록되지 않아, 시간이 지남에 따라 실제 통화량과 장부상 기대 통화량 사이에 대규모 불일치(Tick 60 기준 약 57억 페니)가 발생하고 있습니다.

## Detailed Analysis

### 1. 'money_creation' 트랜잭션 핸들러 누락
- **Status**: ⚠️ Partial (기능은 동작하나 로깅/핸들링 미흡)
- **Evidence**: `simulation/systems/settlement_system.py:L661-675` 및 `simulation/systems/transaction_processor.py:L217`
- **Root Cause**: 
    - `SettlementSystem.create_and_transfer`는 화폐 발행 시 `money_creation` 타입의 트랜잭션을 생성하여 반환합니다.
    - `CentralBankSystem` 등 호출자는 이를 전역 `transactions` 목록에 추가하지만, 해당 트랜잭션은 이미 자금 이동(`_deposit`)이 완료된 "영수증" 성격임에도 불구하고 `executed: True` 플래그가 설정되어 있지 않습니다.
    - 결과적으로 `TransactionProcessor`가 매 틱마다 이들을 다시 처리하려 시도하고, 전용 핸들러가 없어 경고를 발생시킵니다.
- **Notes**: 이 현상은 로깅 노이즈를 유발할 뿐만 아니라, 향후 트랜잭션 재처리 로직 도입 시 중복 입금의 위험을 내포하고 있습니다.

### 2. M2 통화량 불일치 (M2 Leakage)
- **Status**: ❌ Missing (M2 경계 횡단 이체 추적 로직 부재)
- **Evidence**: `simulation/systems/settlement_system.py:L555-600` (`transfer` 메서드)
- **Root Cause**:
    - **M2 정의 불일치**: 현재 시스템에서 가계(Household)와 기업(Firm)은 M2 포함 대상이지만, 은행(Bank), 중앙은행(CB), 정부(Government)는 제외 대상입니다. (`modules/system/constants.py:NON_M2_SYSTEM_AGENT_IDS`)
    - **추적 누락**: `SettlementSystem.transfer`는 단순한 제로섬 이체만 수행하며, 이체가 M2 경계를 넘는지(예: 은행 지준금 -> 가계 예금) 확인하지 않습니다. 
    - **주요 누락 경로**:
        1. **이자 지급**: `Bank` -> `Household` (M2 외부에서 내부로 유입 -> unrecorded expansion)
        2. **복지/인프라 지출**: `Government` -> `Household/Firm` (M2 외부에서 내부로 유입 -> unrecorded expansion)
        3. **세금 징수**: `Household/Firm` -> `Government` (M2 내부에서 외부로 유출 -> unrecorded contraction)
- **Quantification**: Tick 22에서 발생한 약 16.6억 페니의 델타는 시뮬레이션 초기에 발생한 대규모 정부 지출 및 은행 이자 지급이 장부에 반영되지 않았음을 의미합니다. Tick 1의 음수 델타(-4.19억)는 초기 부동산 매각(`HH` -> `Gov`)에 따른 M2 소멸이 기록되지 않아 발생한 현상입니다.

## Risk Assessment
- **통화 정책 왜곡**: 장부상 통화량(`Expected M2`)이 실제 통화량보다 훨씬 낮게 보고됨에 따라, 중앙은행 AI가 과도한 긴축 또는 완화 정책을 펼칠 위험이 있습니다.
- **데이터 오염**: 통계 및 분석 리포트에서 M2 Leakage가 지속적으로 증가하여 장기 시뮬레이션의 신뢰도가 하락합니다.
- **시스템 불안정**: 통화량 불일치가 누적되면 이자율 계산 및 인플레이션 심리 모델에 부정적인 영향을 미쳐 경제 붕괴를 초래할 수 있습니다.

## Conclusion & Action Items

통화 시스템의 무결성을 회복하기 위해 다음과 같은 기술적 수정을 제안합니다 (Mission: `WO-IMPL-FINANCIAL-INTEGRITY-FIX`).

### 1. `SettlementSystem`의 M2 인지형 이체 구현 (High Priority)
- `transfer` 메서드 내부에서 `debit_agent`와 `credit_agent`의 M2 포함 여부를 체크하는 로직을 추가해야 합니다.
- **Rule**: 
    - `Non-M2` -> `M2` 이체 시: `monetary_ledger.record_monetary_expansion` 자동 호출.
    - `M2` -> `Non-M2` 이체 시: `monetary_ledger.record_monetary_contraction` 자동 호출.
- 이를 통해 개별 핸들러(세금, 복지 등)를 수정하지 않고도 시스템 전반의 통화량 정합성을 보장할 수 있습니다.

### 2. 발행/소멸 영수증 처리 최적화
- `SettlementSystem._create_transaction_record`에서 `transaction_type`이 `money_creation` 또는 `money_destruction`인 경우, `metadata`에 `executed: True`를 강제 설정하도록 수정하십시오.
- `TransactionProcessor`에 해당 타입들을 명시적인 No-Op(무연산) 타입으로 등록하여 경고를 제거하십시오.

### 3. 초기 통화량(Baseline) 검증 강화
- `SimulationInitializer`에서 `set_expected_m2` 호출 시점과 `calculate_total_money`의 동기화 순서를 재검토하여 Tick 1의 델타 발생을 차단해야 합니다.

---
**Reporter**: Gemini-CLI Subordinate
**Mission Authority**: Antigravity (The Architect)
**Status**: Investigation Complete. Awaiting Implementation Mission Dispatch.