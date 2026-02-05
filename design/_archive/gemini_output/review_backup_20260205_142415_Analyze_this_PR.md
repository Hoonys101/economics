# 🔍 PR Review: Stress Test & Monetary Integrity Fixes

---

### 1. 🔍 Summary
이번 변경은 시스템의 통화 무결성을 검증하기 위한 100-tick 스트레스 테스트 시나리오를 도입하고, M2(통화량) 계산 시 발생하던 심각한 돈 복사/소멸 버그를 수정하는 데 중점을 둡니다. 주요 수정 사항은 `currency_holders` 리스트를 동기화하여 누락된 에이전트를 M2 계산에 포함시키고, 은행의 채권 매입과 같은 통화 확장/축소 거래를 `MonetaryLedger`가 정확히 추적하도록 개선한 것입니다.

### 2. 🚨 Critical Issues
- **없음**: 보안 취약점, API 키 하드코딩, 시스템 절대 경로 등 즉각적인 수정이 필요한 치명적인 문제는 발견되지 않았습니다.

### 3. ⚠️ Logic & Spec Gaps
- **Conflicting Insight Reports**: PR에 `Bundle_D_Stress_Test.md`와 `mission_report_stress_test.md` 두 개의 인사이트 보고서가 포함되어 있습니다. 두 보고서는 동일한 작업을 다루는 것으로 보이지만, 보고하는 잔여 누수(leak) 금액이 다릅니다.
    - `Bundle_D...`: `-46.7290`의 누수를 보고하며, 2개 가구의 인프라 지출과 관련이 있다고 분석합니다.
    - `mission_report...`: `~ -71,328.04`의 잔차(variance)를 보고하며, 기업 운영 비용 문제로 추정합니다.
    - 이처럼 상충하는 두 개의 보고서는 혼란을 야기하며, 단일하고 명확한 분석 결과를 제공해야 한다는 원칙에 위배됩니다.

### 4. 💡 Suggestions
- **Consolidate Insight Reports**: 두 개의 상충되는 보고서를 하나의 최종적이고 일관된 문서로 통합해야 합니다.
- **Adopt SSoT for Currency Holders**: `Bundle_D` 보고서에서 제안한 것처럼, 별도의 `currency_holders` 리스트를 유지하는 대신 `state.agents`를 단일 진실 공급원(SSoT)으로 삼고 `isinstance(agent, ICurrencyHolder)`로 필터링하는 아키텍처 리팩토링을 다음 단계에서 우선적으로 고려해야 합니다. 현재의 `_rebuild_currency_holders` 함수는 훌륭한 임시 해결책이지만, 근본적인 해결책은 리스트 자체를 제거하는 것입니다.
- **Type Safety in `settlement_system.py`**: `_create_transaction_record` 함수가 `dict` 대신 `Transaction` 객체를 반환하도록 변경된 것은 타입 안전성을 높이는 매우 좋은 개선입니다. 이 패턴을 코드베이스 전체의 유사한 팩토리 함수에 일관되게 적용하는 것을 권장합니다.

### 5. 🧠 Implementation Insight Evaluation
- **Original Insight**: (`Bundle_D_Stress_Test.md` 인용)
  > **Root Cause Analysis (Hypothesis)**
  > 1.  **Missing Agents in M2**: `M2_BREAKDOWN` shows `CurHolders: 234`... This count implies Government and Bank might be missing...
  > 2.  **Synchronization Gap**: `InfrastructureManager` distributes to `active_households` (214). If `currency_holders` has 212 Households... Transfer Gov -> Missing HH. Gov Assets (Visible) Decrease. Missing HH Assets (Invisible) Increase. **Result**: M2 Drop.
- **Reviewer Evaluation**:
  - 작성된 분석은 매우 훌륭하며, M2 총량 계산에서 에이전트 리스트의 비동기화 문제로 인해 돈이 사라지는 것처럼 보이는 현상의 근본 원인을 정확하게 짚어냈습니다. `state.agents`를 단일 진실 공급원으로 사용해야 한다는 결론은 아키텍처적으로 올바른 방향입니다.
  - 또한, 중앙은행이나 시중은행의 특정 금융 활동(예: OMO)이 M2에 미치는 영향을 명시적으로 `money_creation`이나 `is_monetary_expansion`으로 태그하도록 수정한 것은 통화 흐름 추적의 정확성을 크게 향상시키는 핵심적인 개선입니다.

### 6. 📚 Manual Update Proposal
해결된 버그는 시스템의 제로섬(Zero-Sum) 무결성과 직결되는 중요한 기술 부채였습니다. 이 지식을 프로젝트의 공식 원장에 기록하여 재발을 방지해야 합니다.
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  - **ID**: TD-028
    **Status**: Resolved
    **Date First Observed**: 2026-02-05
    **Description**: M2(통화량) 계산 시, `state.currency_holders` 리스트와 실제 활성 에이전트(`state.agents`) 사이에 불일치가 발생하여 돈이 누수되는 것처럼 보이는 현상. 특정 에이전트(예: 새로 생성된 가구, 시스템 에이전트)가 `currency_holders`에 즉시 추가되지 않아, 이들에게 송금 시 M2 총량이 감소하는 버그.
    **Root Cause**: `currency_holders`라는 별도의 상태를 유지하여 발생한 동기화 문제.
    **Resolution**: 매 틱(tick)마다 M2를 계산하기 직전에 `state.agents`를 기준으로 `currency_holders` 리스트를 강제로 재빌드하는 `_rebuild_currency_holders` 로직을 추가함. (WO-220)
    **Lesson Learned**: 시스템의 자원 총량을 계산할 때는 분리된 하위 리스트 대신, 항상 단일 진실 공급원(Single Source of Truth)을 기준으로 실시간으로 필터링해야 한다.
  ```

### 7. ✅ Verdict
- **REQUEST CHANGES (Hard-Fail)**
  - **Reason**: 코드의 로직 자체는 매우 훌륭하며 중요한 버그를 수정했습니다. 그러나 **두 개의 상충하는 인사이트 보고서가 제출된 것**은 심각한 절차적 문제입니다. 분석 결과가 일관되지 않아 현재 시스템의 정확한 상태를 파악하기 어렵습니다. 두 보고서를 하나로 통합하고, 잔여 누수량에 대한 단일하고 명확한 결론을 제출해주십시오. 인사이트 보고는 코드만큼이나 중요한 산출물입니다.
