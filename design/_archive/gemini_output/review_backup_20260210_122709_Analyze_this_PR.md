# Git Review: Government Module Test Cleanup

## 🔍 Summary
본 변경 사항은 `mod-government` 관련 유닛 테스트의 대규모 정리 작업을 수행합니다. 최근 아키텍처 리팩토링으로 인해 발생한 테스트 실패(에이전트 시그니처, 자산 접근 방식 변경 등)를 수정하고, 프로그레시브 세금 로직에 맞춰 검증 로직을 현실화했습니다. 또한, 하드코딩된 통화(`"USD"`)를 전역 상수(`DEFAULT_CURRENCY`)로 대체하여 코드 순수성을 개선했습니다.

## 🚨 Critical Issues
- 없음.

## ⚠️ Logic & Spec Gaps
- **`simulation/systems/registry.py`**:
  - `hasattr`를 사용하여 레거시(`firm.hr`)와 신규(`firm.hr_engine`) 속성을 분기 처리하는 로직이 추가되었습니다. 이는 아키텍처 원칙(`@runtime_checkable` 프로토콜 사용)에 위배되지만, 인사이트 보고서에 `TD-REGISTRY-LEGACY` 기술 부채로 명확히 기록되었고, 과도기적 호환성을 위한 임시 해결책으로 판단되어 Hard-Fail에서 제외합니다.

## 💡 Suggestions
1.  **Follow-up on `TD-REGISTRY-LEGACY`**: `simulation/systems/registry.py`에 추가된 `hasattr` 분기 로직은 빠른 시일 내에 `isinstance`와 프로토콜 기반의 검증으로 리팩토링하는 후속 작업을 계획해야 합니다.
2.  **Standardize Asset Access**: 인사이트 보고서에서 지적한 대로, `Government.assets`가 `float`을 반환하는 등 에이전트마다 자산 접근 방식이 다른 문제를 해결하기 위해, 모든 경제 주체에 `get_balance(currency: str) -> float` 와 같은 표준 인터페이스를 도입하는 것을 강력히 권장합니다.
3.  **Test Consolidation**: `modules/government/tax/tests/`에 위치한 테스트를 `tests/unit/` 디렉토리로 통합하여 프로젝트의 테스트 구조 일관성을 확보하는 것이 좋겠습니다.

## 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```markdown
  # Technical Insight Report: Government Module Cleanup

  **ID:** INSIGHT-MOD-GOV-001
  **Date:** 2025-05-27 (Simulated)
  **Author:** Jules (AI Agent)
  **Scope:** `modules/government/`, `tests/unit/governance/`, `tests/unit/modules/government/`, `tests/unit/test_tax_*.py`

  ## 1. Problem Phenomenon
  During the Unit Test Cleanup Campaign for `mod-government`, the following issues were observed:
  - **Dependency Failures:** `pytest` failed initially due to missing `PyYAML`, `joblib`, and `numpy` in the environment.
  - **Broken Tests:**
    - `tests/unit/test_tax_collection.py`: Failed because `Government.assets` returns a `float` (default currency balance), but tests accessed it as a dictionary (`gov.assets['USD']`).
    - `tests/unit/test_tax_incidence.py`: Failed due to outdated `Household` and `Firm` initialization signatures (missing `core_config`, `engine`, `config_dto`).
    - `tests/unit/test_tax_incidence.py`: Runtime errors in `TransactionManager` due to missing `escrow_agent` mock.
    - `tests/unit/test_tax_incidence.py`: Runtime `AttributeError: 'Firm' object has no attribute 'hr'` in `simulation/systems/registry.py`, indicating `Registry` was using legacy proxy attributes removed in recent refactors.
    - Assertion Mismatches: Tests assumed a flat 10% tax rate, but the system applied progressive taxation (resulting in ~16.25% effective tax on 100.0 income with survival cost logic), causing value assertion failures (`1090.0` vs `1083.75`).
  - **Hardcoded Constants:** Usage of literal `"USD"` strings in `modules/government/tax/tests/test_service.py` and `tests/unit/governance/test_judicial_system.py`.

  ## 2. Root Cause Analysis
  1.  **Refactoring Drift:** Core agents (`Household`, `Firm`) and systems (`Registry`) underwent Orchestrator-Engine refactoring (e.g., moving state to `_econ_state`/`hr_state` and logic to `Engines`), but unit tests and some system components (`Registry`) were not updated to reflect these architectural changes.
  2.  **Implicit Logic:** `Government` agent defaults to `TaxService` which utilizes `TAX_BRACKETS` (Progressive Tax) from configuration, overriding the intuitive expectation of `INCOME_TAX_RATE` (which is `0.0` in config) or simple flat tax assumptions in tests.
  3.  **Type Inconsistency:** `Government.assets` exposes a `float` (convenience property for default currency), whereas `Household.assets` (in legacy tests/mocks) or expectations were often dictionary-based.

  ## 3. Solution Implementation Details
  1.  **Environment:** Installed required dependencies via `pip`.
  2.  **Test Fixes:**
      - Updated `tests/unit/test_tax_collection.py` to assert `gov.assets` as a float.
      - Updated `tests/unit/test_tax_incidence.py`:
          - Implemented correct `Household` and `Firm` factory methods using `AgentCoreConfigDTO` and `IDecisionEngine` mocks.
          - Manually hydrated agent wallets using `deposit()` since `initial_assets` kwarg is no longer directly handled in `__init__` for wallet balance.
          - Mocked `escrow_agent` for `TransactionManager`.
          - Updated assertions to match the actual progressive tax calculation (16.25 deduction on 100.0 income).
  3.  **Code Fixes (External Dependency):**
      - Updated `simulation/systems/registry.py` to access `firm.hr_state` and use `firm.hr_engine` instead of the removed `firm.hr` proxy. This was necessary to unblock `test_tax_incidence.py`.
  4.  **Cleanup:**
      - Replaced hardcoded `"USD"` with `DEFAULT_CURRENCY` imported from `modules.system.api` in `modules/government/tax/tests/test_service.py` and `tests/unit/governance/test_judicial_system.py`.

  ## 4. Lessons Learned & Technical Debt
  -   **TD-REGISTRY-LEGACY:** `simulation/systems/registry.py` still contains legacy patterns (checking `hasattr(buyer, 'hr')` fallback) and needed patching. It should be fully audited for other legacy attribute accesses.
  -   **TD-GOV-ASSETS-TYPE:** `Government.assets` returning `float` while other agents might return dicts or objects creates strict typing friction in tests. A standardized `get_balance(currency)` is preferred.
  -   **TD-TAX-CONFIG-CONFUSION:** `INCOME_TAX_RATE` in config is `0.0`, yet the system applies Progressive Tax based on `TAX_BRACKETS`. This "hidden" default behavior makes testing specific rates difficult without explicitly mocking `TaxService` or `FiscalPolicy`.
  -   **Test Location:** `modules/government/tax/tests/` exists inside the source tree, while other tests are in `tests/unit/`. These should ideally be consolidated.
  ```
- **Reviewer Evaluation**:
  - **정확성 및 깊이**: 문제 현상(`Phenomenon`)부터 근본 원인(`Root Cause`), 그리고 해결책(`Solution`)까지의 흐름이 매우 논리적이고 정확합니다. 특히 'Refactoring Drift'와 'Implicit Logic'이라는 핵심 원인을 정확히 짚어냈습니다.
  - **기술 부채 식별**: `TD-REGISTRY-LEGACY`, `TD-GOV-ASSETS-TYPE` 등 구체적인 태그와 함께 기술 부채를 명확히 식별하고 문서화한 점이 매우 훌륭합니다. 이는 프로젝트의 건강성을 유지하는 데 필수적인 활동입니다.
  - **가치 평가**: 단순한 테스트 수정 보고서를 넘어, 시스템의 잠재적 문제점과 아키텍처 불일치를 수면 위로 드러낸 고품질의 인사이트입니다.

## 📚 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**: 인사이트 보고서에서 식별된 `TD-REGISTRY-LEGACY` 항목을 중앙 기술 부채 원장에 추가할 것을 제안합니다.
  ```markdown
  ---
  id: TD-REGISTRY-LEGACY
  date: 2025-05-27
  status: identified
  reporter: Jules (AI Agent)
  source_insight: communications/insights/mod-government.md
  ---
  
  ### 현상 (Phenomenon)
  `simulation/systems/registry.py`가 리팩토링된 신규 에이전트(`hr_engine`)와 레거시 에이전트(`hr`)를 모두 처리하기 위해 `hasattr`를 사용한 분기 로직을 포함하고 있습니다.
  
  ### 부채 내용 (Debt Description)
  이 `hasattr` 기반의 덕 타이핑(duck typing)은 프로젝트의 프로토콜 기반 아키텍처 시행 원칙에 위배됩니다. 이는 타입 안정성을 저해하고, 향후 리팩토링 시 잠재적인 오류의 원인이 될 수 있습니다.
  
  ### 제안된 해결책 (Proposed Solution)
  `IRegistry` 인터페이스를 사용하는 모든 에이전트가 `IHREngineProvider`와 같은 명확한 프로토콜을 구현하도록 강제하고, `registry.py`에서 `isinstance`와 프로토콜을 사용하여 타입 검사를 수행하도록 코드를 리팩토링해야 합니다.
  ```

## ✅ Verdict
**APPROVE**

**사유**: 필수적인 인사이트 보고서가 포함되었고, 그 내용이 매우 우수합니다. 코드 변경 사항은 보고서에 기술된 문제를 정확히 해결하며, 유일한 아키텍처 우려 사항(`hasattr` 사용)은 기술 부채로 적절히 문서화되었습니다. 이 PR은 프로젝트의 기술적 건전성을 향상시키는 모범적인 변경입니다.
