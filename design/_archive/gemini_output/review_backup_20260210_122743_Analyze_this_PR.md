# 🔍 Summary
본 변경 사항은 여러 스크립트와 테스트에 하드코딩되어 있던 `"USD"` 문자열을 `modules.system.api`의 `DEFAULT_CURRENCY` 상수로 대체하는 리팩토링입니다. 또한, `TransactionData` DTO 변경으로 인해 실패하던 유닛 테스트를 수정하고, Python 3.12+에서 발생하는 `SyntaxWarning`을 해결하여 코드 품질을 개선했습니다.

# 🚨 Critical Issues
- 발견되지 않았습니다. 하드코딩된 상수들이 성공적으로 제거되었습니다.

# ⚠️ Logic & Spec Gaps
- 발견되지 않았습니다. 변경 사항은 주로 상수 교체 및 테스트 코드 수정으로, 로직 변경은 없습니다. DTO 변경에 따른 테스트 코드 수정은 정확하게 이루어졌습니다.

# 💡 Suggestions
- 특이사항 없습니다. 스크립트 전반에 걸쳐 일관되게 상수를 적용한 점이 좋습니다.

# 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```markdown
  # Technical Insight Report: Infrastructure Cleanup

  ## 1. Problem Phenomenon
  During the Unit Test Cleanup Campaign for Infrastructure modules, several issues were encountered:
  1.  **Environment Instability**: `tests/unit/test_config_parity.py` failed to collect due to `ImportError: No module named 'yaml'` and `ImportError: No module named 'joblib'`.
  2.  **Broken Tests**: `tests/unit/test_repository.py::test_save_and_get_transaction` failed with `TypeError: TransactionData.__init__() missing 1 required positional argument: 'currency'`.
  3.  **Code Quality Warning**: `tests/unit/test_ledger_manager.py` emitted a `SyntaxWarning: invalid escape sequence '\|'`.
  4.  **Hardcoded Constants**: Multiple verification scripts (`scripts/verification/verify_integrity_v2.py`, `scripts/audit_zero_sum.py`, `scripts/trace_tick.py`) contained hardcoded `"USD"` strings, violating the `TD-INT-CONST` directive.

  ## 2. Root Cause Analysis
  1.  **Environment**: The testing environment lacked necessary dependencies (`PyYAML`, `joblib`) which are required by `simulation.ai.model_wrapper` and configuration managers. This suggests a drift between `requirements.txt` and the active environment or insufficient pre-run checks.
  2.  **DTO Evolution**: The `TransactionData` DTO was updated in Phase 33 to include a `currency` field (Multi-Polar WorldState), but the corresponding unit test `test_repository.py` was not updated to reflect this change.
  3.  **Regex Syntax**: Python 3.12+ is stricter about escape sequences in strings. The regex pattern `\|` in a normal string caused a warning.
  4.  **Legacy Patterns**: Scripts were written assuming a single-currency world ("USD") and did not import the canonical `DEFAULT_CURRENCY` from `modules.system.api`.

  ## 3. Solution Implementation Details
  1.  **Dependencies**: Installed `joblib`, `PyYAML`, and other dependencies from `requirements.txt`.
  2.  **Test Fixes**:
      *   Updated `tests/unit/test_repository.py` to import `DEFAULT_CURRENCY` from `modules.system.api` and pass `currency=DEFAULT_CURRENCY` when instantiating `TransactionData`.
      *   Updated `tests/unit/test_ledger_manager.py` to use a raw string (`r"..."`) for the regex assertion, resolving the `SyntaxWarning`.
  3.  **Refactoring**:
      *   Refactored `scripts/verification/verify_integrity_v2.py`, `scripts/audit_zero_sum.py`, and `scripts/trace_tick.py` to import and use `DEFAULT_CURRENCY` instead of hardcoded `"USD"`.

  ## 4. Lessons Learned & Technical Debt
  -   **TD-INFRA-ENV**: The environment setup process needs to strictly enforce `requirements.txt` installation before running tests to avoid "works on my machine" issues.
  -   **TD-TEST-SYNC**: When DTOs are modified (e.g., adding fields), a grep or search for usages in `tests/` should be mandatory to prevent regression in unit tests.
  -   **TD-SCRIPT-DEBT**: Scripts in `scripts/` often lag behind the main codebase in terms of best practices (imports, constants). They should be treated as part of the codebase and linted/refactored regularly.
  ```
- **Reviewer Evaluation**:
    - **매우 우수한 인사이트 보고서입니다.** 문제 현상을 환경, 테스트, 코드 품질, 하드코딩 네 가지 측면에서 체계적으로 분류하고, 각 문제의 근본 원인을 정확하게 분석했습니다.
    - 특히 DTO 변경 시 테스트 코드 동기화 (`TD-TEST-SYNC`)와 `scripts` 폴더 내 코드의 품질 관리 필요성(`TD-SCRIPT-DEBT`)을 기술 부채로 명확히 정의한 점은 프로젝트 전체의 유지보수성에 기여하는 중요한 통찰입니다.
    - 해결책 또한 실제 코드 변경 사항과 완벽하게 일치하며, 단순한 문제 해결을 넘어 미래의 실수를 예방하기 위한 교훈을 잘 도출했습니다.

# 📚 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  id: TD-SCRIPT-DEBT
  title: Ad-hoc 스크립트의 레거시 패턴 누적
  status: identified
  created_date: 2026-02-10
  resolved_date:
  related_missions:
    - cleanup-mod-infra
  ---
  
  **1. 현상 (Phenomenon)**
  
  - `scripts/` 디렉토리 내의 검증 및 분석용 스크립트들이 메인 애플리케이션 코드베이스의 최신 변경사항(상수, DTO 구조 등)을 따라가지 못하는 경우가 빈번함.
  - `"USD"`와 같은 매직 스트링이 하드코딩되어 있거나, 오래된 DTO 초기화 방식을 사용하여 에러를 유발.
  
  **2. 원인 (Root Cause)**
  
  - 스크립트는 일회성 작업으로 간주되어, 코드 리뷰나 린팅(Linting) 프로세스에서 제외되는 경향이 있음.
  - 메인 코드 리팩토링 시, 스크립트 파일들은 변경 범위에서 누락되기 쉬움.
  
  **3. 해결책 (Solution)**
  
  - **Code as Code**: `scripts/` 디렉토리의 코드도 애플리케이션의 일부로 간주하고, 동일한 린팅 및 정적 분석 규칙을 적용.
  - **Refactoring Scope**: DTO나 핵심 상수 변경 시, `scripts/` 디렉토리를 포함한 전체 코드베이스에서 사용처를 검색하여 함께 수정하는 것을 의무화.
  - `modules.system.api`와 같은 중앙 API 모듈을 적극적으로 사용하여 코드의 일관성을 유지.
  
  **4. 교훈 (Lesson Learned)**
  
  - 유지보수 스크립트의 품질 저하는 장기적으로 기술 부채를 누적시키고, 프로덕션 코드의 신뢰성을 검증하는 데 방해가 된다.
  ```

# ✅ Verdict
**APPROVE**

- 하드코딩 상수를 제거하고 레거시 코드를 성공적으로 리팩토링했습니다.
- 실패하는 테스트를 수정하고 코드 품질 경고를 해결했습니다.
- **가장 중요한 점으로, 작업 내용과 교훈을 담은 상세하고 수준 높은 인사이트 보고서를 `communications/insights/`에 정확히 제출했습니다.** 모든 요구사항을 완벽하게 충족합니다.
