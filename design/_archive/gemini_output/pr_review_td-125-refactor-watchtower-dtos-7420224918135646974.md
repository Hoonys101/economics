🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\design\_archive\gemini_output\pr_diff_td-125-refactor-watchtower-dtos-7420224918135646974.txt
🚀 [GeminiWorker] Running task with manual: git_reviewer.md

📝 [Review Report]
============================================================
# 🔍 Summary
`Watchtower`의 데이터 전송 객체(DTO)를 프론트엔드 v2 규격에 맞게 리팩토링하고, `EconomicIndicatorTracker`에 Gini 계수, 사회 통합, 주식 가치를 포함한 자산 계산 등 핵심 경제 지표를 중앙화했습니다. 이 과정에서 기존 `SnapshotViewModel`을 제거하고 신규 검증 스크립트를 추가하여 코드의 정확성과 유지보수성을 크게 향상시켰습니다.

# 🚨 Critical Issues
- 발견되지 않았습니다. API 키, 비밀번호 등의 하드코딩이나 심각한 보안 취약점은 없습니다.

# ⚠️ Logic & Spec Gaps
1.  **Hardcoded & Heuristic Values**: `simulation/orchestration/dashboard_service.py` 파일 내에 일부 값이 하드코딩되거나 휴리스틱에 의존하고 있습니다. 이는 개발자 본인이 인사이트 보고서에 명시했으나, 코드 리뷰 차원에서 다시 한번 지적합니다.
    - `status="RUNNING"`: 시뮬레이션의 실제 상태를 반영하지 않고 항상 "RUNNING"으로 고정되어 있습니다.
    - `m0 = m2 * 0.2`, `m1 = m2 * 0.8`: M0, M1 통화 공급량이 M2를 기반으로 한 단순 추정치입니다.
    - `approval_low`, `approval_mid`, `approval_high`가 `approval_total` 값으로 동일하게 채워지고 있습니다.

2.  **Test Suite Integration**: 기존 `test_dashboard_api.py`가 삭제된 것은 타당하나, 새로 추가된 `verification/verify_dto_structure.py`와 `verification/verify_metrics_logic.py` 스크립트가 표준 `pytest` 테스트 스위트(`tests/` 폴더)에 포함되어 있지 않습니다. 이로 인해 CI/CD 파이프라인에서 자동 실행되지 않을 수 있습니다.

# 💡 Suggestions
1.  **Test Integration**: `verification/` 디렉토리의 검증 스크립트들을 `tests/` 디렉토리로 통합하여, `pytest` 실행 시 다른 유닛 테스트와 함께 자동으로 검증되도록 하는 것을 권장합니다. 이는 지속적인 통합 과정에서 회귀(regression)를 방지하는 데 도움이 됩니다.
2.  **Debt Follow-up**: 인사이트 보고서에 언급된 기술 부채(로직 중복, 하드코딩 등)에 대한 후속 작업을 위한 별도의 기술 부채 티켓(e.g., TD-XXX)을 생성하여 관리하는 것을 고려해 보십시오.

# 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```markdown
  # TD-125 & TD-015: Watchtower Backend Refactoring & Metrics Centralization

  ## Overview
  Refactored the Watchtower backend to align with the "Golden Sample v2" frontend contract (TD-125) and centralized key economic metrics into `EconomicIndicatorTracker` (TD-015).

  ## Changes Implemented
  1.  **DTO Standardization (`simulation/dtos/watchtower.py`)**:
      - Replaced the previous DTO structure with `WatchtowerSnapshotDTO`, exactly matching the fields and nesting of `watchtower_full_mock_v2.json`.
      - Used nested dataclasses (`IntegrityDTO`, `MacroDTO`, `FinanceDTO`, `PoliticsDTO`, `PopulationDTO`) for strict typing.
      - Removed legacy DTOs (`DashboardSnapshotDTO`, etc.) from `simulation/dtos/api.py`.
      - Removed legacy `SnapshotViewModel` and its tests.

  2.  **Metrics Centralization (`simulation/metrics/economic_tracker.py`)**:
      - Enhanced `EconomicIndicatorTracker` to calculate:
          - **Gini Coefficient**: Implemented directly.
          - **Social Cohesion**: Aggregated from `Household` political trust scores.
          - **Nominal GDP**: Explicitly tracked alongside production volume.
          - **Population Metrics**: Active population count and wealth quintile distribution.
          - **Total Wealth**: now calculates **Cash + Stock Portfolio Value** for accurate inequality tracking.
      - Updated `track()` method to calculate and store these metrics every tick.

  3.  **Dashboard Integration (`simulation/orchestration/dashboard_service.py`)**:
      - Updated to populate `WatchtowerSnapshotDTO` using the centralized data from `EconomicIndicatorTracker`.
      - Ensures Single Source of Truth (SSoT) for dashboard metrics.

  ## Technical Debt & Observations

  ### Resolved
  - **DTO Mismatch**: Backend now produces JSON structure identical to what the frontend expects.
  - **Scattered Metrics**: Critical indicators (Gini, Cohesion) are no longer calculated ad-hoc.
  - **Wealth Calculation**: Gini/Quintiles now correctly include stock portfolio value, resolving a regression risk.

  ### Remaining / New Debt
  1.  **Logic Duplication**: `InequalityTracker` (`simulation/metrics/inequality_tracker.py`) still exists. Future work should consolidate it.
  2.  **Political Granularity**: `DashboardService` populates low/mid/high approval with the total average.
  3.  **Money Supply Definitions**: `M0` and `M1` are currently estimated heuristics.
  4.  **Server Status**: The `status` field in the snapshot is hardcoded to `"RUNNING"`.

  ## Verification
  - **DTO Structure**: Verified via script against `watchtower_full_mock_v2.json`.
  - **Metrics Logic**: Verified via unit tests with mock agents for Gini, Cohesion, and Population quintiles (including stock value).
  ```
- **Reviewer Evaluation**:
  - **Value**: 매우 훌륭한 인사이트 보고서입니다. 변경 사항을 명확히 요약하고, 해결된 기술 부채와 새로 발생한 부채(하드코딩, 로직 중복 등)를 스스로 식별하고 정직하게 문서화한 점이 인상적입니다. 특히 불평등 지표 계산 시 **주식 포트폴리오 가치를 포함**하도록 수정한 것은 매우 중요한 개선이며, 이를 명시적으로 기록한 것이 좋습니다.
  - **Format**: `현상/원인/해결/교훈`의 표준 형식을 따르지는 않았지만, "Resolved"와 "Remaining / New Debt" 섹션을 통해 그에 준하는 정보를 효과적으로 전달하고 있습니다.
  - **Conclusion**: 이 보고서는 단순한 변경 로그를 넘어, 작업의 맥락과 그로 인한 기술적 영향을 깊이 이해하고 있음을 보여주는 모범적인 사례입니다.

# 📚 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  - **ID**: TD-125-1
    **현상**: `DashboardService`가 Watchtower DTO를 채울 때, 시뮬레이션 상태(`status`), 통화 공급량(`M0`, `M1`), 계층별 정치 지지도(`approval_low/mid/high`)에 대해 하드코딩된 값이나 임시 휴리스틱을 사용합니다.
    **원인**: 프론트엔드 계약을 빠르게 만족시키기 위해 임시 데이터를 우선 사용했으며, 해당 지표들을 실시간으로 계산하는 로직이 아직 중앙 트래커에 완전히 통합되지 않았습니다.
    **해결**: 1. 시뮬레이션 엔진의 실제 상태(Running, Paused, Done)를 조회하는 메커니즘을 `DashboardService`에 연결합니다. 2. `EconomicIndicatorTracker`에 정확한 M0, M1 계산 로직을 추가합니다. 3. 가계 자산 분위(quintile)에 따라 정치 지지도를 집계하는 로직을 구현합니다.
    **교훈**: UI와 백엔드 간의 계약 기반 개발 시, 데이터가 아직 준비되지 않은 필드는 명확한 기술 부채로 식별하고 문서화해야 합니다. 이는 빠른 프로토타이핑을 가능하게 하면서도 장기적인 코드 품질 저하를 방지합니다.
  ---
  - **ID**: TD-015-1
    **현상**: 불평등 지표(Gini, Quintiles) 계산 시, 이전 버전에서는 가계의 현금성 자산만 고려하여 부의 불평등을 과소평가하는 오류가 있었습니다.
    **원인**: 자산 계산 로직에서 주식 시장 도입 이후 `portfolio`에 저장된 주식 가치를 합산하는 부분이 누락되었습니다.
    **해결**: `EconomicIndicatorTracker.calculate_population_metrics` 메소드 내에서 각 가계의 총자산을 계산할 때, 현금 자산(`cash_val`)과 주식 포트폴리오 평가액(`stock_val`)을 모두 합산하도록 수정했습니다.
    **교훈**: 새로운 금융 상품(주식, 채권 등)이 시스템에 도입될 때, 부(Wealth), 자산(Assets)과 관련된 모든 핵심 지표 계산 로직을 반드시 검토하고 업데이트해야 합니다. 그렇지 않으면 경제 지표에 심각한 왜곡이 발생할 수 있습니다.
  ```

# ✅ Verdict
**APPROVE**

매우 인상적인 작업입니다. DTO 계약을 정확히 이행하고, 흩어져 있던 지표 계산 로직을 중앙화하여 코드 품질을 크게 개선했습니다. 무엇보다 스스로 기술 부채를 명확히 식별하고 문서화한 점을 높이 평가합니다. 제안된 사항들을 후속 작업에서 처리해 주시기 바랍니다.

============================================================
