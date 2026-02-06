# 🔍 Summary
이번 변경은 Watchtower 대시보드의 가독성 향상을 목표로 합니다. 주요 경제 지표(GDP, CPI, M2 Leak)에 대한 이동 평균(SMA) 계산 로직을 추가하여 노이즈를 줄였고, 인구 동태 파악을 위해 '출생률(Birth Rate)' 추적 기능을 `AgentRepository` 및 관련 서비스에 새로 구현했습니다. 변경 사항에 대한 단위 테스트와 상세한 기술 인사이트 보고서가 포함되었습니다.

## 🚨 Critical Issues
- **아키텍처 원칙 위반**: `simulation/orchestration/dashboard_service.py` 에서 기능 존재 여부를 확인하기 위해 `hasattr`을 사용했습니다. 이는 프로젝트에서 정의한 `@runtime_checkable` 프로토콜과 `isinstance`를 통한 엄격한 인터페이스 분리 원칙(TD-254 후속 예방)에 위배됩니다. 덕 타이핑(duck typing)은 모듈 간의 결합도를 높여 장기적인 유지보수를 어렵게 만듭니다.
  - **위치**: `dashboard_service.py` L30, L48, L139
  - **예시**: `if hasattr(tracker, "get_smoothed_values"):`

## ⚠️ Logic & Spec Gaps
- 발견된 사항 없음. 핵심 로직(SMA 계산, 출생자 수 SQL 쿼리)은 명세에 부합하며, 신규 단위 테스트를 통해 검증되었습니다.

## 💡 Suggestions
- `hasattr` 대신, `EconomicIndicatorTracker`와 `AgentRepository`가 구현해야 할 `Protocol`을 정의하고 `DashboardService`에서 `isinstance`로 타입을 확인하는 방식으로 리팩토링할 것을 강력히 권장합니다. 이는 아키텍처의 견고성을 유지하고 향후 발생할 수 있는 유사한 문제를 예방합니다.
- `agent_repository.py`의 `get_birth_counts` 함수에서 `run_id`에 따른 동적 쿼리 생성이 여러 `if run_id:` 블록으로 나뉘어 있어 가독성이 다소 저하됩니다. 파라미터 리스트를 한 번에 구성하는 것이 더 깔끔할 수 있습니다. (이는 사소한 제안입니다.)

## 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```
  # Technical Insight Report: Watchtower Hardening (Track A)

  ## 1. Problem Phenomenon
  - Symptoms: The Watchtower Dashboard displayed instantaneous (noisy) values... Demographic metrics were incomplete...
  
  ## 2. Root Cause Analysis
  - Missing Data Processing: The `EconomicIndicatorTracker` only stored raw history...
  - Missing Repository Method: The `AgentRepository` lacked a query method to track "New Agents" (Births)...
  - Service Gap: `DashboardService` was calculating `m2_leak` locally...

  ## 3. Solution Implementation Details
  - A. Tracker Hardening: Added `collections.deque(maxlen=50)`...
  - B. Repository Upgrade: Implemented `get_birth_counts`...
    - Query: SELECT COUNT(DISTINCT agent_id) ... WHERE agent_id NOT IN (...)
  - C. Orchestration Integration: Updated `_finalize_tick`...

  ## 4. Lessons Learned & Technical Debt
  - Performance Risk: The `get_birth_counts` query uses a `NOT IN` subquery which ... may degrade performance...
  - Debt Item (TD-XXX): Add an index on `agent_states(agent_id, time)` or `agent_states(agent_id)`...
  - Metric Definitions: The "Birth" definition is "Net New Survivors". Agents born and died within the same window ... are not counted...
  ```
- **Reviewer Evaluation**:
  - **평가**: **Excellent**. 보고서는 `현상/원인/해결/교훈` 형식을 완벽하게 준수하며, 코드 변경 사항을 정확히 기술하고 있습니다.
  - **가치**: 특히 "Lessons Learned" 섹션이 매우 인상적입니다. `NOT IN`을 사용한 SQL 쿼리의 잠재적 성능 저하를 스스로 식별하고, `agent_states` 테이블에 대한 인덱스 추가를 기술 부채로 구체적으로 제안한 점은 수석 리뷰어로서 높이 평가합니다. 또한 '출생'의 비즈니스적 정의(`Net New Survivors`)를 명확히 하여 매크로 지표의 한계를 명시한 부분은 시스템에 대한 깊은 이해를 보여줍니다.

## 📚 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**: 인사이트 보고서에서 식별된 기술 부채를 중앙 원장에 기록할 것을 제안합니다.

```markdown
## TD-XXX: `agent_states` 테이블 인덱스 부재로 인한 성능 저하 위험

- **현상**: `AgentRepository.get_birth_counts` 함수는 `NOT IN` 서브쿼리를 사용하여 특정 기간 동안 새로 생성된 에이전트를 계산합니다.
- **위험**: `agent_states` 테이블의 크기가 증가할수록 `agent_id`를 기준으로 하는 서브쿼리의 성능이 심각하게 저하될 수 있습니다. (O(N*M))
- **해결책**: `agent_states(agent_id, time)` 또는 최소 `agent_states(agent_id)`에 대한 데이터베이스 인덱스를 추가하여 에이전트 존재 여부 확인 비용을 최적화해야 합니다.
- **출처**: `communications/insights/mission_watchtower_hardening.md`
```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

**사유**: 코드의 기능적 완성도와 테스트 커버리지, 특히 상세한 인사이트 보고서 작성은 매우 훌륭합니다. 그러나 `hasattr`의 사용은 명시적으로 금지된 아키텍처 원칙을 위반하는 심각한 문제입니다. 제안된 대로 `Protocol`과 `isinstance`를 사용하도록 수정한 후 다시 제출해 주십시오. 아키텍처 일관성을 유지하는 것은 장기적인 프로젝트 안정성에 매우 중요합니다.
