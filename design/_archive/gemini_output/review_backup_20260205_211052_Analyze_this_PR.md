# 🔍 Summary
본 변경 사항은 시뮬레이션 스트레스 테스트 중 발생한 여러 크래시를 해결합니다. 주요 수정 사항은 `None` 값을 가질 수 있는 지갑(wallet) 속성에 대한 방어 코드 추가, 다중 통화 자산(dictionary 형태)을 처리하도록 데이터베이스 및 로직 핸들러 업데이트, 그리고 리팩토링된 `InheritanceManager`의 API 불일치 해결을 포함합니다. 변경 사항은 안정성을 크게 향상시킵니다.

## 🚨 Critical Issues
- 발견된 사항 없음. API 키, 비밀번호 또는 시스템 절대 경로와 같은 하드코딩된 값은 없습니다.

## ⚠️ Logic & Spec Gaps
- 발견된 사항 없음. 수정 사항은 인사이트 보고서에 기술된 버그의 근본 원인을 정확하게 해결하며, 제로섬(Zero-Sum) 원칙에 영향을 주지 않습니다.

## 💡 Suggestions
- **Insight Report Format**: `communications/insights/FIX-INHERITANCE-STABILITY.md` 파일의 헤더가 "Phenomenon", "Root Cause" 등으로 영문으로 작성되었습니다. 프로젝트 표준인 `현상/원인/해결/교훈` 형식으로 통일하면 가독성과 일관성이 향상될 것입니다.
- **Artifact Files**: 다수의 `reports/snapshots/*.json` 파일이 삭제되었습니다. 이러한 파일이 테스트 실행의 부산물이라면, 향후 PR을 깔끔하게 유지하기 위해 `.gitignore`에 추가하는 것을 고려해볼 수 있습니다.

## 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```markdown
  # Fix Inheritance Manager and Restore Simulation Stability

  ## Phenomenon
  During the 100-tick stress test (`scenarios/scenario_stress_100.py`), the simulation crashed with an `AttributeError: 'NoneType' object has no attribute 'get_balance'`. This occurred in `SettlementSystem.settle_atomic` -> `_execute_withdrawal`. Debugging revealed that the `agent` passed to `_execute_withdrawal` (specifically an `EscrowAgent` or similar system agent) had a `wallet` attribute that was `None`, causing the crash when `agent.wallet.get_balance` was called.

  Additionally, a `TypeError` and `sqlite3.ProgrammingError` were observed related to multi-currency asset handling. `EscheatmentHandler` failed when `buyer.assets` returned a `defaultdict` (multi-currency) instead of a float during comparison. Similarly, `AgentRepository` failed to persist agent states because `assets` was a dictionary, which SQLite bindings could not handle directly.

  ## Root Cause
  1.  **InheritanceManager API Mismatch:** The `AgentLifecycleManager` passed a `SimulationState` DTO to `InheritanceManager.process_death`, but `InheritanceManager` attempted to access `.world_state` on it, which does not exist on the DTO. This was a legacy artifact where `InheritanceManager` expected the full Engine object.
  2.  **Unsafe Wallet Access:** `SettlementSystem` checked `hasattr(agent, 'wallet')` but did not check if `agent.wallet` was actually `None`. `EscrowAgent` (and potentially others) might declare the property but return `None` or be initialized without it in certain contexts.
  3.  **Multi-Currency Incompatibility:** Recent updates to support multi-currency (Phase 33) changed `agent.assets` to return a dictionary (`Dict[CurrencyCode, float]`).
      *   `EscheatmentHandler` treated `assets` as a scalar float.
      *   `AgentRepository` attempted to save the raw dictionary to a SQLite `REAL` (float) column.

  ## Solution
  1.  **Refactor InheritanceManager:** Updated `process_death` to accept `SimulationState` DTO and pass it directly to `TransactionProcessor`. Removed incorrect usage of `simulation.world_state`.
  2.  **Defensive Wallet Check:** Updated `SettlementSystem._execute_withdrawal` to explicitly check `if hasattr(agent, 'wallet') and agent.wallet is not None`.
  3.  **Multi-Currency Handling:**
      *   Updated `EscheatmentHandler` to detect if `buyer.assets` is a dictionary and extract `DEFAULT_CURRENCY` (defaulting to 0.0) before scalar comparison.
      *   Updated `AgentRepository.save_agent_state` and `save_agent_states_batch` to extract `DEFAULT_CURRENCY` from the `assets` dictionary before DB insertion, preserving schema compatibility.

  ## Lessons Learned
  *   **DTO vs. Engine Confusion:** Explicit typing (`SimulationState` vs `Simulation`) is crucial in "God Class" decomposition. Legacy systems often assume they have access to the full engine (`world_state`), which violates the new decoupled architecture.
  *   **Property Safety:** `hasattr` is insufficient for properties that might return `None`. Always check for existence *and* nullity for optional components.
  *   **Migration Backward Compatibility:** When introducing complex types (like Multi-Currency dictionaries) into fields that were previously scalars (Assets), all consumers (DB, Logic, Handlers) must be audited. Implementing "smart extractors" that handle both types during the transition period is a robust strategy.
  ```
- **Reviewer Evaluation**:
  - 매우 우수한 인사이트 보고서입니다. 세 가지 다른 유형의 오류(AttributeError, TypeError, ProgrammingError)가 어떻게 연관되어 있는지를 명확하게 분석하고, 각 문제의 근본 원인을 정확히 식별했습니다.
  - 특히 "DTO vs. Engine Confusion"에 대한 통찰은 최근 진행된 아키텍처 분리 작업의 핵심을 꿰뚫고 있으며, 이러한 종류의 기술 부채를 식별하고 문서화하는 것은 프로젝트에 매우 가치 있는 기여입니다.
  - `hasattr`의 한계점과 데이터 타입 변경 시 하위 호환성 확보 전략에 대한 교훈은 모든 팀원이 숙지해야 할 중요한 내용입니다.

## 📚 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/ARCHITECTURAL_INSIGHTS.md` (가상 파일 경로)
- **Update Content**: 다음 내용을 "Best Practices" 또는 "Lessons Learned" 섹션에 추가할 것을 제안합니다.

  ```markdown
  ### 주제: 레거시 시스템 리팩토링 시 데이터 구조 및 API 호환성
  - **현상**: 시스템 안정성 테스트 중, DTO(Data Transfer Object)와 전체 엔진(Engine) 객체의 혼용, `None` 반환 속성에 대한 불안전한 접근, 그리고 데이터베이스 스키마와 불일치하는 데이터 타입(scalar -> dict)으로 인해 동시다발적인 크래시가 발생함.
  - **교훈**:
    1.  **API 계약 준수**: "God Class"를 DTO로 분해할 때, 모든 소비 모듈이 더 이상 전체 엔진 객체에 접근할 수 없다는 점을 인지하고 명시적인 DTO 계약만을 사용하도록 철저히 감사해야 한다.
    2.  **방어적 속성 접근**: `hasattr(obj, 'prop')` 검사는 `obj.prop`이 `None`을 반환하는 경우를 막지 못한다. 옵셔널(optional) 컴포넌트에 접근할 때는 항상 존재성(`hasattr`)과 `None` 여부를 함께 확인해야 한다 (`if hasattr(...) and obj.prop is not None`).
    3.  **데이터 타입 마이그레이션**: 필드의 데이터 타입이 단순 타입(e.g., `float`)에서 복합 타입(e.g., `dict`)으로 변경될 때, 해당 필드를 사용하는 모든 로직, 데이터베이스 핸들러, API 소비자를 반드시 감사해야 한다. 전환 기간 동안 두 가지 타입을 모두 처리할 수 있는 "스마트 추출기(smart extractor)"를 구현하는 것은 안정적인 전략이다.
  ```

## ✅ Verdict
**APPROVE**

이 변경 사항은 시스템의 안정성을 크게 개선하며, 문제의 원인과 해결 과정을 상세히 기술한 훌륭한 인사이트 보고서를 포함하고 있습니다. 모든 검사 항목을 통과했습니다.
