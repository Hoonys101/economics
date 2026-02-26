# Technical Debt History (TECH_DEBT_HISTORY.md)

This document archives resolved technical debt items to keep the primary ledger focused on active issues.

## ✅ Resolved Technical Debt

| ID | Module / Component | Description | Resolution Session | Insight Report |
| :--- | :--- | :--- | :--- | :--- |
| **TD-STR-GOD-DECOMP** | Architecture | **Refactor**: CES Lite Agent Shells. | Phase 18 | [Spec](../../3_work_artifacts/specs/MISSION_agent-decomposition_SPEC.md) |
| **TD-TEST-MOCK-DRIFT-GEN** | Testing | **Protocol**: StrictMockFactory enforced. | Phase 18 | [Spec](../../3_work_artifacts/specs/MISSION_mock-automation_SPEC.md) |
| **TD-TEST-UNIT-SCALE** | Testing | **Standard**: Penny Standard Migration. | Phase 18 | [Spec](../../3_work_artifacts/specs/MISSION_test-unit-scale_SPEC.md) |
| **TD-DTO-FLOAT-LEAK** | Config | **Integers**: Config DTOs migrated to Pennies. | Phase 18 | [Review](../../_archive/gemini_output/pr_review_dto-api-repair-int-migration-1186540435321916919.md) |
| **TD-DTO-PROBE-BYPASS** | Architecture | **Protocol**: IFirmStateProvider via DTO Repair. | Phase 18 | [Review](../../_archive/gemini_output/pr_review_dto-api-repair-int-migration-1186540435321916919.md) |
| **WO-101** | Test | Core logic-protocol changes (e.g., wallet) break test mocks. | Clean Room Era | [Audit Guide](../../3_work_artifacts/reports/audit_test_migration_guide.md) |
| **TD-ARCH-LEAK-PROTI** | Architecture | Interface drift: `IFinancialEntity` defines deprecated APIs. | Clean Room Era | [Audit Guide](../../3_work_artifacts/reports/audit_test_migration_guide.md) |
| **TD-DTO-STAB** | Data/DTO | **Standardization**: `CanonicalOrderDTO` enforced & `Transaction` typed. | Clean Room Era | [Insight](../../../communications/insights/TD-DTO-STAB.md) |
| **TD-DTO-LEGACY** | Data/DTO | **Refactor**: `StockOrder` deprecated & `FirmStateDTO` uses `IFirmStateProvider`. | Clean Room Era | [Insight](../../../communications/insights/TD-DTO-STAB.md) |
| **TD-LIQ-INV** | Liquidation | **Protocol**: Enforced `IConfigurable` & removed `getattr` hacks. | Clean Room Era | [Insight](../../../communications/insights/TD-LIQ-INV.md) |
| **TD-FIRM-GOD-OBJECT** | Agents | **Refactor**: Decomposed Firm into Orchestrator-Engine pattern & removed legacy proxies. | Clean Room Era | [Insight](../../_archive/insights/FIRM-RESET-FIX.md) |
| **TD-255-COCKPIT** | System | **Pipeline**: Replaced direct state injection with Async Event Pipeline. | Clean Room Era | [Spec](../../3_work_artifacts/specs/spec_cockpit_events.md) |
| **TD-273** | System | **Type Safety**: Unified Agent ID system (Object/Int/Str -> AgentID). | Clean Room Era | [Spec](../../3_work_artifacts/specs/audit_agent_ids.md) |
| **TD-255** | Tests / Simulation | Mock Fragility - Internal patching 제거 | PH10.1 | [Insight](../../../communications/insights/TD-255_TD-256_TD-257_Stabilization.md) |
| **TD-256** | Lifecycle Manager | `FinanceState` 내 dynamic hasattr 체크 제거 | PH10.1 | [Insight](../../../communications/insights/TD-255_TD-256_TD-257_Stabilization.md) |
| **TD-257** | Finance Engine | 하드코딩된 unit cost(5.0) 설정값으로 이관 | PH10.1 | [Insight](../../../communications/insights/TD-255_TD-256_TD-257_Stabilization.md) |
| **TD-258** | Command Bus | Orchestrator-Engine 시그니처 정규화 | PH10.1 | [Insight](../../../communications/insights/TD-255_TD-256_TD-257_Stabilization.md) |
| **TD-LIF-RESET** | Lifecycle | **Pulse**: Implemented `reset_tick_state` & `HouseholdFactory`. | PH15 | [Insight](../../../communications/insights/implement-lifecycle-pulse) |
| **TD-INV-SLOT** | Inventory | **Protocol**: `InventorySlot` support & removed Registry duplication. | PH15 | [Insight](../../../communications/insights/implement-inventory-slot) |
| **TD-FIN-FORT** | Finance | **SSoT**: `SettlementSystem` authority & removed parallel ledger. | PH15 | [Insight](../../../communications/insights/implement_fortress_finance.md) |
| **TD-FIN-003** | Finance | **SSoT**: Removed Bank `_wallet` and synchronized with Finance ledger. | PH15 | [Insight](../../../communications/insights/implement_fortress_finance.md) |
| **TD-PH10** | Core Agents | `BaseAgent.py` 완전 퇴역 및 삭제 | PH10 | [Insight](../../../communications/insights/PH9.3-STRUCTURAL-PURITY.md) |
| **TD-PROX** | Firms | `HRProxy`, `FinanceProxy` 삭제 | PH10 | [Insight](../../../communications/insights/PH9.2_Firm_Core_Protocol_Enforcement.md) |
| **TD-DTO** | Orders | `OrderDTO` 인터페이스 표준화 | PH9.3 | [Insight](../../../communications/insights/hr_finance_decouple_insight.md) |
| **TD-268** | Core Agents | `BaseAgent` 상속 구조 제거 시작 | PH9.3 | [Insight](../../../communications/insights/TD-268_BaseAgent_Refactor.md) |
| **TD-ANL** | Analytics | 에이전트 내부 접근 대신 DTO Snapshot 사용 | PH10 | [Insight](../../../communications/insights/PH9.2_Firm_Core_Protocol_Enforcement.md) |
| **TD-262** | Scripts | BaseAgent 제거 이후 깨진 검증 스크립트 복구 | PH10 | [Insight](../../_archive/gemini_output/pr_review_bundle-purity-regression-1978915247438186068.md) |
| **TD-DTO-CONTRACT** | Simulation | DTO 필드명 변경 시 발생한 contract 불일치 해결 | PH10 | [Insight](../../_archive/gemini_output/pr_review_bundle-purity-regression-1978915247438186068.md) |
| **TD-263** | Scripts / Maintenance | Report Harvester 누락 경로 반영 및 원격 브랜치 청소 로직 최적화 | PH10.1 | [Log](./design/2_operations/ledgers/INBOUND_REPORTS.md) |
| **TD-274** | Financials | `SettlementSystem` SSoT 위반 (create_settlement) 해결 | PH9.2 | [Report](../../reports/temp/report_20260209_223920_Analyze_the_current.md) |
| **TD-264** | Financials | `SettlementSystem` 우회 코드 제거 및 `IFinancialAgent` 도입 | PH9.2 | [Insight](../../_archive/insights/PH9.2_TrackA.md) |
| **TD-265** | Sensory | `SensorySystem` 캡슐화 파괴 해결 및 DTO 전환 | PH9.2 | [Insight](../../_archive/insights/PH9.2_TrackB_SensoryPurity.md) |
| **TD-266** | Markets | `CanonicalOrderDTO` 도입 및 주문 파편화 해소 | PH9.2 | [Insight](../../_archive/insights/PH9.2_Market_DTO_Unification.md) |
| **TD-267** | Governance | `ARCH_AGENTS.md` 아키텍처 문서 동기화 | PH9.2 | [Spec](../3_work_artifacts/specs/spec_ph9_2_interface_purity.md) |
| **TD-259** | Government | **Refactor**: Orchestrator-Engine 분해 완료 | PH9.3 | [Insight](../../_archive/insights/TD-259_Government_Refactor.md) |
| **TD-261** | Bank / Judicial | **Purification**: Bank 비금융 로직 JudicialSystem 이관 | PH9.3 | [Insight](../../_archive/insights/TD-261_Judicial_Decoupling.md) |
| **TD-269** | Liquidation | **Protocol**: `ILiquidatable` 도입으로 `Firm` 결합 제거 | PH9.3 | [Insight](../../_archive/insights/TD-269_Liquidation_Refactor_Insight.md) |
| **TD-260** | Household Agent | **Decomposition**: Refactored God-Object into Orchestrator-Engine pattern. | PH10.2 | [Insight Report](../../_archive/insights/2026-02-09_Household_Decomposition.md) |
| **TD-FIN-PURE** | Finance | **Stateless**: Refactored bailout request to Command pattern. | PH10.3 | [Insight](../../_archive/insights/2026-02-09_PH10.3_Structural_Integrity.md) |
| **TD-JUD-ASSET** | Judicial | **Waterfall**: Implemented hierarchical asset seizure. | PH10.3 | [Insight](../../_archive/insights/2026-02-09_PH10.3_Structural_Integrity.md) |
| **TD-LIQ-INV** | Liquidation | **Protocol**: `IConfigurable` replacement for `getattr` hacks. | PH10.4 | [Insight](../../_archive/insights/2026-02-09_TD-LIQ-INV_Protocol_Purification.md) |
| **TD-270** | Financials | **Protocol**: Unified asset representation & added `total_wealth`. | PH10 | [Repo](../../_archive/gemini_output/pr_review_market-decoupling-v2-11057596794459553753.md) |
| **TD-271** | Firms | **Utilization**: RealEstateUtilizationComponent for production bonus. | PH10 | [Repo](../../_archive/gemini_output/pr_review_market-decoupling-v2-11057596794459553753.md) |
| **TD-HYGIENE** | Tests / Infrastructure | **Restoration**: Fixed 618+ test collection errors & 80+ unit/integration failures after major refactor. | PH10.5 | [Handover](../HANDOVER.md) |
| **TD-CM-001** | Common | **Fix**: Patched `yaml.safe_load` for ConfigManager unit tests. | Clean Room Era | [Insight](../../3_work_artifacts/reports/inbound/unit-tests-mocking-10138789661756819849_mission_unit_test_hardening.md) |
| **TD-TM-001** | Systems | **Fix**: Implemented `FakeNumpy` for TechnologyManager unit tests. | Clean Room Era | [Insight](../../3_work_artifacts/reports/inbound/unit-tests-mocking-10138789661756819849_mission_unit_test_hardening.md) |
| **TD-ECO-INH** | Simulation | **Fix**: Resolved inheritance leaks via fallback Escheatment & Final Sweep. | Clean Room Era | [Audit Report](../../3_work_artifacts/reports/inbound/economic-integrity-audit-fixes-124275369_AUDIT_ECONOMIC_INTEGRITY.md) |
| **TD-STR-GOD** | Architecture | **Refactor**: Decomposed `Firm` and `Household` into Orchestrator-Engine pattern. | Refactoring Era | [Firm Insight](./firm_decomposition.md), [HH Insight](./HH_Engine_Refactor_Insights.md) |
| **TD-STR-LEAK** | Architecture | **Purification**: Removed raw agent handles from engines (Finance, HH, Firm). | Refactoring Era | [Audit Report](../../../communications/insights/REFACTORING_COMPLIANCE_AUDIT.md) |
| **TD-FIN-ZERO** | Finance | **Fix**: Double-entry integrity in stateless finance engines (Retained Earnings). | Refactoring Era | [Finance Insight](../../../communications/insights/TECH_DEBT_LEDGER.md) |
| **TD-AGENT-STATE-INVFIRM** | Data/DTO | **Serialization Gap**: `AgentStateDTO` multi-slot inventory support. | PH15-FIX | [Insight](../../../communications/insights/FIX-FINAL-TESTS.md) |
| **TD-QE-MISSING** | Financials | **Logic Gap**: QE Bond Issuance logic restoration. | PH15.2 | [Insight](../../../communications/insights/MS-Finance-Purity-QE.md) |
| **TD-FIN-001** | Finance | **Purity**: Refactored `DebtServicing` & `LoanBooking` to functional pattern. | PH15.2 | [Insight](../../../communications/insights/MS-Finance-Purity-QE.md) |
| **TD-PH15-SEO** | Architecture | **Hardening**: Eliminated direct Agent handle leaks in core engines (Tax/Solvency). | PH15.2 | [Insight](../../../communications/insights/MS-0128-Tax-Engine-Refactor.md) |
| **TD-INT-STRESS-SCALE** | System | **O(N) Stress Scan**: Bank -> Depositor reverse index implemented. | 2026-02-14 | [Insight](../../design/_archive/insights/2026-02-14_Settlement_Stress_Scale_Optimization.md) |
| **TD-INT-WS-SYNC** | System | **WS Polling**: Event-driven broadcast via TelemetryExchange implemented. | 2026-02-14 | [Insight](../../design/_archive/insights/2026-02-14_WebSocket_Event_Driven_Optimization.md) |
| **TD-ARCH-PROTO-LOCATION** | System | **Bleeding Protocols**: Refactored to `modules/api/protocols.py`. | 2026-02-14 | [Insight](../../design/_archive/insights/2026-02-14_Post_Merge_Stabilization.md) |
| **TD-SYS-BATCH-FRAGILITY** | System | **Manifest Persistence**: Replaced `command_manifest.py` with `MissionRegistryService`. | 2026-02-15 | [Mission Review](./pr_review_jules-17-1-manifest-service-15689901827980789950.md) |
| **TD-DATA-03-PERF** | Performance | **Demographics O(1)**: Event-driven stats for birth/death. | 2026-02-15 | [Mission Review](./pr_review_jules-17-2-event-demographics-18407633892604030203.md) |
| **TD-SYS-GHOST-CONSTANTS** | Architecture | **Config Proxy**: Solved import-time binding (Ghost Constants). | 2026-02-15 | [Mission Review](./pr_review_jules-17-3-config-proxy-purity-7306288639511283426.md) |
| **TD-MON-SETTLEMENT-DRIFT** | Protocol | **Interface Segregation**: Split `ISettlementSystem` and `IMonetaryAuthority`. | 2026-02-15 | [Mission Review](./pr_review_jules-17-3-config-proxy-purity-7306288639511283426.md) |
| **TD-DATA-01-MOCK** | Finance | **Strict Mocking**: Added `assert_implements_protocol` and segregrated interfaces. | 2026-02-15 | [Mission Review](./pr_review_jules-17-3-config-proxy-purity-7306288639511283426.md) |
| **TD-CRIT-FLOAT-SETTLE** | Settlement | **Protocol Purity**: Enforced strict typing for Settlement System interactions. | 2026-02-15 | [Mission Review](./pr_review_jules-track-a-settlement-12072150354750025434.md) |
| **TD-ARCH-SEC-GOD** | Security | **Hardening**: Enforced Localhost binding and Config DTOs for SimulationServer. | 2026-02-15 | [Mission Review](./pr_review_jules-track-b-security-11612781887738691353.md) |
| **TD-MOCK-BANK-DRIFT** | Finance | **Protocol Alignment**: Fixed `MockBank` to implement `get_total_deposits`. | 2026-02-16 | [PR Review](../../_archive/gemini_output/pr_review_fix-tests-and-protocols-956842252339614960.md) |
| **TD-ASSET-PRECISION** | Engines | **Unit Standardization**: Fixed `AssetManagementEngine` tests using Pennies (int). | 2026-02-16 | [PR Review](../../_archive/gemini_output/pr_review_fix-tests-and-protocols-956842252339614960.md) |
| **TD-PROC-ENGINE-BUG** | Simulation | **Bug Fix**: Resolved `NameError` in `ProductionEngine` and added `AgentID` to Mock Firm. | 2026-02-16 | [PR Review](../../_archive/gemini_output/pr_review_fix-tests-and-protocols-956842252339614960.md) |
| **TD-CMD-ROLLBACK** | System | **Hardening**: Fixed `CommandService` rollback assertions for `IRestorableRegistry`. | 2026-02-16 | [PR Review](../../_archive/gemini_output/pr_review_fix-tests-and-protocols-956842252339614960.md) |
| **TD-MKT-FLOAT-MATCH** | Markets | **Refactor**: MatchingEngine Integer Hardening | Phase 19 | [Review](../../_archive/gemini_output/pr_review_exec-match-engine-int-math-17795771630785453590.md) |
| **TD-ARCH-LIFE-GOD** | Systems | **Refactor**: LifecycleManager Decomposition | Phase 19 | [Review](../../_archive/gemini_output/pr_review_lifecycle-decomposition-15351638010886493967.md) |
| **TD-INT-PENNIES-FRAGILITY** | System | **Protocol**: Integer Pennies Compatibility | Phase 19 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-CRIT-FLOAT-SETTLE** | Finance | **Fix**: Float-to-Int Migration Bridge | Phase 19 | [Review](../../_archive/gemini_output/pr_review_exec-match-engine-int-math-17795771630785453590.md) |
| **TD-DTO-DESYNC-2026** | DTO/API | **Fix**: Cross-Module Contract Fracture | Phase 19 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-TEST-SSOT-SYNC** | Testing | **SSoT**: Balance Mismatch Test Sync | Phase 19 | [Review](../../_archive/gemini_output/pr_review_mission-test-modernization-ssot-557820577312838977.md) |
| **TD-TRANS-LEGACY-PRICING** | Transaction | **Fix**: Float Cast Bridge Elimination | Phase 19 | [Review](../../_archive/gemini_output/pr_review_exec-match-engine-int-math-17795771630785453590.md) |
| **TD-DTO-RED-ZONE** | DTO/API | **Fix**: Reporting Leakage Hardening | Phase 19 | [Review](../../_archive/gemini_output/pr_review_penny-hardening-reporting-dtos-744587785833593148.md) |
| **TD-PROC-TRANS-DUP** | Logic | **Handler Redundancy**: Logic overlap between legacy `TransactionManager` and new `TransactionProcessor`. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-TRANS-INT-SCHEMA** | Transaction | **Schema Lag**: `Transaction` model (simulation/models.py) still uses `float` price. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-DEPR-GOV-TAX** | Government | **Legacy API**: `Government.collect_tax` is deprecated. Use `settle_atomic`. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-DEPR-FACTORY** | Factory | **Stale Path**: `agent_factory.HouseholdFactory` is stale. Use `household_factory`. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-RUNTIME-DEST-MISS** | Lifecycle | **Ghost Destination**: Transactions failing for non-existent agents (Sequence error in `spawn_firm`). | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-TEST-MOCK-STALE** | Testing | **Stale Mocks**: `WorldState` mocks used deprecated `system_command_queue`. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-GOV-SOLVENCY** | Government | **Binary Gates**: Spending modules use all-or-nothing logic; lack partial execution/solvency pre-checks. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-CRIT-SYS0-MISSING** | Systems | **Fix**: Registered `sim.central_bank` in `SimulationInitializer`. | Phase 24 | [Review](../../_archive/gemini_output/pr_review_fix-sys-registry-13312846699871297983.md) |
| **TD-CRIT-PM-MISSING** | Systems | **Fix**: Registered Public Manager and funded with PM overdraft. | Phase 24 | [Review](../../_archive/gemini_output/pr_review_fix-pm-funding-15893498075582379062.md) |
| **TD-DB-SCHEMA-DRIFT** | Systems | **Fix**: Implemented runtime migration for `total_pennies` column in DB. | Phase 24 | [Review](../../_archive/gemini_output/pr_review_fix-db-migration-12248755876135984758.md) |
| **TD-ECON-M2-INV-BUG** | Economic | **M2 Audit Logic**: `audit_total_m2` naively sums negative balances. | Phase 23 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-SYS-BATCH-RACE** | Finance | **Atomic Batch Race**: Multiple withdrawals in a batch bypass balance checks. | Phase 23 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-ARCH-SETTLEMENT-BLOAT** | Architecture | **Settlement Overload**: `SettlementSystem` handles orchestration, ledgers, metrics, and indices. | Phase 4.1 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-CONFIG-HARDCODED-MAJORS** | Configuration | **Hardcoded Majors**: `MAJORS` list hardcoded in `labor/constants.py` instead of yaml. | Phase 4.1 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-ECON-M2-REGRESSION** | Economic | **M2 Negative Inversion**: `calculate_total_money()` sums negative balances. | Phase 23 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-FIN-SAGA-REGRESSION** | Finance | **Saga Drift**: Sagas skipped due to missing/dead participant IDs. | Phase 23 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-LIFECYCLE-GHOST-FIRM** | Lifecycle | **Ghost Firm Bug**: Transactions precede registration during startup. | Phase 23 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-TEST-DTO-MOCK** | Testing | **DTO Hygiene**: `tests/test_firm_brain_scan.py` uses permissive `MagicMock` for DTOs. | Phase 4.1 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-FIN-INVISIBLE-HAND** | Finance | **Initialization Order**: CB/PublicManager registered after AgentRegistry snapshot. | Phase 23 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-MARKET-FLOAT-TRUNC** | Market | **Wealth Destruction**: `MatchingEngine` truncates fractional pennies via `int()`. | Phase 23 | [Insight](../../_archive/insights/TECH_DEBT_LEDGER.md) |
| **TD-SYS-TRANSFER-HANDLER-GAP** | systems | **Generic Transfer Handler Omission** | Wave 6 | [Walkthrough](../../../../../C:/Users/Gram%20Pro/.gemini/antigravity/brain/9e84c9d1-4eb2-468e-b0c9-f9b8fd691c1c/walkthrough.md) |
| **TD-MARKET-CONFIG-PURITY** | Market | **Config Purity**: OrderBookMarket takes DTO instead of raw config. | Phase 34 | [Walkthrough](../../../../../C:/Users/Gram%20Pro/.gemini/antigravity/brain/9e84c9d1-4eb2-468e-b0c9-f9b8fd691c1c/walkthrough.md) |

| **TD-CRIT-LIFECYCLE-ATOM** | Lifecycle | **Agent Startup Atomicity**: Firm registration (Registry) must occur *before* financial initialization (Transfer). | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-SYS-QUEUE-SCRUB** | Lifecycle | **Lifecycle Queue Scrubbing**: AgentLifecycleManager fails to remove stale IDs from queues. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-GOV-SPEND-GATE** | Government | **Binary Spending Gates**: Infrastructure/Welfare modules need "Partial Execution" support. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-CRIT-FLOAT-MA** | Finance | **M&A Float Violation**: `MAManager` and `StockMarket` calculate and transfer `float` values. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-RUNTIME-TX-HANDLER** | Transaction | **Missing Fiscal Handlers**: `bailout`, `bond_issuance` types not registered in `TransactionProcessor`. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-ARCH-FIRM-COUP** | Architecture | **Fix**: `Firm` departments parent pointer pollution. | Phase 24 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-CRIT-FLOAT-CORE** | Finance | **Fix**: `SettlementSystem` float core usage. | Phase 24 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-TEST-COCKPIT-MOCK** | Testing | **Fix**: Cockpit 2.0 Mock Regressions. | Phase 24 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-TEST-LIFE-STALE** | Testing | **Fix**: Stale Lifecycle Logic in tests. | Phase 24 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-ECON-M2-INV** | Economic | **Fix**: M2 Negative Inversion due to overdrafts. | Phase 24 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-ARCH-STARTUP-RACE** | Architecture | **Fix**: Ghost Firm Registry race condition. | Phase 23 | [Insight](./TECH_DEBT_LEDGER.md) |
| **TD-FIN-SAGA-ORPHAN** | Finance | **Fix**: Saga Participant Drift causing `SAGA_SKIP`. | Phase 24 | [Insight](./TECH_DEBT_LEDGER.md) |

## 📓 Implementation Lessons (Resolved Path)

---

### ID: TD-STR-GOD-DECOMP
- **Title**: God Class Decomposition (Firm & Household)
- **Status**: **Resolved** (Phase 18)
- **Solution**: Implemented **CES Lite (Agent Shell)** pattern. `Firm` and `Household` were decomposed into `InventoryComponent`, `FinancialComponent`, and stateless `Orchestrators`.
- **Lesson**: Composition prefers specific typed Components over massive Inheritance hierarchies.

---

### ID: TD-TEST-MOCK-DRIFT-GEN
- **Title**: Recursive Protocol Drift in Mocks
- **Status**: **Resolved** (Phase 18)
- **Solution**: Implemented `StrictMockFactory` and `ProtocolInspector` to enforce `spec_set` compliance on all Mocks.
- **Lesson**: Never use `MagicMock` without a spec. Automated enforcement prevents "Zombie Tests".

---

### ID: TD-TEST-UNIT-SCALE
- **Title**: Dollar-Penny Unit Confusion in Tests
- **Status**: **Resolved** (Phase 18)
- **Solution**: Migrated test suite to **Penny Standard** (`int`). Introduced `P()` helper.
- **Lesson**: Test data must match the physical storage unit (Integer Pennies) of the engine.

---

### ID: TD-DTO-FLOAT-LEAK
- **Title**: Floating-Point Leakage in DTO Boundaries
- **Status**: **Resolved** (Phase 18)
- **Solution**: Converted all monetary configuration constants (`defaults.py`) and Telemetry DTOs to `int` pennies.
- **Lesson**: Precision leakage starts at the injection point. Configuration MUST be strictly typed.


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

---

### ID: TD-SYS-BATCH-FRAGILITY
### Title: Brittle Manifest Persistence (command_manifest.py)
- **Symptom**: `command_manifest.py` was being edited via Regex pattern matching, which was prone to corruption.
- **Resolution**: Migrated to `MissionRegistryService` using a structured JSON backend (`command_registry.json`) and AST-based migration logic.
- **Resolved in**: `jules-17-1-manifest-service`

---

### ID: TD-DATA-03-PERF
### Title: Demographic Statistics Performance (O(N) to O(1))
- **Symptom**: `DemographicManager` iterated thousands of agents every tick to find gender/age/labor totals.
- **Resolution**: Implemented a "Push" model where agents notify the manager on birth/death events, maintaining cached counters.
- **Resolved in**: `jules-17-2-event-demographics`

---

### ID: TD-SYS-GHOST-CONSTANTS
### Title: Ghost Constants & Import-Time Binding
- **Symptom**: `from config import X` bound values at import time, ignoring runtime registry updates (e.g., God Mode tweaks).
- **Resolution**: Refactored `config` to a `sys.modules` Proxy pattern that routes all access to a layered `GlobalRegistry`.
- **Resolved in**: `jules-17-3-config-proxy-purity`
---

### ID: TD-MOCK-BANK-DRIFT
### Title: Protocol-Mock Drift Clearance
- **Symptom**: Abstract class instantiation errors in CI.
- **Resolution**: Implemented missing interface methods across all test files and modernized `test_circular_imports_fix.py`.
- **Lesson**: Interface changes require a global search for mock implementations.

---
### ID: TD-ASSET-PRECISION
### Title: Penny Accounting Enforcement (Tests)
- **Symptom**: Magnitude errors in production/investment results.
- **Resolution**: Refactored `AssetManagementInputDTO` fixtures to use absolute penny values (`int`).
- **Lesson**: Decouple "Display Dollars" from "Simulation Pennies" at the test boundary.

---

### ID: TD-MKT-FLOAT-MATCH
- **Title**: MatchingEngine Integer Hardening
- **Status**: **Resolved** (Phase 19)
- **Solution**: Implemented Dual-Precision model with `total_pennies` as SSoT for matching logic.
- **Lesson**: Mid-price calculation MUST use Round-Down logic to prevent float artifacts.

---

### ID: TD-ARCH-LIFE-GOD
- **Title**: Lifecycle Manager Monolith
- **Status**: **Resolved** (Phase 19)
- **Solution**: Decomposed into `BirthSystem`, `DeathSystem`, and `AgingSystem`.
- **Lesson**: Lifecycle events should be handled by independent systems listening to clock pulses.

---

### ID: TD-INT-PENNIES-FRAGILITY
- **Title**: Integer Pennies Compatibility Debt
- **Status**: **Resolved** (Phase 19)
- **Solution**: Removed `hasattr` wrappers in favor of strict `int` pennies across core DTOs.

---

### ID: TD-TEST-SSOT-SYNC
- **Title**: SSoT Balance Mismatch in Test Suite
- **Status**: **Resolved** (Phase 19)
- **Solution**: Refactored entire test suite to assert against `SettlementSystem` instead of agent attributes.
- **Lesson**: Tests must verify the *authority's* ledger, not the agent's perceived state.

---

- **Solution**: Refactored `MarketReportDTO` and `AgentStateDTO` to use integer pennies.

---

### ID: TD-PROC-TRANS-DUP
- **Title**: Transaction Logic Duplication
- **Status**: **Resolved** (Phase 23)
- **Solution**: Deprecate `TransactionManager` and route all traffic through `TransactionProcessor`.

---

### ID: TD-GOV-SOLVENCY
- **Title**: Government Budget Guardrails (Binary Gates)
- **Status**: **Resolved** (Phase 23)
- **Solution**: Implement `PartialExecutionResultDTO` and `SolvencyException` with proactive balance checks via `SettlementSystem`.

---

### ID: TD-ARCH-GOV-MISMATCH / TD-ARCH-GOV-DYNAMIC
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Synchronized `WorldState` to support `_governments` list and implemented a `@property government` facade for singleton access. Eliminated fragile dynamic injection.

### ID: TD-INT-BANK-ROLLBACK
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Decoupled rollback logic from the `Bank` domain model. Moved to `TransactionProcessor` utilizing strict `ITransactionHandler.rollback` protocols.

### ID: TD-SYS-ACCOUNTING-GAP
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Updated `CommerceSystem` and `AccountingSystem` to ensure reciprocal expense logging for B2B transactions, achieving double-entry alignment.

### ID: TD-LABOR-METADATA
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Refactored `LaborMarket` and `CanonicalOrderDTO` to pass `major` as a first-class `IndustryDomain` enum rather than loose metadata dictionary entries.

### ID: TD-SYS-ANALYTICS-DIRECT
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Enforcement of statelessness in `AnalyticsSystem`. All analytics pipelines now ingest `HouseholdSnapshotDTO` or `AgentStateDTO` instead of direct model access.

### ID: TD-ARCH-ESTATE-REGISTRY
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Formalized `EstateRegistry` for post-mortem financial finalization. Removed "Resurrection Hack" from `SettlementSystem` in favor of claim interception.

### ID: TD-SPEC-DTO-INT-MIGRATION
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Hardened `SettlementResultDTO` and related telemetry DTOs to strictly use `int` (Pennies), eliminating float precision drift in reporting.

### ID: TD-ARCH-GOD-CMD-DIVERGENCE
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Synchronized naming from `god_command_queue` to `god_commands` (List) across `WorldState` and `SimulationState` for parity.

### ID: TD-LIFECYCLE-CONFIG-PARITY
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Implemented `BirthConfigDTO` and `DeathConfigDTO`, decoupling lifecycle subsystems from the raw global configuration module.

### ID: TD-MARKET-LEGACY-CONFIG
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Implemented `LaborMarketConfigDTO` and `StockMarketConfigDTO` ensuring strict DTO injection for all core markets.

### ID: TD-CRIT-FLOAT-CORE
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Forced quantization in `MAManager` via `round_to_pennies()` before initiating mergers, preventing float-to-penny conversion crashes.

### ID: TD-ECON-M2-INV
- **Status**: **Resolved** (Phase 34 - Mass Liquidation)
- **Solution**: Updated `calculate_total_money` logic to strictly separate liquidity sums from liability nets, preventing negative M2 inversion paradoxes.
