# Technical Debt History (TECH_DEBT_HISTORY.md)

This document archives resolved technical debt items to keep the primary ledger focused on active issues.

## ✅ Resolved Technical Debt

| ID | Module / Component | Description | Resolution Session | Insight Report |
| :--- | :--- | :--- | :--- | :--- |
| **WO-101** | Test | Core logic-protocol changes (e.g., wallet) break test mocks. | Clean Room Era | [Audit Guide](../../design/3_work_artifacts/reports/audit_test_migration_guide.md) |
| **TD-ARCH-LEAK-PROTI** | Architecture | Interface drift: `IFinancialEntity` defines deprecated APIs. | Clean Room Era | [Audit Guide](../../design/3_work_artifacts/reports/audit_test_migration_guide.md) |
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
| **TD-LIF-RESET** | Lifecycle | **Pulse**: Implemented `reset_tick_state` & `HouseholdFactory`. | PH15 | [Insight](../../communications/insights/implement-lifecycle-pulse) |
| **TD-INV-SLOT** | Inventory | **Protocol**: `InventorySlot` support & removed Registry duplication. | PH15 | [Insight](../../communications/insights/implement-inventory-slot) |
| **TD-FIN-FORT** | Finance | **SSoT**: `SettlementSystem` authority & removed parallel ledger. | PH15 | [Insight](../../communications/insights/implement_fortress_finance.md) |
| **TD-FIN-003** | Finance | **SSoT**: Removed Bank `_wallet` and synchronized with Finance ledger. | PH15 | [Insight](../../communications/insights/implement_fortress_finance.md) |
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
| **TD-270** | Financials | **Protocol**: Unified asset representation & added `total_wealth`. | PH10 | [Repo](../_archive/gemini_output/pr_review_market-decoupling-v2-11057596794459553753.md) |
| **TD-271** | Firms | **Utilization**: RealEstateUtilizationComponent for production bonus. | PH10 | [Repo](../_archive/gemini_output/pr_review_market-decoupling-v2-11057596794459553753.md) |
| **TD-HYGIENE** | Tests / Infrastructure | **Restoration**: Fixed 618+ test collection errors & 80+ unit/integration failures after major refactor. | PH10.5 | [Handover](../HANDOVER.md) |
| **TD-CM-001** | Common | **Fix**: Patched `yaml.safe_load` for ConfigManager unit tests. | Clean Room Era | [Insight](../../design/3_work_artifacts/reports/inbound/unit-tests-mocking-10138789661756819849_mission_unit_test_hardening.md) |
| **TD-TM-001** | Systems | **Fix**: Implemented `FakeNumpy` for TechnologyManager unit tests. | Clean Room Era | [Insight](../../design/3_work_artifacts/reports/inbound/unit-tests-mocking-10138789661756819849_mission_unit_test_hardening.md) |
| **TD-ECO-INH** | Simulation | **Fix**: Resolved inheritance leaks via fallback Escheatment & Final Sweep. | Clean Room Era | [Audit Report](../../design/3_work_artifacts/reports/inbound/economic-integrity-audit-fixes-124275369_AUDIT_ECONOMIC_INTEGRITY.md) |
| **TD-STR-GOD** | Architecture | **Refactor**: Decomposed `Firm` and `Household` into Orchestrator-Engine pattern. | Refactoring Era | [Firm Insight](./firm_decomposition.md), [HH Insight](./HH_Engine_Refactor_Insights.md) |
| **TD-STR-LEAK** | Architecture | **Purification**: Removed raw agent handles from engines (Finance, HH, Firm). | Refactoring Era | [Audit Report](../../communications/insights/REFACTORING_COMPLIANCE_AUDIT.md) |
| **TD-FIN-ZERO** | Finance | **Fix**: Double-entry integrity in stateless finance engines (Retained Earnings). | Refactoring Era | [Finance Insight](../../communications/insights/TECH_DEBT_LEDGER.md) |
| **TD-AGENT-STATE-INVFIRM** | Data/DTO | **Serialization Gap**: `AgentStateDTO` multi-slot inventory support. | PH15-FIX | [Insight](../../communications/insights/FIX-FINAL-TESTS.md) |
| **TD-QE-MISSING** | Financials | **Logic Gap**: QE Bond Issuance logic restoration. | PH15.2 | [Insight](../../communications/insights/MS-Finance-Purity-QE.md) |
| **TD-FIN-001** | Finance | **Purity**: Refactored `DebtServicing` & `LoanBooking` to functional pattern. | PH15.2 | [Insight](../../communications/insights/MS-Finance-Purity-QE.md) |
| **TD-PH15-SEO** | Architecture | **Hardening**: Eliminated direct Agent handle leaks in core engines (Tax/Solvency). | PH15.2 | [Insight](../../communications/insights/MS-0128-Tax-Engine-Refactor.md) |
| **TD-INT-STRESS-SCALE** | System | **O(N) Stress Scan**: Bank -> Depositor reverse index implemented. | 2026-02-14 | [Insight](../../design/_archive/insights/2026-02-14_Settlement_Stress_Scale_Optimization.md) |
| **TD-INT-WS-SYNC** | System | **WS Polling**: Event-driven broadcast via TelemetryExchange implemented. | 2026-02-14 | [Insight](../../design/_archive/insights/2026-02-14_WebSocket_Event_Driven_Optimization.md) |
| **TD-ARCH-PROTO-LOCATION** | System | **Bleeding Protocols**: Refactored to `modules/api/protocols.py`. | 2026-02-14 | [Insight](../../design/_archive/insights/2026-02-14_Post_Merge_Stabilization.md) |

## 📓 Implementation Lessons (Resolved Path)

---
### ID: TD-TEST-003
### Title: Brittle Global Mocks vs. Robust Local Fakes
- **Symptom**: Unit tests fail in lean environments (e.g., without `numpy`, `yaml`) because global mocks in `conftest.py` cannot adequately simulate complex library behaviors (e.g., matrix operations).
- **Resolution**: Created dedicated "Fake" or "Stub" objects (e.g., a `FakeNumpy` class) patch locally.
- **Lesson Learned**: Unit tests should verify logic flow and state changes. Use predictably simplified fakes for complex dependencies.
- **Resolved in**: `fix-unit-tests-mocking-10138789661756819849`

---
### ID: TD-STR-GOD-FIRM
### Title: Firm God Class and Orchestration Bottleneck
- **현상**: `Firm` 클래스가 지나치게 많은 책임을 가지는 God Class가 됨.
- **해결/완화**: HR/Sales 엔진을 상태 비저장으로 분리하고 `Firm`을 오케스트레이터로 리팩토링.
- **교훈**: 복잡한 에이전트는 단일 책임 원칙에 따라 분해되어야 함.

---
### ID: TD-FIN-FORT
### Title: Financial Fortress Protocol Violation (Direct Wallet Mutation)
- **Symptom**: Direct mutation of `_wallet` bypassing `SettlementSystem`.
- **Solution**: Removed direct mutation APIs. Forced all transfers through `SettlementOrder`.
- **Lesson Learned**: SSoT must be absolute. Dual-writes always drift.
- **Resolved in**: `refactor/financial-fortress-ssot`

---
### ID: TD-INV-SLOT
### Title: Inventory Slot Protocol Violation (input_inventory)
- **Symptom**: `input_inventory` mutated directly using raw dict access.
- **Solution**: Extended `IInventoryHandler` with `InventorySlot` support and refactored call sites.
- **Reported**: `audit_inventory_purity_20260211.md`

---
### ID: TD-LIF-RESET
### Title: Missing Tick-Level State Reset (Household Agent)
- **Symptom**: `Household` agents lack a `reset()` method.
- **Solution**: Implemented `Household.reset_tick_state()` and orchestrated via `AgentLifecycleManager`.
- **Reported**: `audit_lifecycle_hygiene_20260211.md`
