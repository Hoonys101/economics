# Technical Debt Ledger

## 🔴 Active Technical Debt


### [Domain: Agents & Orchestration]


### [Domain: Systems & Infrastructure]

*   **ID: TD-FIN-PURE (FinanceSystem Pure Service)**
    *   **현상 (Phenomenon)**: `FinanceSystem` 구현이 여전히 상태 변경 로직과 트랜잭션 생성을 혼합하여 반환(`grant_bailout_loan`).
    *   **기술 부채 (Tech Debt)**: Service 계층의 순수성 위반. Orchestrator가 반환값을 재처리해야 하는 번거로움.
    *   **해결 방안 (Resolution)**: Stateless Service로 전환하고 명확한 DTO를 반환하도록 리팩토링.
    *   **Origin**: TD-259 Review

*   **ID: TD-JUD-ASSET (Judicial Asset Seizure Granularity)**
    *   **현상 (Phenomenon)**: `JudicialSystem`의 자산 압류 로직이 "All-or-Nothing" 방식으로 구현됨.
    *   **기술 부채 (Tech Debt)**: 부분 압류나 자산 유형별 우선순위 지정 불가.
    *   **해결 방안 (Resolution)**: 압류 목표액 및 우선순위 규칙을 정교화.
    *   **Origin**: TD-261 Review

*   **ID: TD-LIQ-INV (InventoryHandler Config Protocol)**
    *   **현상 (Phenomenon)**: `InventoryLiquidationHandler`가 여전히 `getattr(agent, 'config')`를 사용하여 설정에 접근.
    *   **기술 부채 (Tech Debt)**: Protocol Purity 위반. 런타임 오류 위험.
    *   **해결 방안 (Resolution)**: `IConfigurable` 프로토콜 도입하여 접근 정규화.
    *   **Origin**: TD-269 Review

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
| **TD-264** | Financials | `SettlementSystem` 우회 코드 제거 및 `IFinancialAgent` 도입 | PH9.2 | [Insight](file:///c:/coding/economics/design/_archive/insights/PH9.2_TrackA.md) |
| **TD-265** | Sensory | `SensorySystem` 캡슐화 파괴 해결 및 DTO 전환 | PH9.2 | [Insight](file:///c:/coding/economics/design/_archive/insights/PH9.2_TrackB_SensoryPurity.md) |
| **TD-266** | Markets | `CanonicalOrderDTO` 도입 및 주문 파편화 해소 | PH9.2 | [Insight](file:///c:/coding/economics/design/_archive/insights/PH9.2_Market_DTO_Unification.md) |
| **TD-267** | Governance | `ARCH_AGENTS.md` 아키텍처 문서 동기화 | PH9.2 | [Spec](../3_work_artifacts/specs/spec_ph9_2_interface_purity.md) |
| **TD-259** | Government | **Refactor**: Orchestrator-Engine 분해 완료 | PH9.3 | [Insight](file:///c:/coding/economics/design/_archive/insights/TD-259_Government_Refactor.md) |
| **TD-261** | Bank / Judicial | **Purification**: Bank 비금융 로직 JudicialSystem 이관 | PH9.3 | [Insight](file:///c:/coding/economics/design/_archive/insights/TD-261_Judicial_Decoupling.md) |
| **TD-269** | Liquidation | **Protocol**: `ILiquidatable` 도입으로 `Firm` 결합 제거 | PH9.3 | [Insight](file:///c:/coding/economics/design/_archive/insights/TD-269_Liquidation_Refactor_Insight.md) |
| **TD-260** | Household Agent | **Decomposition**: Refactored God-Object into Orchestrator-Engine pattern. | PH10.2 | [Insight Report](../_archive/insights/2026-02-09_Household_Decomposition.md) |
