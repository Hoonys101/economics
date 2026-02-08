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

*   **ID: TD-264 (Settlement Bypass)**
    *   **현상 (Phenomenon)**: `SettlementSystem`을 우회하여 `agent.assets`에 직접 접근/수정하는 사례 발견.
    *   **기술 부채 (Tech Debt)**: 금융 정합성(Zero-leak) 보장의 불확실성 증대.
    *   **해결 방안 (Resolution)**: 모든 자산 변동을 `SettlementSystem` API로 강제 통일. [Spec](../3_work_artifacts/specs/spec_ph9_2_interface_purity.md)

*   **ID: TD-265 (Sensory System Encapsulation)**
    *   **현상 (Phenomenon)**: `SensorySystem`이 에이전트의 `_econ_state` 등 내부 속성에 직접 접근.
    *   **기술 부채 (Tech Debt)**: DTO/Protocol 기반의 관찰 계층 설계 원칙 위반.
    *   **해결 방안 (Resolution)**: 공인된 DTO Snapshot만을 통해 데이터를 수집하도록 리팩토링. [Spec](../3_work_artifacts/specs/spec_ph9_2_interface_purity.md)

*   **ID: TD-266 (Dual Order DTO Fragmentation)**
    *   **현상 (Phenomenon)**: `simulation.models.Order`와 `modules.market.api.OrderDTO`가 혼재되어 사용됨.
    *   **기술 부채 (Tech Debt)**: 마켓 유형별 구현의 비일관성 및 유지보수 복잡성.
    *   **해결 방안 (Resolution)**: 단일화된 `Order` DTO 프로토콜 정의 및 적용. [Spec](../3_work_artifacts/specs/spec_ph9_2_interface_purity.md)

*   **ID: TD-267 (Architectural Doc Sync)**
    *   **현상 (Phenomenon)**: `ARCH_AGENTS.md`가 실제 구현(Stateless Engine)과 다른 구조(Stateful Parent Pointer)를 서술함.
    *   **기술 부채 (Tech Debt)**: 설계 문서와 코드 간의 불일치로 인한 오해 유발.
    *   **해결 방안 (Resolution)**: 아키텍처 문서를 현재의 패턴에 맞게 업데이트. [Spec](../3_work_artifacts/specs/spec_ph9_2_interface_purity.md)

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
