# 🔍 PR Review: FIX-FINAL-REGRESSIONS

## 1. 🔍 Summary
본 변경 사항은 "페니 스탠다드(Penny Standard)" 마이그레이션 이후 발생한 3개의 주요 테스트 실패를 해결합니다. 주요 수정 내용은 테스트 코드 내 화폐 단위(달러 vs 페니)의 100배수 스케일 불일치 조정, `MagicMock` 반환으로 인한 `TypeError` 해결을 위한 모의 객체(Mock) 설정 강화, 그리고 테스트 스텁(Stub)의 누락된 속성 추가입니다.

## 2. 🚨 Critical Issues
- **없음**. 보안 취약점이나 시스템의 재정 무결성을 해치는 중대한 버그는 발견되지 않았습니다. 오히려 기존에 잠재되어 있던 계산 오류를 수정하였습니다.

## 3. ⚠️ Logic & Spec Gaps
- **하드코딩된 로직 발견**: `WelfareManager` 내부에 최소 생존 비용이 1000 페니($10)로 하드코딩된 "Welfare Floor" 로직이 있음이 개발자에 의해 식별되었습니다. 이로 인해 테스트에서 예상치 못한 복지 지원금이 계산되었습니다. (`test_government_integration.py`의 주석 및 Insight 보고서에 명시됨) 이는 명세서에 명시되지 않은 암묵적 로직으로, 향후 설정 변경 시 잠재적 버그의 원인이 될 수 있습니다.

## 4. 💡 Suggestions
개발자가 `communications/insights/FIX-FINAL-REGRESSIONS.md`에 작성한 제안 사항에 적극 동의하며, 이를 지지합니다.
1.  **`Money` 타입 도입**: `amount_pennies`와 `amount_dollars`와 같이 변수명으로 단위를 구분하는 현재 방식보다, 단위를 명확히 하는 `Money` 같은 Value Object를 도입하여 100배수 계산 오류를 원천적으로 방지하는 것을 강력히 권장합니다.
2.  **설정 값 추출**: `WelfareManager`에 하드코딩된 `1000` (페니) 최저 보장액을 `config/economy_params.yaml` 등의 설정 파일로 추출하여 `MIN_SURVIVAL_COST_PENNIES`와 같은 명확한 이름으로 관리해야 합니다.

## 5. 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```
  # Insight Report: Fix Final Penny-Standard Regressions (PH15-FIX)

  ## 1. Overview
  This mission focused on resolving the last 3 test failures caused by the "Penny Standard" migration (switching from float dollars to integer pennies). The failures were due to mismatched scale assumptions (100x), improper mocking of financial agents, and missing attributes in test stubs.

  ## 2. Key Resolutions

  ### A. 100x Scale Mismatch in Fiscal Policy
  - **Issue**: `FiscalPolicyManager` expects market prices in Dollars (float) and multiplies them by 100 to convert to Pennies. The unit test `test_fiscal_policy_manager.py` provided `1000.0` (thinking it was pennies or intending $1000), which resulted in a survival cost of 100,000 pennies ($1000). The test assertion expected brackets based on 1000 pennies ($10).
  - **Fix**: Updated the test input to `10.0` (Dollars), which correctly converts to 1000 pennies, aligning with the assertion.

  ### B. Mock Fragility in Government Integration (TypeError)
  - **Issue**: `TaxService.collect_wealth_tax` calls `agent.get_balance(currency)` which returns an `int`. The test mocks in `tests/modules/government/test_government_integration.py` did not configure `get_balance` to return a value, causing it to return a `MagicMock` object. This triggered a `TypeError` when compared with an integer threshold.
  - **Fix**: Explicitly configured `agent.get_balance.return_value` to return integer penny amounts in the mocks.

  ### C. Config Ambiguity & Welfare Floor (Assertion Error)
  - **Issue**:
      1. `test_government_integration.py` (Integration) asserted a tax of 380 pennies but got 400. This was because `WEALTH_TAX_THRESHOLD` was set to `1000.0` (1000 pennies), whereas the test logic assumed 100,000 pennies ($1000).
      2. The welfare benefit assertion expected 10 pennies, but got 500. This was due to a hidden logic floor in `WelfareManager`: `max(survival_cost, 1000)`. The test input implied a survival cost of 20 pennies, which was overridden by the 1000-penny floor ($10 minimum).
  - **Fix**:
      1. Updated `WEALTH_TAX_THRESHOLD` to `100000` (pennies).
      2. Updated the welfare benefit assertion to `500` (50% of the 1000-penny floor) and documented the floor logic in the test.

  ### D. Missing QE Support in Test Stub
  - **Issue**: `FinanceSystem.issue_treasury_bonds` contains logic to check `government.sensory_data.current_gdp` for QE triggers. The `StubGovernment` used in `test_system.py` lacked `sensory_data`.
  - **Fix**: Added `sensory_data` mock and `current_gdp` attribute to `StubGovernment`.

  ## 3. Technical Debt Observations

  | ID | Module | Description | Status |
  | :--- | :--- | :--- | :--- |
  | **TD-TEST-SCALE** | Tests | Unit tests mix Dollar and Penny inputs without explicit type/variable naming (e.g., `price` vs `price_pennies`). | Mitigated (Local Fix) |
  | **TD-WELFARE-FLOOR**| Government | `WelfareManager` has a hardcoded floor of 1000 pennies ($10) for survival cost, which might not scale with config changes. | Identified |
  | **TD-MOCK-TYPE** | Tests | Mocks often lack type enforcement (`spec=IAgent`), allowing missing methods (`get_balance`) to fail late at runtime. | Ongoing |

  ## 4. Recommendations
  - **Strict Typing for Money**: Adopt `Money` value objects or strictly name variables `amount_pennies` vs `amount_dollars` to prevent 100x errors.
  - **Review Hardcoded Floors**: The 1000-penny floor in `WelfareManager` should be configurable (`MIN_SURVIVAL_COST`).
  ```
- **Reviewer Evaluation**:
  - **매우 훌륭함 (Excellent)**. 이 Insight 보고서는 단순한 작업 요약을 넘어, 실패한 테스트 케이스 각각에 대한 **현상, 원인, 해결** 과정을 명확하게 기술하고 있습니다.
  - 특히 `TypeError`의 원인이 `get_balance` 메소드가 `MagicMock` 객체를 반환했기 때문이라는 점과, 복지 지원금 계산 오류가 하드코딩된 `1000` 페니 하한선 때문이라는 점을 정확히 분석해낸 것은 문제의 근본 원인을 파악하는 높은 디버깅 역량을 보여줍니다.
  - `TD-TEST-SCALE`, `TD-WELFARE-FLOOR` 등의 ID를 부여하여 기술 부채를 구체적으로 식별하고 관리하려는 시도 또한 모범적입니다.

## 6. 📚 Manual Update Proposal
해당 변경사항에서 발견된 인사이트는 프로젝트의 중요한 자산입니다. 다음 내용을 관련 기술 원장에 추가할 것을 제안합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  | ID | Module | Description | Reporter | Date | Status |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | TD-WELFARE-FLOOR | `modules.government.WelfareManager` | The minimum survival cost for welfare calculations is hardcoded to `1000` pennies ($10) via `max(survival_cost, 1000)`. This should be extracted into a configurable parameter (`MIN_SURVIVAL_COST_PENNIES`) to avoid unexpected behavior when economic parameters change. | Jules | 2026-02-12 | Identified |
  ```

## 7. ✅ Verdict
**APPROVE**

- **사유**: 모든 변경 사항은 테스트 코드의 정합성을 복구하는 데 명확히 기여합니다. 무엇보다, 규정에 따라 **상세하고 수준 높은 Insight 보고서(`communications/insights/FIX-FINAL-REGRESSIONS.md`)가 작성 및 포함**되었습니다. 식별된 문제점들은 즉각적인 수정이 필요한 보안/로직 결함이 아니며, 오히려 향후 개선을 위한 귀중한 기술 부채로 잘 문서화되었습니다.
