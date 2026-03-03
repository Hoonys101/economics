# Code Review Report

## 1. 🔍 Summary
SagaCaretaker를 도입하여 비활성 Agent가 포함된 고아(Orphaned) Saga를 주기적으로 정리(Sweep)하고 보상 트랜잭션을 트리거하는 가비지 컬렉션 로직을 추가했습니다. 그러나 실제 시스템에서 사용되는 데이터 구조와 Caretaker가 예상하는 인터페이스 간의 치명적인 불일치가 있으며, 예외 처리 미흡으로 인한 무한 루프 취약점과 하드코딩이 발견되었습니다.

## 2. 🚨 Critical Issues
*   **Runtime Crash (Type/Interface Mismatch)**: 
    - `modules/finance/saga/caretaker.py`의 `_extract_participant_ids` 메서드에서 `saga.payload`를 통해 참여자 ID를 추출하려고 시도합니다.
    - 그러나 현재 `SagaOrchestrator`가 관리하고 런타임에 실제로 주입되는 객체는 `HousingTransactionSagaStateDTO`이며, 이 DTO에는 `payload` 속성이 아예 존재하지 않습니다.
    - 이 코드가 실제 환경에 배포되면 `if not saga.payload:` 평가 시 즉시 `AttributeError`를 발생시키며 크래시가 납니다. 단위 테스트가 현실의 구조체 대신 Mock(`SagaStateDTO`) 객체만 사용하여 통과한 'Mock Fantasy'의 전형입니다.
*   **Infinite Loop on Compensation Failure**: 
    - `modules/finance/sagas/orchestrator.py`의 `compensate_and_fail_saga` 내부에서 `handler.compensate_step(saga)` 실행 중 예외가 발생할 경우, 예외만 던지고(raise) `self.active_sagas`에서 해당 Saga를 삭제하지 않습니다.
    - 이로 인해 Saga는 여전히 진행 중인 상태(`PENDING_INSPECTION` 등)로 활성 큐에 남게 되며, 매 Tick마다 Caretaker가 이를 다시 발견하여 보상을 시도하고 다시 예외를 뱉어내는 **무한 오류 루프(Infinite Retry Loop)**에 빠지게 됩니다.
*   **Protocol Duplication**: 
    - `ISagaOrchestrator` 프로토콜이 기존의 `modules/finance/kernel/api.py`와 이번에 신규 추가된 `modules/finance/saga/api.py` 두 곳에 파편화되어 중복 정의되었습니다. Single Source of Truth 원칙에 심각하게 위배됩니다.

## 3. ⚠️ Logic & Spec Gaps
*   **Hardcoded Magic Number (`current_tick=0`)**:
    - `modules/finance/sagas/orchestrator.py` 내부에서 `HousingTransactionSagaHandler`를 인스턴스화할 때 `current_tick=0`을 하드코딩하여 주입했습니다. 이는 Late-Reset Principle 및 Engine Purity를 위반하는 안티 패턴입니다.
*   **Hardcoded Domain Knowledge in Orchestrator**:
    - 제네릭하게 모든 종류의 Saga를 다뤄야 할 `SagaOrchestrator.compensate_and_fail_saga`가 도메인에 종속적인 `HousingTransactionSagaHandler`를 직접 하드코딩하여 생성하고 있습니다. 이는 관심사 분리(Separation of Concerns)를 위반합니다.

## 4. 💡 Suggestions
*   **DTO Interface Unification**: `SagaStateDTO`의 비정형 `payload` 딕셔너리에 의존하는 방식을 버리고, 모든 Saga DTO가 반드시 구현해야 할 `participant_ids: List[AgentID]`와 같은 명시적인 프로토콜을 정의하십시오.
*   **Robust Failure Handling**: `compensate_step`이 실패하더라도, 시스템 안정성을 위해 해당 Saga의 상태를 `FAILED_ROLLED_BACK_ERROR` 같은 터미널 상태로 강제 전환하고 `active_sagas` 큐에서 안전하게 제거하여 무한 루프를 방지하십시오.
*   **Refactor Protocol & Tick Propagation**: `modules/finance/saga/api.py`의 중복된 `ISagaOrchestrator` 정의를 삭제하십시오. 또한 `compensate_and_fail_saga` 서명에 `current_tick: int` 파라미터를 추가하여 하드코딩된 `0`을 제거하십시오.

## 5. 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "Saga Payload Fragmentation: During the caretaker spec design, it was identified that SagaStateDTO.payload is an unstructured dictionary (dict[str, Any]). This presents a structural risk for the Caretaker, which needs to homogeneously extract participant IDs across different saga domains (Housing, Bonds, FX). Decision: A structural mandate is proposed to either enforce a participant_ids field on SagaStateDTO or implement a standard extraction protocol in the repository."
    > "Decoupling State from Execution: The Orchestrator historically acted as both the repository and the executor. By enforcing ISagaRepository and ISagaOrchestrator segregation, we protect the Caretaker from unintentionally triggering side-effects while querying states."
*   **Reviewer Evaluation**: 
    - 원문 인사이트는 `payload` 딕셔너리 사용이 가져오는 잠재적 위험(Fragmentation)을 올바르게 짚어냈습니다.
    - **그러나 가장 중요한 통찰을 놓쳤습니다.** 현재 운영 중인 `HousingTransactionSagaStateDTO`에는 아예 `payload`라는 필드 자체가 없다는 사실을 인지하지 못했습니다. 
    - 인터페이스 분리(Decoupling)에 대한 목적은 좋았으나, 결과적으로 중복된 `ISagaOrchestrator` 프로토콜을 양산하는 부작용을 낳았습니다. Mock에 과도하게 의존한 단위 테스트의 위험성을 교훈으로 추가해야 합니다.

## 6. 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
```markdown
### [Saga Payload Fragmentation & Interface Illusion]
- **현상 (Symptom)**: `SagaCaretaker`가 `SagaStateDTO.payload` 딕셔너리에 의존하여 participant ID를 추출하도록 구현되었으나, 실제 런타임에 주입되는 데이터 구조체(`HousingTransactionSagaStateDTO`)에는 `payload` 속성이 존재하지 않아 크래시(AttributeError)가 발생할 위험이 있었습니다.
- **원인 (Cause)**: 현실의 데이터 구조와 단절된 Mock 객체만을 사용한 단위 테스트(Mock Fantasy)로 인해 타입 불일치를 런타임 이전에 잡아내지 못했습니다. 또한 관심사 분리를 시도하다 `ISagaOrchestrator` 프로토콜이 여러 파일에 중복 정의되는 파편화가 발생했습니다.
- **해결 (Resolution)**: [진행 중] 1) 모든 Saga State DTO가 공통 `participants: List[AgentID]` 필드를 가지도록 기반 구조를 리팩토링합니다. 2) 보상 트랜잭션 실패 시 무한 루프에 빠지지 않도록 터미널 상태 전이 및 큐(Queue) 제거 로직을 강제합니다.
- **교훈 (Lesson)**: 프로토콜과 인터페이스를 설계하고 분리할 때, Mock 객체에 과도하게 의존하지 말고 실제 의존성 사슬에서 데이터 형식이 어떻게 교환되는지 End-to-End Type 검증을 반드시 거쳐야 합니다.
```

## 7. ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**