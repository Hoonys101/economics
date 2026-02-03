# 🔍 Summary

본 변경 사항은 기존의 단순 `Order` 기반 주택 구매 로직을 트랜잭션의 원자성을 보장하는 **Saga 패턴 기반의 주택 구매 오케스트레이션**으로 전환하는 대규모 아키텍처 개선입니다. `HousingTransactionSagaHandler`를 도입하여 대출 신청, 계약금 지불, 대출금 지급, 소유권 이전까지의 복잡한 과정을 단계별로 관리하며, 실패 시 롤백을 통해 금융 시스템의 정합성을 보장합니다.

# 🚨 Critical Issues

**없음.**

- **보안**: API 키, 시스템 경로 등의 하드코딩이 발견되지 않았습니다.
- **Zero-Sum**: `HousingTransactionSagaHandler` 내 자금 이체 로직과 롤백(`_rollback_down_payment`, `_rollback_loan`) 로직이 `settlement_system`을 통해 구현되어 있으며, 자금의 생성/소멸 없이 정확하게 처리되는 것으로 보입니다.

# ⚠️ Logic & Spec Gaps

- **(Minor)** `modules/market/housing_planner.py`의 `_parse_unit_id` 함수에서 ID 파싱 실패 시 `except: return 0`으로 처리하는 부분은 잠재적 위험이 있습니다. 만약 유효하지 않은 `unit_id`가 입력되면 항상 `property_id=0`에 대한 구매를 시도하게 될 수 있으며, 오류가 조용히 무시됩니다. 예외 처리를 더 명시적으로 하고 오류를 로깅하는 것이 안전합니다.
- **(Minor)** `modules/household/decision_unit.py`에서 `housing_system`이 없을 경우 `pass`로 조용히 넘어가는데, 이는 구매 결정이 아무런 행동 없이 무시되는 것을 의미합니다. 잠재적인 문제를 진단하기 위해 경고 로그(`logger.warning`)를 추가하는 것이 좋습니다.
- **(Minor)** `modules/finance/saga_handler.py`의 `_handle_initiated` 함수에서 대출 기간(`loan_term=360`)이 하드코딩되어 있습니다. 이 값은 주택이나 대출 상품의 특성에 따라 달라질 수 있으므로, 설정 파일(`config`)에서 가져오거나 `MortgageApplicationDTO`의 일부로 전달받는 것이 더 유연한 설계입니다.

# 💡 Suggestions

- **(Performance)** `modules/finance/saga_handler.py`의 `_handle_initiated` 함수에서 판매자 ID를 찾기 위해 `self.simulation.real_estate_units` 리스트 전체를 순회합니다. 부동산 유닛이 많아질 경우 성능 저하가 발생할 수 있습니다. `simulation` 레벨에서 부동산 ID를 키로 하는 딕셔너리(해시맵)를 유지하여 O(1) 시간 복잡도로 조회할 수 있도록 개선하는 것을 고려해 보십시오.
- **(Robustness)** `simulation/loan_market.py`의 `request_mortgage` 함수에서 `loan_id` 파싱 실패 시 `hash(loan_info['loan_id']) % 10000000`를 사용한 폴백(fallback) 로직은 드물지만 해시 충돌의 가능성이 있습니다. Loan ID가 시스템 전반에서 고유하게 유지되는 것이 중요하다면, UUID를 사용하거나 Bank에서 발급하는 ID가 항상 파싱 가능한 형식을 갖도록 강제하는 것이 더 안정적입니다.

# 🧠 Manual Update Proposal

이번 변경은 **"에이전트는 Order만 반환한다"** 는 기존의 핵심 아키텍처 원칙에서 벗어나는 중요한 결정이므로, 반드시 관련 내용을 기술 부채 대장(Ledger)에 기록하여 모든 팀원이 인지할 수 있도록 해야 합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  
  ### ID: TD-015 - Housing Purchase via Saga Pattern (Bypassing Order System)
  
  *   **Date**: 2026-02-03
  *   **Author**: Gemini
  *   **Context**:
      *   주택 구매와 같이 여러 단계의 금융 트랜잭션(대출, 계약금, 잔금)이 얽힌 복잡한 상호작용은 단일 `Order` 객체로 표현하기 어렵고, 원자성을 보장할 수 없습니다.
      *   **Mission `H1-V2`** 에서 이 문제를 해결하기 위해 Saga 패턴(`HousingTransactionSagaHandler`)을 도입했습니다.
  *   **Debt Incurred (The "What")**:
      *   `DecisionUnit`이 `BUY` `Order`를 반환하는 대신, `HousingSystem.initiate_purchase`를 직접 호출하여 Saga를 시작합니다.
      *   이는 "에이전트는 상태 변경을 직접 수행하지 않고 오직 `Order`를 통해 의도를 표현한다"는 기존의 핵심 아키텍처 원칙에서 벗어나는 예외 사례입니다.
  *   **Reasoning (The "Why")**:
      *   Saga 패턴은 복잡한 분산 트랜잭션의 상태 관리와 롤백을 오케스트레이션하여 데이터 정합성을 보장하는 강력한 방법입니다.
      *   기존 `Order` 시스템을 수정하여 Saga를 지원하도록 하는 것은 과도한 복잡성을 야기하므로, 별도의 핸들러를 통한 직접 호출(Method Dispatch) 방식을 선택했습니다.
  *   **Repayment Plan (The "How")**:
      *   현재로서는 상환 계획이 없습니다. 이 패턴은 향후 다른 복잡한 트랜잭션(예: 기업 M&A)에도 재사용될 수 있는 표준으로 간주될 수 있습니다.
      *   단, 이와 같은 예외가 무분별하게 확산되지 않도록 엄격한 아키텍처 리뷰를 거쳐야 합니다.
  *   **Linked Insight**: `communications/insights/H1-V2.md`
  
  ---
  ```

# ✅ Verdict

**APPROVE**

- 이번 변경은 복잡한 금융 트랜잭션의 원자성을 보장하기 위한 사려 깊은 아키텍처 개선입니다.
- 가장 중요한 요구사항인 **인사이트 보고서(`communications/insights/H1-V2.md`)가 상세하고 명확하게 작성**되었으며, 기술 부채와 아키텍처 변경의 이유를 투명하게 공유했습니다.
- 원자성 보장을 위한 롤백 로직이 검증 스크립트(`verify_atomic_housing_purchase.py`)를 통해 잘 테스트되었습니다.
- 지적된 이슈들은 마이너하며, 시스템의 안정성을 해치는 수준이 아닙니다. 제안된 내용들을 다음 작업에서 고려해 주십시오.
