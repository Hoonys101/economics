# 🔍 PR Review: Watchtower Backend & Monetary Metrics Refactor

---

### 1. 🔍 Summary
본 변경 사항은 `DashboardService`의 주요 아키텍처 부채를 해결하는 데 중점을 둡니다. 주요 내용은 다음과 같습니다:
- 기존의 휴리스틱 방식(e.g., `M0 = M2 * 0.2`) 통화량 계산 로직을 `WorldState`의 실제 자산 합계를 기반으로 하는 결정론적 계산 로직으로 대체했습니다.
- `PopulationDTO` 생성 시 필수 인자였던 `distribution`이 누락되었던 버그를 수정하고, 이에 대한 테스트 케이스를 보강했습니다.
- `communications/insights/`에 기술 부채 해결 과정 및 교훈에 대한 상세한 보고서를 추가했습니다.

### 2. 🚨 Critical Issues
- 발견되지 않았습니다. API 키나 시스템 경로 등 민감 정보의 하드코딩은 없었으며, 보안상 즉각적인 조치가 필요한 항목은 없습니다.

### 3. ⚠️ Logic & Spec Gaps
- **M1/M2 동일성 가정**: `economic_tracker.py`에서 M1과 M2를 동일하게 처리(`m1 = m2`)하고 있습니다. 주석에 "현재 모든 예금은 유동성이 높기 때문"이라고 명시되어 있으나, 향후 요구불 예금과 저축성 예금이 분리될 경우 해당 로직의 수정이 필요함을 인지해야 합니다. 현재 시뮬레이션의 범위 내에서는 수용 가능한 단순화입니다.
- **범위 외 변경사항**: `tests/utils/factories.py`에 추가된 `survival_need_death_ticks_threshold` 필드는 본 PR의 핵심 목표(통화량 계산 리팩토링)와 직접적인 관련이 없어 보입니다. 단일 PR은 단일 책임을 갖는 것이 이상적입니다. 기능적으로 문제는 없으나, 커밋 히스토리 관리 측면에서 아쉬운 점입니다.

### 4. 💡 Suggestions
- **M1/M2 계산 로직**: 향후 M1의 정교한 계산(요구불 예금만 집계)이 필요할 경우를 대비하여, `m1 = m2` 라인에 `TODO` 주석과 함께 관련 기술 부채 티켓(e.g., `TD-XXX`)을 명시해두면 추적이 용이할 것입니다.
- **DTO 스키마 자동 검증**: 인사이트 보고서에서 제안된 바와 같이, DTO와 JSON 스키마 간의 불일치를 방지하기 위한 CI/CD 파이프라인 내 자동 검증 테스트를 도입하는 것을 강력히 권장합니다. 이는 이번에 수정된 `PopulationDTO` 버그와 같은 문제를 원천적으로 방지할 수 있습니다.

### 5. 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```
  # Insight: Watchtower Backend Refactor (Mission PH6)

  ## Overview
  This mission focuses on resolving architectural debt in the Watchtower backend, specifically standardizing DTOs and centralizing economic metrics.

  ## Technical Debt Resolved
  - **DTO Standardization (TD-125):** Refactored `simulation/dtos/watchtower.py` to align strictly with `watchtower_full_mock_v2.json`. This eliminates discrepancies between backend data structures and frontend expectations.
  - **Metrics SSoT (TD-015):** Centralized Gini, Social Cohesion, and Monetary Aggregates (M0, M1, M2) calculation in `EconomicIndicatorTracker`. Previously, `DashboardService` relied on heuristics or dispersed logic.
  - **Bug Fix:** Fixed a critical bug in `DashboardService` where `PopulationDTO` was instantiated without the required `distribution` argument.

  ## Insights
  - **Heuristic to Deterministic:** Moved from heuristic M0/M1 calculations (e.g., M0 = M2 * 0.2) to deterministic calculations based on `WorldState` (e.g., M0 = Central Bank Liabilities). This improves simulation accuracy.
  - **Dashboard Service Role:** `DashboardService` is now purely an orchestration layer for the API, delegating all calculation logic to the domain-specific `EconomicIndicatorTracker`. This adheres better to SRP.
  - **Type Safety:** The use of strict DTOs helps catch issues like the missing `distribution` field early if static analysis or correct instantiation checks are used.

  ## Future Recommendations
  - **Automated Schema Validation:** Implement a test that automatically validates DTOs against the JSON schema during CI/CD to prevent regression.
  - **Metric Historicity:** `EconomicIndicatorTracker` currently stores history in memory. For long-running simulations, this should be moved to a database or time-series store.
  ```
- **Reviewer Evaluation**:
  - **정확성**: 변경된 코드의 내용(휴리스틱 제거, DTO 버그 수정, SRP 원칙 적용)을 매우 정확하고 상세하게 기술했습니다.
  - **깊이**: 단순히 "수정했다"에서 그치지 않고, "왜" 수정했는지(Heuristic -> Deterministic), 그로 인해 "무엇이" 좋아졌는지(정확성 향상, SRP 준수)를 명확히 설명하여 기술적 부채 해결의 가치를 잘 보여줍니다.
  - **실용성**: `Future Recommendations`에서 제안한 자동 스키마 검증과 데이터베이스 기반 이력 관리는 프로젝트의 안정성과 확장성을 위해 반드시 고려해야 할 실용적인 제안입니다.
  - **평가**: 매우 우수한 인사이트 보고서입니다. 프로젝트의 기술적 자산을 풍부하게 만드는 모범적인 사례입니다.

### 6. 📚 Manual Update Proposal
해당 미션에서 얻은 귀중한 인사이트를 프로젝트의 중앙 지식 베이스에 통합할 것을 제안합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  ## TD-015: 휴리스틱 경제 지표 계산 로직 제거

  - **현상 (Symptom)**: `DashboardService` 등 여러 위치에서 M0, M1과 같은 핵심 통화 지표를 실제 데이터 합산이 아닌, 다른 지표(M2)에 기반한 임시방편적인 추정치(e.g., `M0 = M2 * 0.2`)로 계산하고 있었음. 이는 시뮬레이션의 정확성을 저해하고 Zero-Sum 원칙을 위반할 소지가 있는 심각한 기술 부채임.
  - **원인 (Cause)**: 초기 프로토타이핑 단계에서 구현의 편의성을 위해 도입된 휴리스틱 로직이 정식 리팩토링 없이 계속 사용됨.
  - **해결 (Resolution)**: `EconomicIndicatorTracker`에 `calculate_monetary_aggregates` 함수를 신설하여, `WorldState` 내 모든 경제 주체(가계, 기업, 정부, 은행)의 지갑(wallet) 자산을 직접 순회하고 합산하여 M0를 계산하는 결정론적 방식으로 변경함.
  - **교훈 (Lesson)**:
    - 핵심 경제 모델 로직에 임시방편적인 휴리스틱을 사용하는 것은 장기적으로 데이터 신뢰성에 심각한 문제를 야기한다.
    - 모든 계산 로직은 단일 책임 원칙(SRP)에 따라 특정 도메인 트래커(`EconomicIndicatorTracker`)에 중앙화하여 관리해야 한다.
  ```

### 7. ✅ Verdict
**APPROVE**

- **사유**: 치명적인 보안 이슈나 로직 오류가 없으며, 오히려 시뮬레이션의 정확성을 크게 향상시키는 중요한 리팩토링을 수행했습니다. 또한, 필수 요구사항인 인사이트 보고서(`communications/insights/*.md`)가 누락 없이 상세하고 정확하게 작성되었습니다. 테스트 케이스 보강까지 완료되어 변경 사항의 안정성을 입증했습니다.
