# Technical Debt Ledger

## 🔴 Active Technical Debt


### [Domain: Agents & Orchestration]

#### [TD-FIRM-GOD-OBJECT] [Open] The `Firm` class is a "God Object" with legacy proxy properties.
- **Description**: The `Firm` class combines multiple concerns (finance, production, etc.) and uses legacy patterns like the `finance` property returning `self` for backward compatibility. This creates fragile, non-obvious dependencies in orchestration code and increases the risk of state management errors.
- **Impact**: High. Obscures true component structure, complicates maintenance, and violates Separation of Concerns.
- **Source**: [Insight Report](../_archive/insights/2026-02-10_Tick_Level_State_Reset_Integrity.md)

---
### [Domain: Systems & Infrastructure]

---

### TD-274: Settlement System SSoT Violation (Inheritance Path)

- **Phenomenon**: `SettlementSystem.create_settlement()` was directly accessing `agent.assets` instead of using the `IFinancialAgent.get_balance()` protocol.
- **Risk**: Creates a bypass of the financial monitoring layers and potential for monetary leaks during agent removal (inheritance/liquidation).
- **Resolution**: Replaced direct attribute access with the formal `get_balance(DEFAULT_CURRENCY)` protocol method.
- **Reference**: `Interface Purity Compliance Report` (2026-02-09)

---


### TD-255: Cockpit's Direct State Injection

- **Phenomenon**: Control functions from `mission_active_cockpit` (`SET_BASE_RATE`, `SET_TAX_RATE`) directly modify the WorldState.
- **Risk**: Bypasses the event pipeline, potentially causing state inconsistencies as other agents or systems do not react to the change. Conflicts with automated logic (e.g., fiscal stabilizers) can occur.
- **Resolution**: Refactor commands into traceable "Manual Intervention" events processed through the standard Action Processor.
- **Related Mission**: `mission_active_cockpit`
- **Reference**: `2026-02-09_Cockpit_Direct_State_Intervention.md`

---

### [Pattern] DTO Contract Instability

- **Phenomenon**: A consumer system (`AnalyticsSystem`) crashed due to an `AttributeError` after a field was renamed in a DTO (`EconStateDTO`).
- **Cause**: The change in the DTO, which acts as a data contract, was not propagated to all its consumers.
- **Lesson**: DTOs are a critical API boundary. Any changes must be treated as a breaking change, requiring a full audit of all dependencies. Automated integration or smoke tests are essential for detecting such regressions early.
- **Reference**: `2026-02-09_DTO_Contract_Stability.md`

---

### TD-LIQ-INV: Protocol Purity Violation via `getattr`

- **Phenomenon**: A handler (`InventoryLiquidationHandler`) used `getattr` and `hasattr` to access internal agent attributes (`config`, `last_prices`), creating a tight coupling to a concrete class (`Firm`).
- **Risk**: Hinders extensibility and makes refactoring fragile. Violates architectural principles of depending on abstractions, not concretions.
- **Resolution**:
  1. Define a `LiquidationConfigDTO` for data transfer.
  2. Define an `IConfigurable` protocol with a `get_liquidation_config()` method.
  3. Implement the protocol on `Firm` to adapt its internal state into the DTO.
  4. The handler now checks for the protocol (`isinstance`) and operates on the DTO.
- **Lesson**:
  - **Protocols over Concretions**: Logic must depend on abstract protocols, not concrete classes.
  - **Test with `spec`**: `unittest.mock.MagicMock` must use the `spec` argument to enforce interface compliance in tests.
- **Reference**: `2026-02-09_Protocol_Purity_and_Mock_Specs.md`

---

### [Pattern] Legacy DTO Migration via Adapter

- **Phenomenon**: Multiple, incompatible versions of a DTO exist in the system (e.g., `StockOrder` vs `CanonicalOrderDTO`), causing type errors and increasing maintenance costs.
- **Cause**: Incomplete or phased refactoring leaves legacy DTOs in the codebase.
- **Solution**:
  1. Define a single, canonical DTO as the system standard.
  2. Implement an **Adapter function** to convert legacy DTOs or dictionaries into the canonical format. Use duck-typing sparingly to avoid circular imports if necessary.
  3. Enforce that core modules only accept the canonical DTO in their interfaces.
  4. Trace and refactor all legacy call sites to use the adapter.
- **Lesson**: The Adapter pattern is an effective, non-disruptive method for incrementally resolving technical debt. Logging within the adapter helps track legacy usage to plan for final removal.
- **Reference**: `2026-02-09_Adapter_Pattern_for_Legacy_DTOs.md`

---

### TD-272: Inconsistent Use of System Constants

- **Phenomenon**: The codebase, particularly the test suite, uses a mix of hardcoded literals (e.g., `'USD'`) and system-defined constants (e.g., `DEFAULT_CURRENCY`).
- **Risk**: Makes the system brittle. A future change to the default currency would require a manual, error-prone search-and-replace.
- **Resolution**: Mandate the use of system constants and add a linting rule to detect hardcoded literals where a constant is available.
- **Reference**: `../_archive/insights/2026-02-09_Review_Integrity_Shield_Fix.md`

---

### TD-273: Stringly-Typed Agent Identifiers

- **Phenomenon**: System processes (e.g., welfare transfers) use a mix of object instances, integer IDs, and special string literals (e.g., `"GOVERNMENT"`) to identify agents.
- **Risk**: Creates fragile logic that must explicitly check for and handle different identifier types, leading to potential errors if a type is missed.
- **Resolution**: Implement a unified Agent ID type or class that can encapsulate both regular and singleton agents.
- **Reference**: `../_archive/insights/2026-02-09_System_API_Contract_Preservation.md`

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
| **TD-274** | Financials | `SettlementSystem` SSoT 위반 (create_settlement) 해결 | PH9.2 | [Report](../../reports/temp/report_20260209_223920_Analyze_the_current.md) |
| **TD-264** | Financials | `SettlementSystem` 우회 코드 제거 및 `IFinancialAgent` 도입 | PH9.2 | [Insight](file:///c:/coding/economics/design/_archive/insights/PH9.2_TrackA.md) |
| **TD-265** | Sensory | `SensorySystem` 캡슐화 파괴 해결 및 DTO 전환 | PH9.2 | [Insight](file:///c:/coding/economics/design/_archive/insights/PH9.2_TrackB_SensoryPurity.md) |
| **TD-266** | Markets | `CanonicalOrderDTO` 도입 및 주문 파편화 해소 | PH9.2 | [Insight](file:///c:/coding/economics/design/_archive/insights/PH9.2_Market_DTO_Unification.md) |
| **TD-267** | Governance | `ARCH_AGENTS.md` 아키텍처 문서 동기화 | PH9.2 | [Spec](../3_work_artifacts/specs/spec_ph9_2_interface_purity.md) |
| **TD-259** | Government | **Refactor**: Orchestrator-Engine 분해 완료 | PH9.3 | [Insight](file:///c:/coding/economics/design/_archive/insights/TD-259_Government_Refactor.md) |
| **TD-261** | Bank / Judicial | **Purification**: Bank 비금융 로직 JudicialSystem 이관 | PH9.3 | [Insight](file:///c:/coding/economics/design/_archive/insights/TD-261_Judicial_Decoupling.md) |
| **TD-269** | Liquidation | **Protocol**: `ILiquidatable` 도입으로 `Firm` 결합 제거 | PH9.3 | [Insight](file:///c:/coding/economics/design/_archive/insights/TD-269_Liquidation_Refactor_Insight.md) |
| **TD-260** | Household Agent | **Decomposition**: Refactored God-Object into Orchestrator-Engine pattern. | PH10.2 | [Insight Report](../_archive/insights/2026-02-09_Household_Decomposition.md) |
| **TD-FIN-PURE** | Finance | **Stateless**: Refactored bailout request to Command pattern. | PH10.3 | [Insight](../_archive/insights/2026-02-09_PH10.3_Structural_Integrity.md) |
| **TD-JUD-ASSET** | Judicial | **Waterfall**: Implemented hierarchical asset seizure. | PH10.3 | [Insight](../_archive/insights/2026-02-09_PH10.3_Structural_Integrity.md) |
| **TD-LIQ-INV** | Liquidation | **Protocol**: `IConfigurable` replacement for `getattr` hacks. | PH10.4 | [Insight](../_archive/insights/2026-02-09_TD-LIQ-INV_Protocol_Purification.md) |
| **TD-255** | Housing | **Hardening**: Replaced `hasattr` with `IHousingTransactionParticipant`. | PH12 (Shield) | [Insight](../_archive/insights/2026-02-09_System_Protocol_Composition_Pattern.md) |
| **TD-270** | Financials | **Protocol**: Unified asset representation & added `total_wealth`. | PH10 | [Repo](../_archive/gemini_output/pr_review_market-decoupling-v2-11057596794459553753.md) |
| **TD-271** | Firms | **Utilization**: RealEstateUtilizationComponent for production bonus. | PH10 | [Repo](../_archive/gemini_output/pr_review_market-decoupling-v2-11057596794459553753.md) |
