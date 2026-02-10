🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\design\_archive\gemini_output\pr_diff_cleanup-mod-household-17794814435586128663.txt
🚀 [GeminiWorker] Running task with manual: git_reviewer.md

📝 [Review Report]
============================================================
# 🔍 Summary
본 변경 사항은 `household` 모듈의 대규모 리팩토링 및 클린업을 수행합니다. Orchestrator-Engine 아키텍처 변경으로 인해 발생한 수많은 테스트 실패를 해결하고, 코드 전반에 하드코딩된 매직 넘버를 상수로 추출하여 가독성과 유지보수성을 크게 향상시켰습니다. 또한, 테스트 작성을 표준화하기 위한 팩토리(`create_household`)를 도입하고, 스냅샷 생성 시 `Wallet` 객체가 독립적으로 복사되도록 로직을 수정하여 데이터 무결성을 강화했습니다.

## 🚨 Critical Issues
- 없음. 보안 위반, 돈 복사/유출, 주요 로직 오류 등 즉각적인 수정이 필요한 항목은 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps
- **테스트 커버리지 공백 (인지된 부채)**: `cleanup-mod-household.md` 인사이트 보고서에 명시된 바와 같이, 더 이상 사용되지 않는 레거시 AI Tactic (`decide_and_learn`)을 검증하던 테스트 파일들(`test_household_ai_consumption.py`, `test_household_decision_engine_multi_good.py`, `test_household_marginal_utility.py`)이 삭제되었습니다. 이는 새로운 `ActionVector` 기반 로직에 대한 테스트 커버리지 공백을 의미하며, 보고서에서 기술 부채로 올바르게 지적하고 있습니다.

## 💡 Suggestions
- **`DecisionUnit` 역할 명확화**: 인사이트 보고서에서 `DecisionUnit`의 모호한 역할을 기술 부채로 지적한 것은 매우 정확합니다. 이번 PR에서 관련 테스트(`test_decision_unit.py`)가 수정되긴 했지만, 후속 작업으로 `BudgetEngine` 및 `ConsumptionEngine`과의 역할을 명확히 구분하고 점진적으로 제거하는 것을 강력히 권장합니다.
- **신규 테스트 조기 작성**: 삭제된 레거시 테스트로 인해 발생한 커버리지 공백을 메우기 위해, `AIDrivenHouseholdDecisionEngine`의 `ActionVector` 결과물을 검증하는 새로운 테스트 케이스들을 우선순위를 높여 작성할 필요가 있습니다.

## 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```markdown
  # Technical Insight Report: Household Module Cleanup

  **Mission Key:** `cleanup-mod-household`
  **Date:** 2024-05-23
  **Author:** Jules

  ## 1. Problem Phenomenon
  The `household` module unit tests were failing due to significant architectural drift. Key symptoms included:
  - `TypeError` during `Household` instantiation due to signature changes (missing `core_config`, `engine`).
  - `AttributeError` on mocks (e.g., `_bio_state`) because tests mocked the class but didn't populate internal DTOs used by new Orchestrator logic.
  - `TypeError` in `EconStateDTO` initialization (missing `wallet`, `employment_start_tick`).
  - Tests referencing deprecated components (`DecisionUnit` housing logic, AI Tactics) that have been refactored or removed.
  - Tests expecting `assets` (float) on `EconStateDTO` instead of `IWallet`.

  ## 2. Root Cause Analysis
  1.  **Architecture Shift:** The transition to the Orchestrator-Engine pattern and `AIDrivenHouseholdDecisionEngine` (ActionVector based) rendered many tests obsolete. Tests were still verifying legacy AI Tactics (`decide_and_learn`) which are no longer used.
  2.  **DTO Evolution:** `EconStateDTO` evolved to use `IWallet` and added fields like `employment_start_tick`, but tests were not updated.
  3.  **Missing Mixin:** `Household` class in `simulation/core_agents.py` was missing inheritance from `HouseholdStateAccessMixin`, causing `HouseholdSnapshotAssembler` to fail when accessing `get_bio_state` etc.
  4.  **Hardcoded Values:** Logic contained magic numbers (e.g., `0.95` smoothing factor, `30` tick check) scattered across engines.

  ## 3. Solution Implementation Details
  1.  **Test Factory Update:**
      -   Updated `tests/utils/factories.py` with a robust `create_household` factory that handles dependency injection (`AgentCoreConfigDTO`, `IDecisionEngine`, `Wallet` hydration).
      -   This standardized test setup and eliminated boilerplate errors.

  2.  **DTO & Logic Fixes:**
      -   Updated `EconStateDTO` initialization in tests to use `Wallet` and include all required fields.
      -   Updated `EconStateDTO.copy()` to perform a deep copy of `Wallet` to ensure snapshot isolation, fixing `TestHouseholdSnapshotAssembler` failures.
      -   Added `HouseholdStateAccessMixin` to the `Household` class to support snapshot services.

  3.  **Legacy Test Cleanup:**
      -   Deleted/Skipped tests in `test_household_decision_engine_multi_good.py`, `test_household_marginal_utility.py`, and `test_household_ai_consumption.py` that verified deprecated AI Tactics (`decide_and_learn`) or removed internal methods (`_handle_specific_purchase`).
      -   Updated `test_decision_unit.py` to mock `HousingPlanner` and `HousingSystem` (Saga) interactions, as `DecisionUnit` now delegates housing actions instead of executing them directly.

  4.  **Constant Refactoring:**
      -   Extracted magic numbers in `modules/household/engines/*.py` to module-level constants or `HouseholdConfigDTO` lookups.
      -   Replaced hardcoded `"USD"` with `modules.system.api.DEFAULT_CURRENCY`.

  ## 4. Lessons Learned & Technical Debt
  -   **Technical Debt (Legacy Tests):** A significant portion of tests in `tests/unit/test_household_*.py` targets legacy logic (Tactics, old DecisionUnit). These tests were deleted/skipped to unblock the build but represent a gap in coverage for the new `ActionVector` logic. **Action:** Create new tests for `AIDrivenHouseholdDecisionEngine` focusing on `ActionVector` outputs.
  -   **Technical Debt (DecisionUnit):** `DecisionUnit` class seems to be a legacy orchestrator co-existing with `BudgetEngine`. Its role is ambiguous. **Action:** Deprecate `DecisionUnit` fully in favor of `BudgetEngine` and `ConsumptionEngine`.
  -   **Mocking Risks:** Tests relying on `MagicMock(spec=Household)` were fragile because they missed dynamic attributes initialized in `__init__`. **Insight:** Use factories (`create_household`) to instantiate real objects with mocked dependencies for more robust integration-like unit tests.
  ```
- **Reviewer Evaluation**:
  - **정확성 및 깊이**: 최고 수준의 인사이트 보고서입니다. 발생한 문제(Phenomenon)를 `TypeError`, `AttributeError` 등 구체적인 증상으로 정확히 나열하고, 그 근본 원인(Root Cause)을 아키텍처 변화, DTO 진화, Mixin 누락 등 핵심적인 설계 변경 사항과 정확하게 연결지었습니다.
  - **가치**: 이 보고서는 단순한 버그 수정을 넘어, 왜 코드가 깨졌는지에 대한 명확한 진단을 제공합니다. 특히 "Mocking Risks"에서 `MagicMock(spec=...)`의 취약점을 지적하고, 이를 해결하기 위해 실제 객체를 생성하는 팩토리(`create_household`)를 도입한 교훈은 프로젝트 전체의 테스트 품질을 향상시킬 수 있는 매우 가치 있는 통찰입니다.
  - **기술 부채 관리**: 레거시 테스트 삭제로 인한 커버리지 공백과 `DecisionUnit`의 모호한 역할을 명확히 기술 부채로 식별하고 구체적인 후속 조치(Action)를 제안한 점은 매우 훌륭합니다. 이는 프로젝트의 건강성을 유지하기 위한 책임감 있는 태도입니다.

## 📚 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**: `MagicMock` 사용의 위험성과 팩토리 패턴의 유용성에 대한 교훈은 모든 모듈 개발에 적용될 수 있는 중요한 내용이므로, 기술 부채 원장 또는 테스트 가이드라인에 추가할 것을 제안합니다.

  ```markdown
  ---
  - **부채 유형**: 테스트 취약성 (Test Fragility)
  - **현상**: `MagicMock(spec=ClassName)`을 사용한 테스트는 클래스의 `__init__`에서 동적으로 생성되는 속성(예: 내부 DTO 객체)을 모킹하지 못해, `AttributeError`를 유발하며 아키텍처 변경에 매우 취약함.
  - **원인**: `spec`은 메소드 시그니처만 검증할 뿐, 생성자 내부의 실제 객체 상태를 보장하지 않음.
  - **해결/교훈**: 테스트에 필요한 실제 객체를 생성하되, 외부 의존성만 모킹하는 **테스트 팩토리 패턴** (`create_household`와 같은)을 도입한다. 이는 테스트의 견고성을 높이고 실제 객체의 동작에 더 가깝게 검증할 수 있도록 한다.
  ---
  ```

## ✅ Verdict
- **APPROVE**

이 PR은 기술 부채를 해결하고 코드 품질을 크게 개선하는 모범적인 변경입니다. 특히, 변경 사항의 배경과 결과를 상세히 기록한 고품질의 인사이트 보고서를 포함한 점이 인상적입니다. 제기된 기술 부채에 대한 후속 조치를 계획하는 것을 조건으로 승인합니다.

============================================================
