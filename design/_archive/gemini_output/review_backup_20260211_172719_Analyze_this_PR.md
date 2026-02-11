# 🔍 PR Review: `fix-household-and-tests-pennies`

## 🔍 Summary
이번 변경은 시스템의 핵심 재무 로직을 부동소수점(float, 달러)에서 정수(int, 페니) 단위로 전환하여, 부동소수점 정밀도 오류 및 자산 누수(leak) 문제를 해결하는 데 중점을 둡니다. 이 리팩토링은 거래 관리, 세금, 상속, 출생 증여금 등 돈과 관련된 거의 모든 로직에 영향을 미쳤으며, 변경 사항을 검증하기 위해 관련된 테스트 코드가 광범위하게 수정되었습니다.

## 🚨 Critical Issues
- 발견되지 않았습니다. API 키, 비밀번호 등의 하드코딩은 없으며, 이번 변경의 핵심 목표인 Zero-Sum 위반 문제를 성공적으로 해결한 것으로 보입니다.

## ⚠️ Logic & Spec Gaps
- **의도된 설계**: `TransactionManager` (페니 단위 처리)와 `TaxService` (달러 단위 처리) 간의 단위 불일치가 존재합니다. 하지만 이는 개발자가 명확히 인지하고 있는 사항이며, `TransactionManager` 내에 페니-달러 간 변환을 수행하는 '어댑터' 로직을 명시적으로 구현하여 문제를 해결했습니다. 이는 버그나 설계 누락이 아닌, 점진적 마이그레이션을 위한 현실적인 설계 결정입니다. 이 내용은 첨부된 `Insight` 보고서에도 기술 부채로 잘 기록되어 있습니다.

## 💡 Suggestions
- **후속 마이그레이션 권장**: 현재 `TransactionManager`에 구현된 단위 변환 로직은 훌륭한 임시 해결책이지만, 장기적으로는 `TaxService`와 관련 재정 정책 모듈 전체를 페니 단위로 마이그레이션하여 불필요한 변환 오버헤드와 잠재적 오류 가능성을 제거하는 것이 좋습니다. 이는 제출된 인사이트 보고서에서도 언급된 내용으로, 이를 공식적인 기술 부채로 관리하고 후속 미션으로 계획할 것을 강력히 권장합니다.

## 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```markdown
  # Mission Insights: Household Fixes & Integer Precision

  ## Overview
  This mission focused on resolving failures in Household modules and Scenario diagnostics, primarily driven by the migration to integer pennies (`int`) for currency values and DTO field updates.

  ## Key Changes & Fixes
  ...

  ## Technical Debt & Insights
  - **Unit Mismatch**: There is persistent friction between `TransactionManager` (handling pennies for settlement) and `TaxService`/`Government` methods (expecting dollars for calculation). The explicit conversion in `TransactionManager` is a bridge, but a full migration of `TaxService` to pennies would be cleaner.
  - **Mock Consistency**: Many unit tests use `MagicMock` without full spec compliance or with legacy attribute names (`assets` as float instead of `wallet`). This requires careful updating when underlying contracts change.
  - **Configuration Ambiguity**: Config values like `TAX_BRACKETS` or `WEALTH_TAX_THRESHOLD` are implicitly dollars, requiring conversion when comparing against penny-based state. This implicit assumption is a source of bugs.
  ```
- **Reviewer Evaluation**:
  - **정확성 및 깊이**: 제출된 인사이트 보고서는 매우 훌륭합니다. 부동소수점 정밀도 문제라는 핵심 원인을 정확히 파악하고, DTO, 세금, 상속 등 주요 변경 영역을 체계적으로 문서화했습니다.
  - **기술 부채 식별**: 가장 중요한 점은, 해결된 문제뿐만 아니라 여전히 남아있는 기술 부채(정산 시스템과 세금 시스템 간의 단위 불일치)를 명확히 식별하고 기록했다는 것입니다. 이는 시스템에 대한 깊은 이해를 보여주며, 프로젝트의 장기적인 안정성에 기여하는 매우 성숙한 접근 방식입니다.
  - **결론**: 이 보고서는 단순한 작업 요약을 넘어, 시스템의 현재 상태와 나아갈 방향에 대한 깊은 통찰을 제공하는 고품질의 기술 문서입니다.

## 📚 Manual Update Proposal
- 해당 인사이트는 프로젝트의 중요한 기술 부채이므로, 중앙 원장에 기록하여 추적 관리할 것을 제안합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  
  ### ID: TD-234 - Monetary Unit Mismatch (Pennies vs Dollars)
  
  - **현상 (Symptom)**:
    - `TransactionManager` 및 `SettlementSystem`은 모든 금융 거래를 정수(pennies) 단위로 처리하도록 마이그레이션되었음.
    - 그러나 `TaxService` 및 관련 `FiscalPolicyManager`는 여전히 부동소수점(dollars) 단위를 기준으로 세금 구간 및 세율을 계산함.
  
  - **원인 (Cause)**:
    - 시스템 전반의 부동소수점 정밀도 오류를 해결하기 위해 정수 기반의 금융 시스템(pennies)을 도입.
    - 복잡한 재정 정책 로직의 마이그레이션 범위를 현재 미션에서 최소화하기 위해, `TransactionManager`에서 두 단위를 변환하는 '어댑터' 역할을 수행하도록 의도적으로 설계함. (`trade_value / 100.0` 및 `round_to_pennies(tax * 100)`).
  
  - **해결/완화 (Resolution/Mitigation)**:
    - `TransactionManager`가 세금 계산 로직 호출 직전에 달러로 변환하고, 결과값을 다시 페니로 변환하여 일시적으로 문제를 해결함.
  
  - **교훈/장기적 해결책 (Lesson/Long-term Solution)**:
    - 현재의 어댑터 패턴은 단위 불일치로 인한 버그를 방지하는 효과적인 임시방편임.
    - 하지만 장기적으로는 `TaxService`, `FiscalPolicyManager` 및 관련 설정(`TAX_BRACKETS` 등)을 모두 페니 단위로 완벽하게 마이그레이션하여, 불필요한 단위 변환 로직을 제거하고 시스템의 개념적 일관성을 확보해야 함. 이는 코드 복잡도를 낮추고 잠재적인 계산 오류를 원천 차단할 수 있음.
  ```

## ✅ Verdict
**APPROVE**

- 시스템의 안정성을 저해하는 핵심적인 자산 누수 문제를 근본적으로 해결했습니다.
- 변경 사항에 맞춰 관련된 모든 테스트 코드를 꼼꼼하게 수정하여 코드의 신뢰성을 확보했습니다.
- 가장 중요한 점으로, 변경 과정에서 얻은 통찰과 남아있는 기술 부채를 `communications/insights/mission_household_fix.md` 파일에 매우 상세하고 정확하게 기록했습니다. 이는 프로젝트의 유지보수성과 투명성을 크게 향상시키는 모범적인 사례입니다.
