### 1. 🔍 Summary
이번 PR은 누락되었던 중앙은행(CentralBank)의 통화 발행/회수 트랜잭션을 WorldState의 글로벌 트랜잭션 큐에 직접 주입(Injection)하는 패턴을 도입하여 M2 통화량의 무결성을 확보하고, 불필요한 Phase를 통합 및 채권 상환 로직을 회계 기준에 맞게 개선한 변경입니다.

### 2. 🚨 Critical Issues
- **None**: 직접적인 보안 위반이나 치명적인 돈 복사(Magic Creation) 버그, 악의적인 외부 하드코딩은 발견되지 않았습니다.

### 3. ⚠️ Logic & Spec Gaps
- **Test Hardcoding**: `tests/unit/modules/government/components/test_monetary_ledger_expansion.py` 파일 내에 `tx.buyer_id = "4" # ID_PUBLIC_MANAGER`와 같이 매직 스트링이 하드코딩되어 있습니다. `modules.system.constants.ID_PUBLIC_MANAGER`를 import하여 `str(ID_PUBLIC_MANAGER)`로 명시적으로 사용하는 것이 안전합니다. ("작은 하드코딩 하나도 놓치지 마십시오" 지침 위반)
- **Mock Purity Violation**: `tests/unit/test_tax_collection.py` 내부 `MockSettlementSystem.transfer`에서 `tx = MagicMock()`을 반환하도록 설정되었습니다. DTO(Transaction)를 테스트에서 다룰 때 원시값이 아닌 `MagicMock` 객체를 그대로 반환하게 되면, 향후 직렬화나 엄격한 타입 체킹 시 `TESTING_STABILITY`를 위반하여 예기치 않은 에러가 발생할 수 있습니다. `MagicMock` 대신 실제 `Transaction` 인스턴스나 상태만 저장하는 단순 데이터 클래스(Dummy DTO)를 반환해야 합니다.

### 4. 💡 Suggestions
- `CentralBankSystem`의 `mint_money` 및 `transfer_and_burn` 로깅 시 `amount:.2f` 포맷을 사용하고 있습니다. `SettlementSystem.transfer`는 엄격하게 `int` 단위(혹은 최소 화폐 단위)를 요구하여 float 유입 시 `FloatIncursionError`를 발생시키므로, `amount`가 항상 정수형으로 보장된다면 로깅 포맷도 불필요한 소수점 표기 대신 정수형에 맞게 통일하는 것이 코드 혼선을 방지할 수 있습니다.

### 5. 🧠 Implementation Insight Evaluation
- **Original Insight**:
> # WO-WAVE5-MONETARY-FIX: M2 Integrity & Audit Restoration
> 
> ## Architectural Insights
> 
> ### 1. Ledger Synchronization via Transaction Injection
> The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. These operations used the `SettlementSystem` but failed to bubble up the resulting transactions to the `WorldState` transaction queue, which is the single source of truth for the `MonetaryLedger`.
> 
> To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`. By injecting the `WorldState.transactions` list into the `CentralBankSystem` upon initialization, we enable it to directly append side-effect transactions (like LLR minting) to the global ledger. This ensures that every penny created or destroyed is visible to the audit system, regardless of where in the call stack the operation occurred.
>
> ### 2. Orchestrator Phase Consolidation
> We removed the redundant `Phase_MonetaryProcessing` from the `TickOrchestrator`. Previously, this phase attempted to process transactions independently, leading to potential double-counting or race conditions with `Phase3_Transaction`. By consolidating all transaction processing logic (including `MonetaryLedger` updates) into `Phase3_Transaction`, we ensure a strictly linear and atomic execution flow: Execute -> Verify -> Record.
>
> ### 3. M2 Perimeter Harmonization
> We refined the definition of M2 (Total Money Supply) in `WorldState.calculate_total_money`. The `PublicManager` (ID 4) and System Agent (ID 5) are now explicitly excluded from the M2 calculation, aligning them with the Central Bank (ID 0) as "System Sinks". This prevents money held by these administrative agents (e.g., from escheatment) from being counted as circulating supply, eliminating "phantom" M2 fluctuations. ID comparisons were also robustified using string conversion to preventing type mismatch errors.
>
> ### 4. Bond Repayment Logic
> We enhanced the `MonetaryLedger` to respect the split between Principal and Interest during bond repayments. Previously, the ledger treated the entire repayment (Principal + Interest) as money destruction (Contraction). Now, if metadata is available, only the Principal portion is counted as M0/M2 destruction, while Interest is treated as a transfer to the System (which may or may not be recycled), aligning the ledger with standard accounting practices where only asset redemption contracts the supply.

- **Reviewer Evaluation**:
  작성된 인사이트는 시스템의 "Ghost Money" 현상에 대한 원인 분석과 **Transaction Injection Pattern**이라는 구체적인 해결책을 명확히 제시하고 있습니다. 또한 M2 산정 범위(`ID_PUBLIC_MANAGER`, `ID_SYSTEM` 제외) 변경과 채권 원금/이자 분리에 대한 회계적 관점의 개선도 잘 담겨 있습니다.
  다만, 테스트 코드 작성 과정에서 DTO에 `MagicMock`을 주입하는 안티패턴에 대한 기술적 반성(Testing Hygiene)이 누락되어 있습니다. 이 부분을 보강하여 매뉴얼화하는 것이 향후 테스트 안정성 확보에 기여할 것입니다.

### 6. 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Draft Content**:
```markdown
### [WO-WAVE5-MONETARY-FIX] M2 Integrity Architecture & DTO Mocking Anti-Pattern

- **현상 (Symptom)**: 
  1. 중앙은행(CentralBank)의 묵시적 통화 발행(LLR 등)이 글로벌 트랜잭션 큐에 기록되지 않아 M2 지표와 실제 통화량 간 불일치(Ghost Money) 발생.
  2. 세금 징수 테스트 등에서 `SettlementSystem.transfer`가 실제 Transaction DTO 대신 `MagicMock`을 반환하여 잠재적 테스트 불안정성 야기.
- **원인 (Cause)**: 
  1. `CentralBankSystem`이 `SettlementSystem`만 호출하고 생성된 트랜잭션을 `WorldState.transactions`에 버블링하지 않음.
  2. 테스트 편의성을 이유로 DTO 객체를 원시 속성이 없는 `MagicMock`으로 단순 대체함.
- **해결 (Solution)**: 
  1. **Transaction Injection Pattern** 적용: `CentralBankSystem` 초기화 시 `WorldState.transactions` 리스트의 참조를 주입하여, 내부 조작 시 직접 트랜잭션을 append 하도록 수정.
  2. 불필요한 `Phase_MonetaryProcessing`을 삭제하고 `Phase3_Transaction`으로 트랜잭션 처리를 단일화하여 원자성 확보.
- **교훈 (Lesson Learned)**: 
  - 통화 발행과 소각을 포함한 모든 상태 변경은 반드시 단일 Source of Truth (WorldState Transaction Queue)를 거치도록 아키텍처를 설계해야 한다 (Double-Entry Purity). 
  - 단위 테스트에서 DTO를 반환하는 의존성을 Mocking할 때는 `MagicMock` 반환을 지양하고, 실제 DTO 인스턴스 또는 원시값을 온전히 가진 명시적 테스트 픽스처를 반환하도록 하여 `TESTING_STABILITY` 위반을 차단해야 한다.
```

### 7. ✅ Verdict
- **REQUEST CHANGES (Hard-Fail)**

**사유**:
기능적, 아키텍처적 개선 방향(M2 정합성 확보, Transaction Injection)은 훌륭하나, `tests/unit/test_tax_collection.py`에서 `MagicMock`을 Transaction DTO로서 그대로 반환하는 `TESTING_STABILITY` 가이드라인 위반 사항과, `test_monetary_ledger_expansion.py` 내의 `ID_PUBLIC_MANAGER` 매직 스트링("4") 하드코딩이 발견되었습니다. 무결성 및 테스트 안정성 확보를 위해 해당 부분 수정 후 다시 리뷰를 요청해주시기 바랍니다.