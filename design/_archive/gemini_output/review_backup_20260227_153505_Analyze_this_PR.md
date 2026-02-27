# Code Review Report

## 1. 🔍 Summary
Central Bank의 LLR(최종대부자) 동작 등에서 발생하는 통화 생성/소멸 내역이 전역 원장(WorldState)에 누락되는 문제를 해결하기 위해 `CentralBankSystem`에 트랜잭션 리스트 참조를 주입(Injection)하는 패턴을 적용했습니다. 또한 M2 통화량 계산 시 시스템 계정(Public Manager 등)을 명시적으로 제외하고, 채권 상환 시 원금 부분만 통화량 감소로 정확히 인식하도록 원장 회계 로직을 개선했습니다.

## 2. 🚨 Critical Issues
*   **없음.** 하드코딩된 API 키, 외부 URL, 시스템 파괴 요소나 심각한 돈 복사 버그(Magic Creation) 등 즉시 수정을 요하는 치명적인 결함은 발견되지 않았습니다.

## 3. ⚠️ Logic & Spec Gaps
*   **Performance & Type Smell (`simulation/world_state.py`)**: 
    ```python
    holder_id_str = str(holder.id)
    if holder_id_str == str(ID_CENTRAL_BANK) or holder_id_str == str(ID_PUBLIC_MANAGER) or holder_id_str == str(ID_SYSTEM):
    ```
    이 로직은 매 틱마다 모든 에이전트를 대상으로 실행되는 통화량 계산 루프 내부에 위치하므로 잦은 `str()` 캐스팅이 성능 저하를 유발할 수 있습니다. ID의 타입 불일치를 매번 캐스팅으로 해결하기보다는, 에이전트 초기화 시점에 ID 타입을 정규화하거나, `SYSTEM_SINK_IDS = {str(ID_CENTRAL_BANK), str(ID_PUBLIC_MANAGER), ...}` 형태의 Set을 캐싱하여 `str(holder.id) in SYSTEM_SINK_IDS` 방식으로 비교하는 것이 바람직합니다.
*   **Type Casting Risk (`modules/government/components/monetary_ledger.py`)**: 
    ```python
    amount = float(repayment_details["principal"])
    ```
    `SettlementSystem`에서는 `amount`를 엄격하게 `int`로 강제하고(`FloatIncursionError` 발생) 있습니다. Ledger 단에서 데이터를 `float`로 캐스팅할 경우 원장 내부 계산용으로는 무방할 수 있으나, 시스템 전반의 정수 기반 회계(Integer-based accounting) 원칙과 충돌할 잠재적 위험이 있습니다.

## 4. 💡 Suggestions
*   **Transaction Injection Purity (`simulation/systems/central_bank_system.py`)**: 
    `CentralBankSystem`이 `world_state.transactions` 리스트를 직접 주입받아 `append`를 수행하는 방식은 당장의 버그를 고치는 데 유효하지만, 엔진 클래스가 글로벌 상태 리스트를 직접 Mutate하게 만들어 캡슐화와 Stateless 원칙을 다소 약화시킵니다. 장기적으로는 `EventBus`를 통해 `TransactionCreatedEvent`를 발행(Publish)하고, 이를 `WorldState`나 `Ledger`가 구독하여 큐에 쌓는 이벤트 주도(Event-Driven) 방식의 리팩토링을 고려하십시오.
*   **Test Mock Purity (`tests/unit/test_tax_collection.py`)**: 
    `MockSettlementSystem`에서 반환하는 트랜잭션 객체를 `MagicMock()`으로 생성하여 그대로 반환하고 있습니다. `TESTING_STABILITY.md`의 권고사항에 따라 DTO의 무결성 검증을 위해 `MagicMock`보다는 실제 `Transaction` DTO 인스턴스를 활용하여 테스트의 신뢰도를 높이는 것을 제안합니다.

## 5. 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > **1. Ledger Synchronization via Transaction Injection**
    > The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. These operations used the `SettlementSystem` but failed to bubble up the resulting transactions to the `WorldState` transaction queue, which is the single source of truth for the `MonetaryLedger`.
    > To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`. By injecting the `WorldState.transactions` list into the `CentralBankSystem` upon initialization, we enable it to directly append side-effect transactions (like LLR minting) to the global ledger. This ensures that every penny created or destroyed is visible to the audit system, regardless of where in the call stack the operation occurred.
    >
    > **2. Orchestrator Phase Consolidation**
    > We removed the redundant `Phase_MonetaryProcessing` from the `TickOrchestrator`. Previously, this phase attempted to process transactions independently, leading to potential double-counting or race conditions with `Phase3_Transaction`. By consolidating all transaction processing logic (including `MonetaryLedger` updates) into `Phase3_Transaction`, we ensure a strictly linear and atomic execution flow: Execute -> Verify -> Record.
    >
    > **3. M2 Perimeter Harmonization**
    > We refined the definition of M2 (Total Money Supply) in `WorldState.calculate_total_money`. The `PublicManager` (ID 4) and System Agent (ID 5) are now explicitly excluded from the M2 calculation, aligning them with the Central Bank (ID 0) as "System Sinks". This prevents money held by these administrative agents (e.g., from escheatment) from being counted as circulating supply, eliminating "phantom" M2 fluctuations. ID comparisons were also robustified using string conversion to preventing type mismatch errors.
    >
    > **4. Bond Repayment Logic**
    > We enhanced the `MonetaryLedger` to respect the split between Principal and Interest during bond repayments. Previously, the ledger treated the entire repayment (Principal + Interest) as money destruction (Contraction). Now, if metadata is available, only the Principal portion is counted as M0/M2 destruction, while Interest is treated as a transfer to the System (which may or may not be recycled), aligning the ledger with standard accounting practices where only asset redemption contracts the supply.

*   **Reviewer Evaluation**: 
    매우 훌륭한 인사이트 보고서입니다. "Ghost money" 생성의 시스템적 근본 원인을 정확히 진단하고, 이를 어떠한 패턴(Transaction Injection)으로 파훼했는지 논리적으로 서술하였습니다. 특히 채권의 원금과 이자를 분리하여 원장 파괴 및 통화량 산정을 정밀화한 대목은 경제 시뮬레이션의 정합성을 한 단계 높이는 훌륭한 발견입니다. 다만, "Transaction Injection Pattern"이 리스트 직접 주입 방식이라는 점에서 시스템 간 강결합(Tight Coupling)이라는 기술 부채를 남길 수 있음에 유의해야 합니다.

## 6. 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md` (또는 해당하는 기술 부채/인사이트 원장 파일)
*   **Draft Content**:
    ```markdown
    ### [WO-WAVE5] System Agent Transaction Synchronization (Ghost Money Prevention)
    *   **현상 (Symptom)**: Central Bank 등 시스템 에이전트가 LLR(최종대부자) 역할 수행 시 발생하는 자금의 발행 및 소각 내역이 M2(총 통화량) 감사 계산에 누락되는 "Ghost Money" 현상 발생.
    *   **원인 (Cause)**: 암묵적 시스템 오퍼레이션이 `SettlementSystem`을 호출하여 잔고를 변경하기는 하나, 생성된 트랜잭션이 `WorldState`의 글로벌 트랜잭션 큐로 반환(Bubble Up)되지 않아 `MonetaryLedger`의 감사망을 회피함.
    *   **해결 (Resolution)**: `CentralBankSystem` 초기화 시 `WorldState.transactions` 리스트의 참조를 직접 주입(Transaction Injection Pattern)하여, 백그라운드에서 발생하는 모든 통화 생성/소멸 트랜잭션을 글로벌 큐에 명시적으로 `append` 하도록 파이프라인 수립. 또한 이중 처리를 방지하기 위해 `Phase_MonetaryProcessing`을 폐기하고 `Phase3_Transaction`으로 결산 로직을 병합함.
    *   **교훈 (Lesson Learned)**: 상태 변경(Agent의 잔고 업데이트)과 이벤트 기록(Global Transaction Queue 추가)은 반드시 원자적(Atomic)으로 이루어져야 함. 프론트엔드 에이전트 동작뿐만 아니라, 백그라운드 엔진(Stateless Engine)에 의한 시스템적 자금 이동 시에도 전역 원장과의 동기화 파이프라인이 필수적임. (추후 리스트 직접 주입 방식은 Event Bus 패턴으로 결합도를 낮추는 리팩토링 검토 필요).
    ```

## 7. ✅ Verdict
**APPROVE**
(제시된 PR은 로직 오류 및 보안 문제를 포함하지 않으며, 요구사항에 부합하는 인사이트 문서 작성을 완료했습니다. ⚠️ 지적된 Type Smell 및 캐스팅 이슈는 다음 리팩토링 페이즈에 반영할 것을 권장합니다.)