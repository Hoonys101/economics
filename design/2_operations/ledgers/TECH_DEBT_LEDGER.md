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
    *   **기술 부채 (Tech Debt)**: 은행 본연의 기능(예금/대출) 외의 책임이 섞여 있음.
    *   **해결 방안 (Resolution)**: 해당 로직을 `JudicialSystem` 등으로 이관.

*   **ID: TD-262 (Script & Regression Brittleness)**
    *   **현상 (Phenomenon)**: `/scripts` 내의 검증 스크립트들이 `BaseAgent` 제거 이후 취약해지거나 깨짐.
    *   **기술 부채 (Tech Debt)**: 회귀 테스트 자동화 능력 저하.
    *   **해결 방안 (Resolution)**: `TransactionProcessor` 흐름에 맞춰 스크립트 현대화.

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
