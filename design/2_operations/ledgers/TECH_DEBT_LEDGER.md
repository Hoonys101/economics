# Technical Debt Ledger

## 🔴 Active Technical Debt

### [Domain: Agents & Orchestration]

*   **ID: TD-259 (Government Agent Monolith)**
    *   **현상 (Phenomenon)**: `Government`는 여전히 거대 상속 클래스로 남아있음.
    *   **기술 부채 (Tech Debt)**: 모든 로직이 하나의 클래스에 몰려 있어 확장이 어려움.
    *   **해결 방안 (Resolution)**: `Firm`과 같은 Orchestrator-Engine 구조로 리팩토링 필요.

*   **ID: TD-260 (Household Agent Complexity)**
    *   **현상 (Phenomenon)**: `Household` 내부가 과도한 Mixin으로 복잡함.
    *   **기술 부채 (Tech Debt)**: 상태와 로직의 경계가 모호하여 유지보수 비용 증대.
    *   **해결 방안 (Resolution)**: 하위 시스템(NeedsManager 등)으로 추가 분해 고려.

### [Domain: Systems & Infrastructure]

*   **ID: TD-261 (Bank Domain Purification)**
    *   **현상 (Phenomenon)**: `Bank` Facade가 여전히 비금융 "Consequence" 로직(XP 패널티 등)을 처리함.
    *   **기술 부채 (Tech Debt)**: 은행 본연의 기능(예금/예출) 외의 책임이 섞여 있음.
    *   **해결 방안 (Resolution)**: 해당 로직을 `JudicialSystem` 등으로 이관.



*   **ID: TD-269 (Liquidation Manager Legacy Debt)**
    *   **현상 (Phenomenon)**: `LiquidationManager` 및 `audit_zero_sum.py`가 `Firm` 에이전트의 예전 `finance` 속성에 의존함.
    *   **기술 부채 (Tech Debt)**: `Firm`이 Composition 구조로 리팩토링된 이후 정합성 검증 스크립트 실패 유발.
    *   **해결 방안 (Resolution)**: `LiquidationManager`가 프로토콜 인터페이스를 통해 금융 상태에 접근하도록 리팩토링.

---

---

## ✅ Resolved Technical Debt

| ID | Module / Component | Description | Resolution Session | Insight Report |
| :--- | :--- | :--- | :--- | :--- |
| **TD-255** | Tests / Simulation | Mock Fragility - Internal patching 제거 | PH10.1 | [Insight](file:///c:/coding/economics/communications/insights/TD-255_TD-256_TD-257_Stabilization.md) |
| **TD-256** | Lifecycle Manager | `FinanceState` 내 dynamic hasattr 체크 제거 | PH10.1 | [Insight](file:///c:/coding/economics/communications/insights/TD-255_TD-256_TD-257_Stabilization.md) |
| **TD-257** | Finance Engine | 하드코딩된 unit cost(5.0) 설정값으로 이관 | PH10.1 | [Insight](file:///c:/coding/economics/communications/insights/TD-255_TD-256_TD-257_Stabilization.md) |
| **TD-258** | Command Bus | Orchestrator-Engine 시그니처 정규화 | PH10.1 | [Insight](file:///c:/coding/economics/communications/insights/TD-255_TD-256_TD-257_Stabilization.md) |
| **TD-PH10** | Core Agents | `BaseAgent.py` 완전 퇴역 및 삭제 | PH10 | [Insight](file:///c:/coding/economics/communications/insights/PH9.3-STRUCTURAL-PURITY.md) |
| **TD-PROX** | Firms | `HRProxy`, `FinanceProxy` 삭제 | PH10 | [Insight](file:///c:/coding/economics/communications/insights/PH9.2_Firm_Core_Protocol_Enforcement.md) |
| **TD-DTO** | Orders | `OrderDTO` 인터페이스 표준화 | PH9.3 | [Insight](file:///c:/coding/economics/communications/insights/hr_finance_decouple_insight.md) |
| **TD-268** | Core Agents | `BaseAgent` 상속 구조 제거 시작 | PH9.3 | [Insight](file:///c:/coding/economics/communications/insights/TD-268_BaseAgent_Refactor.md) |
| **TD-ANL** | Analytics | 에이전트 내부 접근 대신 DTO Snapshot 사용 | PH10 | [Insight](file:///c:/coding/economics/communications/insights/PH9.2_Firm_Core_Protocol_Enforcement.md) |
| **TD-262** | Scripts | BaseAgent 제거 이후 깨진 검증 스크립트 복구 | PH10 | [Insight](file:///c:/coding/economics/design/_archive/gemini_output/pr_review_bundle-purity-regression-1978915247438186068.md) |
| **TD-DTO-CONTRACT** | Simulation | DTO 필드명 변경 시 발생한 contract 불일치 해결 | PH10 | [Insight](file:///c:/coding/economics/design/_archive/gemini_output/pr_review_bundle-purity-regression-1978915247438186068.md) |
| **TD-263** | Scripts / Maintenance | Report Harvester 누락 경로 반영 및 원격 브랜치 청소 로직 최적화 | PH10.1 | [Log](./design/2_operations/ledgers/INBOUND_REPORTS.md) |
| **TD-264** | Financials | `SettlementSystem` 우회 코드 제거 및 `IFinancialAgent` 도입 | PH9.2 | [Insight](./communications/insights/PH9.2_TrackA.md) |
| **TD-265** | Sensory | `SensorySystem` 캡슐화 파괴 해결 및 DTO 전환 | PH9.2 | [Insight](./communications/insights/PH9.2_TrackB_SensoryPurity.md) |
| **TD-266** | Markets | `CanonicalOrderDTO` 도입 및 주문 파편화 해소 | PH9.2 | [Insight](./communications/insights/PH9.2_Market_DTO_Unification.md) |
| **TD-267** | Governance | `ARCH_AGENTS.md` 아키텍처 문서 동기화 | PH9.2 | [Spec](../3_work_artifacts/specs/spec_ph9_2_interface_purity.md) |
