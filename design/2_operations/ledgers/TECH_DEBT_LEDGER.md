# Technical Debt Ledger

## 🔴 Active Technical Debt

| ID | Domain | Description | Impact / Risk | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-INT-CONST** | System | Inconsistent use of System Constants (e.g., hardcoded 'USD'). | **Low**: Logic brittleness (TD-272). | Open |
| **WO-101** | Test | Core logic-protocol changes (e.g., wallet) break test mocks. | **High**: Logic brittleness/Drift. | Partially Mitigated |
| **TD-STR-GOD** | Architecture | God Classes: `Firm` (1164 LOC) and `Household` (1121 LOC) exceed maintainability thresholds. | **High**: High maintenance cost & circular dependencies. | Mitigating (Firm) |
| **TD-STR-LEAK** | Architecture | Abstraction Leaks: Raw agents passed to stateless engines (Production, HR, Gov, Policy). | **Medium**: Tight coupling, hard to test in isolation. | Mitigating (HR/Sales) |
| **TD-LEG-TRANS** | System | Legacy `TransactionManager` contains redundant/conflicting logic. | **Low**: Confusion & code bloat. | Pending Deletion |

## ✅ Resolved Technical Debt

| ID | Module / Component | Description | Resolution Session | Insight Report |
| :--- | :--- | :--- | :--- | :--- |
| **TD-DTO-STAB** | Data/DTO | **Standardization**: `CanonicalOrderDTO` enforced & `Transaction` typed. | Clean Room Era | [Insight](../../communications/insights/TD-DTO-STAB.md) |
| **TD-DTO-LEGACY** | Data/DTO | **Refactor**: `StockOrder` deprecated & `FirmStateDTO` uses `IFirmStateProvider`. | Clean Room Era | [Insight](../../communications/insights/TD-DTO-STAB.md) |
| **TD-LIQ-INV** | Liquidation | **Protocol**: Enforced `IConfigurable` & removed `getattr` hacks. | Clean Room Era | [Insight](../../communications/insights/TD-LIQ-INV.md) |
| **TD-FIRM-GOD-OBJECT** | Agents | **Refactor**: Decomposed Firm into Orchestrator-Engine pattern & removed legacy proxies. | Clean Room Era | [Insight](../_archive/insights/FIRM-RESET-FIX.md) |
| **TD-255-COCKPIT** | System | **Pipeline**: Replaced direct state injection with Async Event Pipeline. | Clean Room Era | [Spec](../../design/3_work_artifacts/specs/spec_cockpit_events.md) |
| **TD-273** | System | **Type Safety**: Unified Agent ID system (Object/Int/Str -> AgentID). | Clean Room Era | [Spec](../../design/3_work_artifacts/specs/audit_agent_ids.md) |
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
| **TD-HYGIENE** | Tests / Infrastructure | **Restoration**: Fixed 618+ test collection errors & 80+ unit/integration failures after major refactor. | PH10.5 | [Handover](../HANDOVER.md) |
| **TD-CM-001** | Common | **Fix**: Patched `yaml.safe_load` for ConfigManager unit tests. | Clean Room Era | [Insight](../../design/3_work_artifacts/reports/inbound/unit-tests-mocking-10138789661756819849_mission_unit_test_hardening.md) |
| **TD-TM-001** | Systems | **Fix**: Implemented `FakeNumpy` for TechnologyManager unit tests. | Clean Room Era | [Insight](../../design/3_work_artifacts/reports/inbound/unit-tests-mocking-10138789661756819849_mission_unit_test_hardening.md) |
| **TD-ECO-INH** | Simulation | **Fix**: Resolved inheritance leaks via fallback Escheatment & Final Sweep. | Clean Room Era | [Audit Report](../../design/3_work_artifacts/reports/inbound/economic-integrity-audit-fixes-124275369_AUDIT_ECONOMIC_INTEGRITY.md) |

## 📓 Implementation Lessons & Detailed Debt

---
### ID: TD-TEST-003
### Title: Brittle Global Mocks vs. Robust Local Fakes
- **Symptom**: Unit tests fail in lean environments (e.g., without `numpy`, `yaml`) because global mocks in `conftest.py` cannot adequately simulate complex library behaviors (e.g., matrix operations).
- **Root Cause**: Over-reliance on generic, globally-scoped mocks for dependencies that require nuanced behavior.
- **Solution**: For complex dependencies, create dedicated "Fake" or "Stub" objects (e.g., a `FakeNumpy` class) at the test-suite level. Use `unittest.mock.patch` to inject these fakes locally, ensuring tests are fully isolated and do not depend on the presence of heavy external libraries.
- **Lesson Learned**: Unit tests should verify logic flow and state changes. When a dependency's *behavior* is complex, it is better to create a simplified, predictable fake implementation for the unit test rather than fighting with complex `MagicMock` configurations. The verification of the *actual implementation* should be delegated to integration tests that run with the real dependencies.
- **Resolved in**: `fix-unit-tests-mocking-10138789661756819849`

---
### ID: TD-STR-GOD-FIRM
### Title: Firm God Class and Orchestration Bottleneck
- **현상**: `Firm` 클래스가 생산, 재무, HR, 영업 등 지나치게 많은 책임을 가지는 God Class가 되어 오케스트레이션의 병목 지점이 되고 있음.
- **원인**: 관련된 로직들이 각자의 엔진으로 분리되지 않고 `Firm` 클래스 내에 직접 구현되었었음.
- **해결/완화**: HR/Sales 엔진을 상태 비저장으로 분리하고 `Firm`을 오케스트레이터로 만드는 리팩토링을 통해 일부 책임이 분산됨. (Branch: `refactor-hr-sales-engines-stateless-10517561335784044124`)
- **교훈**: 복잡한 에이전트는 단일 책임 원칙에 따라 여러 개의 작은 오케스트레이터와 상태 비저장 엔진의 조합으로 분해되어야 테스트와 유지보수성이 향상됨. `FinanceEngine` 등 다른 영역에도 동일한 패턴 적용이 필요함.
---
