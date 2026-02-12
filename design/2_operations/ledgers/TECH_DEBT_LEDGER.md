# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **WO-101** | Test | Core logic-protocol changes (e.g., wallet) break test mocks. | **High**: Logic brittleness/Drift. | Resolved |
| **TD-LEG-TRANS** | System | Legacy `TransactionManager` contains redundant/conflicting logic. | **Low**: Confusion & code bloat. | Pending Deletion |
| **TD-PRECISION** | Financials | Use of `float` for currency leads to precision dust/leaks over long runs. | **Medium**: Marginal zero-sum drift. | Identified (Next Priority) |
| **TD-CONFIG-MUT** | System | Scenarios directly mutate global config via `setattr`. | **Medium**: State pollution risk. | Identified (Next Priority) |
| **TD-COCKPIT-FE** | Simulation | **Ghost Implementation**: FE missing sliders/HUD for Cockpit (Phase 11) despite BE readiness. | **Medium**: Logic usability gap. | Identified |
| **TD-STR-GOD-DECOMP** | Architecture | **Residual God Classes**: `Firm` (1276 lines) and `Household` (1042 lines) exceed 800-line limit. | **Medium**: Maintenance friction. | Open |
| **TD-ARCH-LEAK-CONTEXT** | Finance | **Abstraction Leak**: `LiquidationContext` passes agent interfaces instead of pure DTO snapshots. | **Low**: Future coupling risk. | Identified |
| **TD-AGENT-STATE-INVFIRM** | Data/DTO | **Serialization Gap**: `AgentStateDTO` (save/load) does not support multi-slot inventories (e.g., `_input_inventory`). | **High**: Data loss on reload. | Open |
| **TD-ARCH-LEAK-PROTI** | Architecture | **Interface Drift**: `IFinancialEntity` still defines `deposit/withdraw` which now raise errors. | **Medium**: Type safety friction. | Resolved |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-DOC-PARITY** | Documentation | **Missing Manual**: `AUDIT_PARITY.md` missing from operations manuals. | **Low**: Knowledge loss. | Identified |
| **TD-ENFORCE-NONE** | System | **Protocol Enforcement**: Lack of static/runtime guards for architectural rules. | **High**: Regression risk. | Open (Phase 15) |
| **TD-CONFIG-LEAK** | Architecture | **Encapsulation**: Direct access to `agent.config` in internal systems. | **Medium**: Coupling risk. | Open |
| **TD-QE-MISSING** | Financials | **Logic Gap**: QE Bond Issuance logic lost during refactor. | **High**: Feature Regression. | Open |

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
| **TD-255** | Housing | **Hardening**: Replaced `hasattr` with `IHousingTransactionParticipant`. | PH12 (Shield) | [Insight](../_archive/insights/2026-02-09_System_Protocol_Composition_Pattern.md) |
| **TD-270** | Financials | **Protocol**: Unified asset representation & added `total_wealth`. | PH10 | [Repo](../_archive/gemini_output/pr_review_market-decoupling-v2-11057596794459553753.md) |
| **TD-271** | Firms | **Utilization**: RealEstateUtilizationComponent for production bonus. | PH10 | [Repo](../_archive/gemini_output/pr_review_market-decoupling-v2-11057596794459553753.md) |
| **TD-HYGIENE** | Tests / Infrastructure | **Restoration**: Fixed 618+ test collection errors & 80+ unit/integration failures after major refactor. | PH10.5 | [Handover](../HANDOVER.md) |
| **TD-CM-001** | Common | **Fix**: Patched `yaml.safe_load` for ConfigManager unit tests. | Clean Room Era | [Insight](../../design/3_work_artifacts/reports/inbound/unit-tests-mocking-10138789661756819849_mission_unit_test_hardening.md) |
| **TD-TM-001** | Systems | **Fix**: Implemented `FakeNumpy` for TechnologyManager unit tests. | Clean Room Era | [Insight](../../design/3_work_artifacts/reports/inbound/unit-tests-mocking-10138789661756819849_mission_unit_test_hardening.md) |
| **TD-ECO-INH** | Simulation | **Fix**: Resolved inheritance leaks via fallback Escheatment & Final Sweep. | Clean Room Era | [Audit Report](../../design/3_work_artifacts/reports/inbound/economic-integrity-audit-fixes-124275369_AUDIT_ECONOMIC_INTEGRITY.md) |
| **TD-STR-GOD** | Architecture | **Refactor**: Decomposed `Firm` and `Household` into Orchestrator-Engine pattern. | Refactoring Era | [Firm Insight](./firm_decomposition.md), [HH Insight](./HH_Engine_Refactor_Insights.md) |
| **TD-STR-LEAK** | Architecture | **Purification**: Removed raw agent handles from engines (Finance, HH, Firm). | Refactoring Era | [Audit Report](../../communications/insights/REFACTORING_COMPLIANCE_AUDIT.md) |
| **TD-FIN-ZERO** | Finance | **Fix**: Double-entry integrity in stateless finance engines (Retained Earnings). | Refactoring Era | [Finance Insight](../../communications/insights/TECH_DEBT_LEDGER.md) |
| **WO-101** | Test | **Restoration**: Fixed test mocks and signatures broken by SSoT migration. | Clean Room Era | [Audit Guide](../../design/3_work_artifacts/reports/audit_test_migration_guide.md) |
| **TD-ARCH-LEAK-PROTI** | Architecture | **Purification**: Migrated tests away from deprecated `deposit/withdraw` interfaces. | Clean Room Era | [Audit Guide](../../design/3_work_artifacts/reports/audit_test_migration_guide.md) |

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
### ID: TDL-031
### Title: QE Bond Issuance Logic Missing Post-Refactor
- **Date**: 2026-02-11
- **Component**: `modules.finance.system.FinanceSystem`
- **Issue**: QE Bond Issuance Logic Missing Post-Refactor
- **Description**: The `issue_treasury_bonds` function in the stateless `FinanceSystem` engine hardcodes the bond buyer as the primary commercial bank (`self.bank.id`). The original logic, which allowed the Central Bank to be the buyer under specific QE conditions (e.g., high debt-to-gdp), was lost during refactoring.
- **Impact**: The system can no longer properly simulate Quantitative Easing. Test `test_qe_bond_issuance` has a critical assertion marked as xfail to prevent build failure.
- **Reporter**: Jules (via PR #FP-INT-MIGRATION-02)
- **Status**: Open
---
### ID: TD-FIN-001
### Title: Impure Financial Engines (State Mutation)
- **Symptom**: `DebtServicingEngine`, `LiquidationEngine`, `LoanBookingEngine` directly mutate input DTOs.
- **Risk**: Breaks functional purity, creates race conditions, and complicates zero-sum verification.
- **Solution**: Refactor to `State_In -> State_Out` pattern using DTO copies.
---
### ID: TD-FIN-002
### Title: Monetary Unit Mismatch (Pennies vs Dollars)
- **Symptom**: Configs and Tax/Fiscal modules still use float dollars, requiring adapters in `TransactionManager`.
- **Risk**: Implicit unit conversions are high-friction and prone to 100x scaling errors.
- **Solution**: Complete the "Penny Standard" migration across all configurations and government modules.
---
### ID: TD-FIN-003
### Title: Bank Agent Residual State (SSoT Violation)
- **Symptom**: `Bank` agent maintains a `_wallet` separate from the `FinanceSystem` ledger.
- **Risk**: Desync between agent wallet and central ledger.
- **Solution**: Remove `self._wallet` and delegate all state access to `FinanceSystem`.
---
### ID: TD-FIN-004
### Title: Missing Sovereign Risk Premium Logic
- **Symptom**: `issue_treasury_bonds` uses fixed spreads regardless of debt levels.
- **Risk**: Inability to model fiscal sustainability crises.
- **Solution**: Integrate `debt_to_gdp` based feedback loops into bond yield calculations.
---
---
### ID: TD-INV-SLOT
### Title: Inventory Slot Protocol Violation (input_inventory)
- **Symptom**: `input_inventory` for raw materials is mutated directly by `GoodsHandler`, `Registry`, and `Bootstrapper` using raw dict access.
- **Risk**: Quality-averaging logic is bypassed, leading to data drift. SRP violation by multiple modules owning the mutation logic.
- **Solution**: Extend `IInventoryHandler` with `InventorySlot` support and refactor all call sites to use protocol methods.
- **Reported**: `audit_inventory_purity_20260211.md`

---
### ID: TD-LIF-RESET
### Title: Missing Tick-Level State Reset (Household Agent)
- **Symptom**: `Household` agents lack a `reset()` method. `labor_income_this_tick`, `current_consumption`, etc., are never cleared.
- **Risk**: Violates "Late-Reset Principle". Analytics and AI training receive cumulative instead of marginal (per-tick) data, corrupting long-run dynamics.
- **Solution**: Implement `Household.reset_tick_state()` and orchestrate via `AgentLifecycleManager`.
- **Reported**: `audit_lifecycle_hygiene_20260211.md`

---
### ID: TD-FIN-FORT
### Title: Financial Fortress Protocol Violation (Direct Wallet Mutation)
- **Symptom**: `Household.deposit/withdraw` and `Firm.load_state` allow direct mutation of `_wallet` bypassing `SettlementSystem`.
- **Risk**: "Ghost Money" creation during agent cloning/instantiation. Breaks Double-Entry integrity.
- **FinanceSystem Schizophrenia**: Parallel ledger in `FinanceSystem` drifts from agent wallets.
- **Solution**: Remove direct mutation APIs. Force all transfers through `SettlementOrder` commands via `SettlementSystem`.
- **Solution**: Remove direct mutation APIs. Force all transfers through `SettlementOrder` commands via `SettlementSystem`.
- **Lesson Learned**: SSoT must be absolute. Dual-writes always drift.
- **Resolved in**: `refactor/financial-fortress-ssot`

---
### ID: TD-AGENT-STATE-INVFIRM
### Title: Serialization Gap in AgentStateDTO
- **Symptom**: `AgentStateDTO` (save/load) does not support multi-slot inventories (e.g., `_input_inventory`).
- **Risk**: Saving and loading a simulation results in loss of all non-`MAIN` inventory data for firms.
- **Solution**: Update `AgentStateDTO` to support a map of slots to inventories.
- **Reported**: `review_backup_20260212_073151_Analyze_this_PR.md`

---
### ID: TD-ARCH-LEAK-PROTI
### Title: Residual Interface Drift (IFinancialEntity)
- **Symptom**: `IFinancialEntity` still defines `deposit/withdraw` which now raise `NotImplementedError`.
- **Risk**: Breaks type safety assumptions for consumers.
- **Solution**: Fully retire `IFinancialEntity` in favor of `IFinancialAgent` or direct `SettlementSystem` usage.
- **Reported**: `review_backup_20260212_081300_Analyze_this_PR.md`

---
### ID: TD-ARCH-DI-SETTLE
### Title: Dependency Injection Fragility in Settlement System
- **Symptom**: `AgentRegistry` is injected into `SettlementSystem` post-initialization.
- **Risk**: Circular dependency risks during startup; fragile initialization order.
- **Solution**: Implement a proper DI container or split initialization into distinct registration phases.
- **Reported**: `review_backup_20260212_081300_Analyze_this_PR.md`

---
### ID: TD-COCKPIT-FE
### Title: Simulation Cockpit Frontend Ghost Implementations
- **Symptom**: `PROJECT_STATUS.md` marks Phase 11 (Cockpit) as completed, but `frontend/src` lacks Base Rate/Tax sliders, Command Stream Intervention UI, and "M2 Leak" header stats.
- **Risk**: Backend capabilities (WebSocket endpoints, DTOs) are unusable by the end-user. Disconnect between project metrics and actual UX.
- **Solution**: Implement missing React components in `GovernmentTab.tsx`, `FinanceTab.tsx`, and Header HUD.
- **Reported**: `PROJECT_PARITY_AUDIT_REPORT_20260212.md`

---
### ID: TD-STR-GOD-DECOMP
### Title: Residual Orchestrator Bloat (Firm & Household)
- **Symptom**: `Firm` (1276 lines) and `Household` (1042 lines) remain over the 800-line limit despite engine delegation.
- **Root Cause**: Extensive property delegation, interface implementation, and legacy mixin methods.
- **Solution**: Further extract non-core orchestrator logic (e.g., `BrandManager` in Firms, `Legacy Mixins` in Households) into dedicated service components.
- **Reported**: `STRUCTURAL_AUDIT_REPORT.md` (2026-02-12)

---
### ID: TD-ARCH-LEAK-CONTEXT
### Title: Interface-based Abstraction Leaks in Contexts
- **Symptom**: `LiquidationContext` and `FiscalContext` pass `IFinancialEntity` (Agent) instead of raw DTOs or Snapshots.
- **Risk**: Agents are technically "passed around" the simulation, increasing coupling and bypass risks.
- **Solution**: Refactor these contexts to accept only Pydantic/Dataclass DTOs or specialized Services.
- **Reported**: `STRUCTURAL_AUDIT_REPORT.md` (2026-02-12)

---
### ID: TD-DOC-PARITY
### Title: Missing Operations Manual for Parity Audits
- **Symptom**: `PROJECT_PARITY_AUDIT_REPORT_20260212.md` identified that the standard reference manual `design/2_operations/manuals/AUDIT_PARITY.md` is missing.
- **Risk**: Inconsistency in future parity audits due to lack of defined methodology.
- **Solution**: Restore or recreate the `AUDIT_PARITY.md` manual.
- **Reported**: `PROJECT_PARITY_AUDIT_REPORT_20260212.md`
