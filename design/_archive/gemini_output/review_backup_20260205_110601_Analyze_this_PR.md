# 🔍 Summary
이번 변경은 시뮬레이션의 실시간 데이터를 외부로 스트리밍하기 위한 `Watchtower` 대시보드 백엔드 서버를 구현합니다. `FastAPI`와 `WebSocket`을 사용하여 새로운 `server.py`가 추가되었으며, 시뮬레이션 상태를 집계하는 `DashboardService`와 데이터 전송 규격인 `DashboardSnapshotDTO`가 정의되었습니다. 또한, 구현 과정에서 발견된 아키텍처상의 잠재적 문제점들을 기록한 상세한 인사이트 보고서가 포함되었습니다.

# 🚨 Critical Issues
- 발견되지 않았습니다. 보안 및 하드코딩 관련 위반 사항이 없습니다.

# ⚠️ Logic & Spec Gaps
- **데이터 일관성 위험 (Risk of Data Inconsistency)**: `communications/insights/PH6_Watchtower.md` 보고서에서 지적된 바와 같이, M2 Leak, 인플레이션 등 주요 거시 경제 지표를 산출하는 소스가 `EconomicIndicatorTracker`와 `Government`의 `sensory_data`로 이원화되어 있습니다. 현재 구현은 `Government`의 데이터를 우선적으로 사용하지만, 두 소스 간의 동기화가 완벽하지 않을 경우 데이터 불일치가 발생할 수 있습니다. 이는 버그는 아니지만 시스템 레벨의 잠재적 문제입니다.
- **임시 지표 사용 (Placeholder Metric)**: `simulation/orchestration/dashboard_service.py`의 `get_snapshot` 함수 내에서 `social_cohesion` 지표가 `gov.approval_rating`을 임시로 사용(`Proxy for now`)하고 있습니다. 이 지표는 추후 별도의 로직으로 구현되어야 합니다.

# 💡 Suggestions
- **서버 바인딩 주소 (Server Binding Address)**: `server.py`의 `uvicorn.run` 호출 시 `host="0.0.0.0"`으로 설정되어 있습니다. 이는 컨테이너 환경에서는 일반적이지만, 직접 배포 시에는 보안을 위해 방화벽 설정이 필수적이거나, 더 구체적인 인터페이스(예: `localhost`)에 바인딩하는 것을 고려해야 합니다.
- **FPS 계산 위치 (FPS Calculation Locus)**: 인사이트 보고서에서도 언급되었듯이, FPS(Frames Per Second)가 `DashboardService` 레벨에서 계산되고 있습니다. 더 정확한 성능 측정을 위해서는 시뮬레이션 엔진(`Simulation` 클래스) 레벨에서 tick 처리 시간을 직접 측정하고 노출하는 것이 바람직합니다.

# 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```
  1.  **M2 Leak Calculation Integrity**:
      - The `TickOrchestrator` performs an M2 integrity check using `baseline_money_supply`... and `government.get_monetary_delta()`.
      - However, `MonetaryLedger.get_monetary_delta()` returns the delta for the *current tick*, not cumulative... the orchestration check might be flawed.
      - In `DashboardService`, `m2_leak` is calculated as: `Current M2 - (Baseline M2 + Cumulative Issued - Cumulative Destroyed)`. This assumes `Baseline M2` is static. This logic should be centralized (e.g., in `IntegritySystem`) to avoid divergence between the Orchestrator check and the Dashboard.

  2.  **Metric Source of Truth**:
      - Macro metrics (Inflation, Gini) are accessed via `Government.sensory_data`...
      - `EconomicIndicatorTracker` also calculates metrics but `DashboardService` prioritizes `Government` sensory data for consistency with agent behavior.
      - This dual-source potential (Tracker vs Gov Sensory) could lead to discrepancies if not synchronized perfectly.
  ```
- **Reviewer Evaluation**:
  - **매우 높은 품질의 인사이트입니다.** 제출된 코드가 당장 버그를 일으키지는 않지만, 시스템이 확장될 경우 발생할 수 있는 심각한 아키텍처적 위험을 정확히 식별했습니다.
  - **'M2 Leak 계산 무결성'** 지적은 동일한 지표(M2 Leak)를 계산하는 두 주체(`TickOrchestrator`와 `DashboardService`)가 서로 다른 방식을 사용하여 결과가 달라질 수 있다는 "계산 분기(Divergence)" 문제를 명확히 짚어냈습니다. 이는 시스템의 신뢰성과 관련된 핵심적인 관찰입니다.
  - **'Metric Source of Truth'** 지적은 데이터의 "진실 공급원(Source of Truth)"이 이원화될 때 발생하는 고전적인 데이터 일관성 문제를 제기합니다. 이는 향후 리팩토링의 필요성을 제기하는 중요한 아키텍처적 부채 식별입니다.
  - 이 보고서는 단순 구현을 넘어, 시스템 전체의 안정성과 확장성을 고려하는 수석 개발자의 관점을 보여줍니다.

# 📚 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**: 위 `Implementation Insight Evaluation`에서 식별된 아키텍처 기술 부채를 원장에 기록할 것을 제안합니다.

  ```markdown
  ---
  id: TD-015
  title: "Divergent Metric Calculation and Dual Sources of Truth"
  status: "OPEN"
  date_identified: "2026-02-05"
  reporter: "Jules (via PH6-Watchtower)"
  severity: "Medium"
  ---

  ### 현상 (Phenomenon)
  - 동일한 핵심 경제 지표(예: M2 Leak)를 계산하는 로직이 시스템 내 여러 위치(`TickOrchestrator`, `DashboardService`)에 분산되어 존재함.
  - 주요 거시 경제 지표의 데이터 소스가 `EconomicIndicatorTracker`와 `Government.sensory_data`로 이원화되어 있음.

  ### 원인 (Cause)
  - 기능 추가 시 기존 로직을 재사용하거나 중앙화하는 대신, 해당 기능 범위 내에서 독립적으로 지표를 계산하는 방식을 택함.
  - 각 모듈(Agent, Tracker, Dashboard)이 필요에 따라 자체적으로 데이터를 계산하거나 캐싱하면서 발생.

  ### 영향 (Impact)
  - 시스템의 각 부분에서 보고하는 동일 지표의 값이 서로 다를 수 있어 데이터 신뢰성 저하.
  - 향후 지표 계산 로직 변경 시, 모든 관련 코드를 찾아 수정해야 하므로 유지보수 비용 증가 및 버그 발생 가능성 증대.

  ### 해결책 제안 (Proposed Solution)
  - 모든 핵심 경제 지표 계산 로직을 `EconomicIndicatorTracker` 또는 별도의 `MetricsSystem`으로 중앙화.
  - 다른 모든 모듈은 중앙화된 서비스에서만 데이터를 조회하도록 리팩토링하여 '단일 진실 공급원(Single Source of Truth)' 원칙을 확립.
  ```

# ✅ Verdict
**APPROVE**

**사유**: 코드의 완성도, 테스트 커버리지, 그리고 무엇보다 시스템의 잠재적 위험을 깊이 있게 분석하고 문서화한 인사이트 보고서의 품질이 매우 뛰어납니다. 제기된 이슈들은 즉각적인 버그가 아닌 아키텍처 개선 사항이므로, 기술 부채로 기록하고 병합을 승인합니다.
