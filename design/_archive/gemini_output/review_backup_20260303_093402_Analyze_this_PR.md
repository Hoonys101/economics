### 1. 🔍 Summary
`SagaCaretaker`를 도입하여 비활성 에이전트가 포함된 고아(Orphaned) Saga를 식별 및 정리하고, 보상 트랜잭션 중 발생하는 예외가 무한 루프를 유발하지 않도록 `SagaOrchestrator`의 롤백 및 상태 정리 로직을 강화했습니다.

### 2. 🚨 Critical Issues
- **Breaking API Change (`SagaStateDTO`)**: `modules/finance/api.py`의 `SagaStateDTO`는 `@dataclass(frozen=True)`입니다. 기본값(Default value) 지정 없이 `participant_ids: List[int]` 필드를 중간에 추가하면, 시스템 내에서 기존 방식대로 `SagaStateDTO`를 인스턴스화하던 모든 코드(레거시 및 테스트)에서 파라미터 누락으로 인한 생성 에러(`TypeError`)가 발생합니다.
- **Unsafe Casting (`HousingTransactionSagaStateDTO`)**: `participant_ids` 프로퍼티에서 `int(self.buyer_context.household_id)`를 실행할 때 `try-except` 블록이 없습니다. 만약 데이터에 잘못된 타입이 있거나 변환할 수 없는 형태일 경우 `ValueError`가 발생하여 `Caretaker` 전체의 순회 로직이 중단될 위험이 있습니다. (Orchestrator의 기존 `process_sagas`에서는 해당 변환 시 안전하게 예외 처리를 하고 있었습니다.)

### 3. ⚠️ Logic & Spec Gaps
- **Duct-Tape Duck Typing (Vibe Check Fail)**: `caretaker.py`에서 상태값을 가져오기 위해 `getattr(saga, "state", getattr(saga, "status", None))`와 같이 중첩된 임시방편 코드를 사용하고 있습니다. 이는 명확한 인터페이스 기반 접근을 위반하는 전형적인 '바이브 코딩'이며, 인사이트 문서에서 주장한 "DTO Interface Unification(인터페이스 통일)"과 정면으로 모순됩니다.
- **Test vs Production Mismatch**: 테스트는 `state` 필드를 가진 `SagaStateDTO`를 사용하고 실제 프로덕션은 `status` 필드를 가진 `HousingTransactionSagaStateDTO`를 사용하고 있습니다. 위와 같은 Duck Typing 우회 코드는 이 두 구조적 차이를 덮기 위해 추가된 불건전한 해결책입니다.

### 4. 💡 Suggestions
- **True Protocol Unification**: 두 DTO 클래스가 공통적으로 구현하는 `ISagaState` Protocol을 새롭게 정의하십시오. 이 Protocol은 `status` (또는 `state` 중 하나로 통일)와 `participant_ids` 프로퍼티를 명시해야 합니다.
- **Safe Type Conversion**: `HousingTransactionSagaStateDTO.participant_ids` 프로퍼티 내의 `int()` 캐스팅 로직에 `ValueError`, `TypeError`에 대한 예외 처리를 추가하여 안전한 리스트 반환을 보장하십시오.
- **Default Factory**: `SagaStateDTO`에 새 필드를 추가할 때는 기존 인스턴스화의 호환성을 위해 `participant_ids: List[int] = field(default_factory=list)` 형식으로 기본값을 부여하십시오.

### 5. 🧠 Implementation Insight Evaluation
- **Original Insight**:
  > - **Saga Payload Fragmentation & Interface Illusion**: During the initial caretaker design, `SagaCaretaker` mistakenly relied on an unstructured `payload` dictionary to extract participant IDs. However, the runtime DTO `HousingTransactionSagaStateDTO` lacks a `payload` attribute entirely, which would have caused an `AttributeError` crash. This highlighted the dangers of "Mock Fantasy" - where unit tests pass purely because the mock objects possess attributes that the real production objects do not.
  > - **DTO Interface Unification**: To resolve the structural mismatch and ensure type safety, `SagaStateDTO` and `HousingTransactionSagaStateDTO` were unified to implement a `participant_ids` property, guaranteeing homogeneous extraction.
  > - **Robust Failure Handling**: The `compensate_and_fail_saga` process in the orchestrator lacked proper state management when the inner `compensate_step` threw an exception. This led to a vulnerability where failing sagas remained in `active_sagas`, causing infinite retry loops across ticks. The design was hardened to ensure failing compensations transition the saga to a terminal error state (`FAILED_ROLLED_BACK_ERROR`) and safely evict it from the queue.
  > - **Protocol Deduplication & Purity**: Duplicate `ISagaOrchestrator` declarations across modules were purged in favor of a Single Source of Truth (`kernel/api.py`). The orchestrator initialization also correctly receives `current_tick` from the caretaker instead of hardcoding `0`, respecting Engine Purity.

- **Reviewer Evaluation**:
  "Mock Fantasy"에 대한 통찰은 매우 뛰어납니다. 단위 테스트 시 실제 프로덕션 DTO의 엄격한 구조를 무시하고 Mock에 임의의 `payload`를 주입하는 것이 얼마나 위험한지 정확히 짚어냈습니다. `finally` 블록을 활용한 "Robust Failure Handling" 큐 이탈 로직 역시 무한 루프를 방지하는 적절하고 견고한 조치입니다.
  **하지만, "DTO Interface Unification" 주장은 실제 코드 구현과 모순됩니다.** 개발자는 타입 안정성을 확보했다고 보고했으나, 실제 `caretaker.py` 코드는 `state`와 `status`라는 서로 다른 필드명을 우회하기 위해 `getattr` 중첩이라는 매우 취약한 방식을 사용했습니다. 이는 근본적인 인터페이스 통일이 전혀 이루어지지 않았음을 의미하며, Vibe Check 관점에서 수용할 수 없는 'Duct-Tape' 해결책입니다.

### 6. 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Draft Content**:
  ```markdown
  ### [YYYY-MM-DD] The "Mock Fantasy" Anti-Pattern & DTO Interface Mismatches
  - **현상 (Phenomenon)**: 단위 테스트는 완벽히 통과하지만, 프로덕션 런타임에 DTO 객체의 속성에 접근할 때 `AttributeError`가 발생하거나, 이를 우회하기 위한 `getattr` 중첩 로직이 코드베이스에 오염되는 현상.
  - **원인 (Cause)**: 테스트 객체(Mock)에 실제 프로덕션 DTO(`HousingTransactionSagaStateDTO`)에는 존재하지 않는 임의의 딕셔너리(`payload`)나 일치하지 않는 상태 필드(`state` vs `status`)를 주입하여 억지로 통과시켰기 때문.
  - **해결 (Resolution)**: 다형성을 띠는 여러 DTO를 순회할 때는 임시방편적인 `getattr` 파싱을 지양해야 함. 대신 `ISagaState`와 같이 명확한 필드(`status`, `participant_ids`)를 강제하는 `Protocol`을 정의하고, 대상 DTO들이 이를 준수하도록 리팩토링해야 함.
  - **교훈 (Lesson)**: 테스트 코드가 실제 프로덕션 환경의 강타입(Strongly-typed) 구조를 반영하지 못하는 "Mock Fantasy"를 엄격하게 경계해야 함. 구조적 불일치는 런타임 우회 코드를 낳으므로, Interface/Protocol 설계 단계에서부터 근본적으로 차단해야 함.
  ```

### 7. ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**