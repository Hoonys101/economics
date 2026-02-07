# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-268 | 2026-02-06 | `BaseAgent` Constructor Overloading | Brittle dependency propagation | [Review](../../_archive/gemini_output/pr_review_fix-base-agent-memory-init-3901883710155225022.md) | **MEDIUM** |

## 🏭 2. FIRMS & CORPORATE

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-270 | 2026-02-06 | Firm-Department Tight Coupling | SoC Violation (Circular Ref) | [Audit Report](../../../reports/audits/audit_agents.md) | **MEDIUM** |
| TD-275 | 2026-02-07 | Dividend Logic Abstraction Leak | O(N*M) - Exposes Raw Agents | [Audit](../../3_work_artifacts/reports/inbound/structural-20241024-3897336574840583858_audit_structural_20241024.md) | **HIGH** |
| TD-276 | 2026-02-07 | HR/Finance Raw Agent Coupling | Abstraction Leak (List[Household]) | [Audit](../../3_work_artifacts/reports/inbound/structural-20241024-3897336574840583858_audit_structural_20241024.md) | **CRITICAL** |

## 🧠 3. DECISION & AI ENGINE (`ARCH_AI_ENGINE.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (No Active Items) | | | | | |

## 💹 4. MARKETS & ECONOMICS

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | | |


## 💸 5. SYSTEMS & TRANSACTIONS (`ARCH_TRANSACTIONS.md`)

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | | |
| TD-273 | 2026-02-06 | liquid_assets Protocol Bypass | Direct Manipulation | [Audit Report](../../../reports/audits/audit_agents.md) | **MEDIUM** |
| TD-274 | 2026-02-07 | `Bank` Class Saturation | Responsibilities Mix (>700 LOC) | [Audit](../../3_work_artifacts/reports/inbound/structural-20241024-3897336574840583858_audit_structural_20241024.md) | **MEDIUM** |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | | |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | | |


| TD-265 | 2026-02-06 | Configuration Access Unstandardized | Brittle `getattr` calling / Type safety | [Report](../../../reports/temp/report_20260206_135149_Architectural.md) | **MEDIUM** |
| TD-266 | 2026-02-06 | Sparse Firm ID Risk in TechnologyManager | Memory bloat if IDs are non-sequential | [Report](../../../reports/temp/report_20260206_135149_Architectural.md) | **LOW** |
| TD-277 | 2026-02-07 | `TickOrchestrator` Responsibility Mix | Mixed logic & orchestration phases | [Audit](../../3_work_artifacts/reports/inbound/structural-20241024-3897336574840583858_audit_structural_20241024.md) | **LOW** |
| (No Active Items) | | | | | |
| (No Active Items) | | | | | |
| (No Active Items) | | | | | |
| (No Active Items) | | | | | |
| (No Active Items) | | | | | |
| (No Active Items) | | | | | |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact | Refs |
|---|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints | Abandoned C++ | - |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Failed due to 'Mock-Magic' leaks | Architectural Bloat | - |

## ✅ RESOLVED DEBTS (상환 완료)

| ID | Resolution Date | Description | Spec Ref | Insight Report |
|---|---|---|---|---|
| TD-271 | 2026-02-07 | OrderBook IMarket Contract Violation | [Spec](../../3_work_artifacts/specs/PH7_HARDENING_SPEC_spec.md) | [Insight](../../_archive/gemini_output/pr_review_arch-hardening-ph7-11201669796122016862.md) |
| TD-272 | 2026-02-07 | Persistence Manager Purity Breach | [Spec](../../3_work_artifacts/specs/PH7_HARDENING_SPEC_spec.md) | [Insight](../../_archive/gemini_output/pr_review_arch-hardening-ph7-11201669796122016862.md) |
| TD-028 | 2026-02-05 | M2 Calculation Synchronization | Fixed via `_rebuild_currency_holders` (SSoT) | [Insight](../../communications/insights/mission_report_stress_test.md) |
| TD-231/232 | 2026-02-05 | System Integrity Cleanup (SalesTax/Inheritance) | [Audit](../../3_work_artifacts/reports/inbound/refactor_sales-tax-atomicity-inheritance-381587902011087733_audit_economic_WO_SALESTAX.md) | [Insight](../../communications/insights/Bundle_C_System_Integrity.md) |
| TD-225/223 | 2026-02-05 | Liquidation & DTO Unification | [Spec](../../3_work_artifacts/specs/TD-225_Unified_Liquidation.md) | [Insight](../../communications/insights/Bundle_C_System_Integrity.md) |
| TD-226 | 2026-02-05 | Gov Decoupling (WelfareManager Service) | [Handover](../../../reports/temp/report_20260205_190938_Architectural.md) | [Insight](../../communications/insights/Bundle_A_Government_Welfare.md) |
| TD-Audit | 2026-02-05 | Synchronous Inheritance Processing | [Handover](../../../reports/temp/report_20260205_190938_Architectural.md) | - |
| TD-193 | 2026-02-04 | Fragmented Politics Sync | [Spec](../../3_work_artifacts/specs/WO-4.5_Adaptive_Brain.md) | - |
| TD-238 | 2026-02-05 | Phases.py Decomposition | [Structural Audit](../../3_work_artifacts/reports/inbound/structural-structural-001-15007860028193717728_audit_structural_STRUCTURAL-001.md) | [Insight](../../communications/insights/Bundle_C_System_Integrity.md) |

| TD-035 | 2026-02-06 | Hardcoded Political AI Heuristics | [Spec](../../config/economy_params.yaml) | [Insight](../../communications/insights/structural_debt_clearance.md) |
| TD-254 | 2026-02-06 | Settlement Abstraction Leak (hasattr) | - | [Insight](../../communications/insights/structural_debt_clearance.md) |
| TD-188 | 2026-02-06 | Config Path Doc Drift | - | [Insight](../../communications/insights/structural_debt_clearance.md) |
| PH6-A | 2026-02-06 | Watchtower Hardening (SMA & Birth Rate) | [Spec](../../3_work_artifacts/specs/PH6_WATCHTOWER_REFINED.md) | [Insight](../../communications/insights/mission_watchtower_hardening.md) |
| WO-136 | 2026-02-06 | Vectorized Tech Diffusion (Numpy matrix) | [Spec](../../3_work_artifacts/specs/WO-136_CLEAN_SWEEP_REFINED.md) | [Insight](../../communications/insights/mission_clean_sweep_generalization.md) |
| TD-255 | 2026-02-06 | Housing Saga DTO Purity | [Spec](../../3_work_artifacts/specs/spec_combined_purity_reforms.md) | [Insight](../../communications/insights/PH7-A-PURITY.md) |
| TD-256 | 2026-02-06 | Inventory Abstraction (IInventoryHandler) | [Spec](../../3_work_artifacts/specs/spec_combined_purity_reforms.md) | [Insight](../../communications/insights/PH7-A-PURITY.md) |
| TD-263 | 2026-02-06 | Watchtower Observability Recovery | [Guide](../../3_work_artifacts/drafts/bundle_c_watchtower_fix_guide.md) | [Insight](../../communications/insights/watchtower_fix.md) |
| PH7-A | 2026-02-06 | Global Inventory Purity Reform | [Spec](../../3_work_artifacts/specs/spec_combined_purity_reforms.md) | [Insight](../../communications/insights/PH7-A-PURITY.md) |
| TD-FIX-ATTR | 2026-02-06 | BaseAgent memory_v2 init fix | - | [Insight](../../communications/insights/agent_memory_init_fix.md) |

| TD-250 | 2026-02-06 | Sales Tax & Inheritance Atomicity | [Audit](../../3_work_artifacts/reports/inbound/economic-jules-001-12984982393375704591_audit_economic_JULES_001.md) | [Insight](../../communications/insights/mission_report_economic_integrity.md) |
| TD-015 | 2026-02-05 | Divergent Metric Calculation (M0/M1/M2) | [Review](../../_archive/gemini_output/pr_review_watchtower-backend-6136124806422059806.md) | [Insight](../../communications/insights/PH6_STABILIZATION_REPORT.md) |
| TD-125 | 2026-02-05 | Watchtower Backend Refactor (DTO Sync) | [Review](../../_archive/gemini_output/pr_review_watchtower-backend-6136124806422059806.md) | [Insight](../../communications/insights/PH6_STABILIZATION_REPORT.md) |
| TD-029 | 2026-02-05 | Residual Macro Leak Identification | [Handover](../../../reports/temp/report_20260205_190938_Architectural.md) | [Insight](../../communications/insights/PH6_STABILIZATION_REPORT.md) |
| TD-240 | 2026-02-05 | Post-Merge Type Error (Altman Z) | [trace_leak error] | [Insight](../../communications/insights/TD-213-B_MultiCurrency_Migration.md) |
| TD-213-B | 2026-02-05 | Logic-wide Multi-Currency Migration | [Handover](../../../reports/temp/report_20260205_190938_Architectural.md) | [Insight](../../communications/insights/TD-213-B_MultiCurrency_Migration.md) |
| TD-226/227/228 | 2026-02-05 | Gov Decoupling & SRP Refactor | [Handover](../../../reports/temp/report_20260205_190938_Architectural.md) | [Insight](../../communications/insights/Bundle_A_Government_Welfare.md) |
| TD-233 | 2026-02-05 | FinanceDept LoD Violation | [Structural Audit](../../3_work_artifacts/reports/inbound/structural-structural-001-15007860028193717728_audit_structural_STRUCTURAL-001.md) | [Insight](../../communications/insights/TD-213-B_MultiCurrency_Migration.md) |
| TD-191 | 2026-02-03 | Weak Typing in Housing Logic | [Spec](../../3_work_artifacts/specs/spec_td191_tp_refactor.md) | [Insight](../../communications/insights/TD-191_ENCAPSULATION.md) |
| TD-198 | 2026-02-03 | MortgageApplicationDTO Inconsistency | [Spec](../../3_work_artifacts/specs/spec_h1_housing_v3_saga_blueprint.md) | [Insight](../../communications/insights/TD-198_SAGA.md) |
| TD-195 | 2026-02-03 | Loan ID Consistency (Int vs Str) | ^ | ^ |
| TD-199 | 2026-02-03 | SettlementSystem Mocking Fragility | ^ | ^ |
| TD-180 | 2026-02-04 | Test Suite Bloat & Factory Sync | [Spec](../../3_work_artifacts/specs/spec_td180_test_refactor.md) | [Insight](../../communications/insights/TD-180-Test-Refactor.md) |
| TD-190 | 2026-02-04 | Config Shadowing & God Object | [Spec](../../3_work_artifacts/specs/spec_td190_config_refactor.md) | [Insight](../../communications/insights/TD-190_Config_Refactor.md) |
| TD-161 | 2026-02-04 | Registry Decoupling & Phase Decomposition | [Spec](../../3_work_artifacts/specs/spec_td161_arch_refactor.md) | [Insight](../../communications/insights/TD-161_Architecture_Refactoring.md) |
| TD-211 | 2026-02-03 | `trace_leak.py` NameError Fix | [Handover](../../../reports/temp/report_20260205_190938_Architectural.md) | [Insight](../../communications/insights/PH33_DEBUG.md) |
| TD-160 | 2026-02-04 | Non-Atomic Inheritance | Fixed via deferred asset_transfer & inheritance manager | [Merge_8a7cff1](../../files_in_commit.txt) |
| TD-192 | 2026-02-04 | Direct Asset Manipulation in Emergency | Fixed via atomic sales_tax settlement in emergency handler | [Merge_8a7cff1](../../files_in_commit.txt) |
| TD-214 | 2026-02-04 | `Household` God Class Decomposition | [Spec](../../3_work_artifacts/specs/WO-4.0_Household_Mixins.md) | [Insight](../../communications/insights/WO-4.0.md) |
| TD-217 | 2026-02-04 | Protected Member Access (Snapshotting) | ^ | ^ |
| TD-215 | 2026-02-04 | Market Handler Abstraction Leaks | [Spec](../../3_work_artifacts/specs/WO-4.1_Market_Decoupling.md) | [Review](../../_archive/gemini_output/pr_review_wo-4.1-protocols-6715402864351195902.md) |
| TD-212 | 2026-02-04 | Legacy Assets (Float) Callers | [Spec](../../3_work_artifacts/specs/WO-4.2A_Wallet_Abstraction.md) | [Insight](../../communications/insights/WO-4.2A.md) |
| TD-216 | 2026-02-04 | TickOrchestrator Coupling | [Spec](../../3_work_artifacts/specs/WO-4.2B_Orchestrator_Alignment.md) | [Insight](../../communications/insights/WO-4.2B_Orchestrator_Alignment.md) |
| TD-187 | 2026-02-04 | Severance/Liquidation SRP | [Spec](../../3_work_artifacts/specs/TD-187_Severance_Waterfall.md) | [Insight](../../communications/insights/TD-187_LIQUIDATION_REFACTOR.md) |
| TD-207 | 2026-02-04 | Loan Saga Pattern | - | [Insight](../../communications/insights/LOAN_SAGA_REFACTOR.md) |
| TD-208 | 2026-02-04 | Liquidation Manager SRP | - | [Insight](../../communications/insights/TD-187_LIQUIDATION_REFACTOR.md) |
| TD-197 | 2026-02-04 | HousingManager Cleanup | - | [Insight](../../communications/insights/TD-197_HousingManager_Cleanup.md) |
| TD-194 | 2026-02-04 | Household DTO Sync | - | [Insight](../../communications/insights/TD-194_DTO_SYNC.md) |
| TD-206 | 2026-02-04 | Mortgage DTO Precision | - | [Insight](../../communications/insights/TD-206_PRECISION.md) |
| TD-203 | 2026-02-04 | SettlementSystem Test Upgrade | - | [Insight](../../communications/insights/INFRA_DEBT_BUNDLE_202602.md) |
| TD-204 | 2026-02-04 | BubbleObservatory SRP Refactor | - | [Insight](../../communications/insights/INFRA_DEBT_BUNDLE_202602.md) |
| TD-210 | 2026-02-04 | Test Dependency Cleanup | - | [Insight](../../communications/insights/INFRA_DEBT_BUNDLE_202602.md) |
| TD-223 | 2026-02-04 | Mortgage DTO Unification | - | [Insight](../../communications/insights/INFRA_DEBT_BUNDLE_202602.md) |
| TD-213 | 2026-02-04 | Multi-Currency Audit | - | [Insight](../../communications/insights/TD-213.md) |
| TD-150 | 2026-02-04 | Ledger Automation | - | [Insight](../../communications/insights/TD-150_Ledger_Automation.md) |
| TD-224 | 2026-02-04 | Governance Mapping Refactor | - | [Review](../../_archive/gemini_output/pr_review_identity-governance-refactor-17364238259413903980.md) |
| TD-209 | 2026-02-04 | Identifier Decoupling | - | [Review](../../_archive/gemini_output/pr_review_identity-governance-refactor-17364238259413903980.md) |
| TD-220 | 2026-02-04 | Central Bank ID Unification | - | [Review](../../_archive/gemini_output/pr_review_identity-governance-refactor-17364238259413903980.md) |
| TD-205 | 2026-10-04 | Transaction Engine SRP Refactor | [Spec](../../3_work_artifacts/specs/spec_td205_transaction_decomposition.md) | [Insight](../../communications/insights/TD-205_Transaction_Engine.md) |
| PH35-J2 | 2026-02-04 | Central Bank Service Implementation | [Spec](../../3_work_artifacts/specs/spec_phase35_central_bank.md) | [Insight](../../communications/insights/Mission_Phase5_Interfaces.md) |
| PH35-J3 | 2026-02-04 | Call Market Implementation | ^ | [Insight](../../communications/insights/CallMarket_Impl.md) |
| TD-230 | 2026-02-05 | M2 Integrity: Newborn Tracking leak | Fixed via LifecycleManager currency_holders update | [Walkthrough](../../../brain/a4ca8651-e1d6-40f9-96b7-5133429de32b/walkthrough.md) |
| TD-030 | 2026-02-06 | M2 Integrity: Registry Refactor | Fixed via StrictCurrencyRegistry & Lifecycle Suture | [Insight](../../communications/insights/Pulse_Integrity_Report.md) |
| TD-251 | 2026-02-06 | Stock Market IPO/SEO NULL Seller ID | Fixed in branch `fix-null-seller-id...` | [Review](../../_archive/gemini_output/pr_review_fix-null-seller-id-integrity-error-11984105662396074718.md) |
| TD-252 | 2026-02-06 | Massive M2 Leak (571k at Tick 100) | Resolved by formula correction & Registry fix | [Insight](../../communications/insights/Pulse_Integrity_Report.md) |
| TD-035 | 2026-02-06 | Residual M2 Drift from Bond Transactions | Tracked in [walkthrough.md](file:///C:/Users/Gram Pro/.gemini/antigravity/brain/becf7013-8d5e-43c8-8052-cd658d3936ea/walkthrough.md) | [Insight](../../communications/insights/Pulse_Integrity_Report.md) |
| TD-036 | 2026-02-06 | Sequencing Documentation Rot | ARCH_SEQUENCING vs tick_orchestrator.py | [Insight](../../communications/insights/Pulse_Integrity_Report.md) |
| TD-037 | 2026-02-06 | Firm Agent Stateful Component Drift | Violates stateless ARCH_AGENTS | [Insight](../../communications/insights/Pulse_Integrity_Report.md) |
| TD-038 | 2026-02-06 | ThoughtStream Instrumentation Blindspots | Labor, Pricing, Failed Matching | [Insight](../../communications/insights/Pulse_Integrity_Report.md) |
| TD-253 | 2026-02-06 | Settlement God Class Refactor (Track A) | Decoupled SagaOrchestrator & Kernel Hardening | [Review](../../_archive/gemini_output/pr_review_settlement-kernel-hardening-saga-decoupling-1046151433748562353.md) |
| TD-255 | 2026-02-06 | DTO Purity: Housing Saga Context | Snapshotting agent state at saga initiation | [Review](../../_archive/gemini_output/pr_review_housing-saga-dto-purity-7981336162459409252.md) |
| TD-256 | 2026-02-06 | Housing Service Inventory Abstraction | Decoupled SagaHandler via IInventoryHandler Protocol | [Review](../../_archive/gemini_output/pr_review_housing-saga-dto-purity-7981336162459409252.md) |
| TD-257/035 | 2026-02-06 | Absolute M2 Drift (0.0000% Leak) | Fixed via Bond Repayment tracking & Atomic Settlement | [Walkthrough](../../../brain/797943ac-fe9b-486b-b1b6-b7fbcc37a5f7/walkthrough.md) |
| TD-259 | 2026-02-06 | Asset Type Hardening (Dict/Float) | Hardened Vectorized Planner & Tracker for polymorphic assets | [Walkthrough](../../../brain/797943ac-fe9b-486b-b1b6-b7fbcc37a5f7/walkthrough.md) |
| TD-260 | 2026-02-06 | Household Wallet Delegation Breach | Fixed incorrect native interface calls (deposit/withdraw) | [Walkthrough](../../../brain/797943ac-fe9b-486b-b1b6-b7fbcc37a5f7/walkthrough.md) |

---

## 🏗️ ACTIVE DEBT DETAILS (최근 식별된 상세 부채)

### 🔴 TD-276: HR/Finance Raw Agent Coupling (Critical)
- **현상 (Phenomenon)**: `HRDepartment` 및 `FinanceDepartment`가 `Household` 객체 원본 리스트를 직접 소유하거나 순회함.
- **원인 (Cause)**: 에이전트 간 직접 참조를 허용하는 구조적 느슨함.
- **해결책 제안 (Proposed Solution)**: `List[int]` (ID)만 유지하고, 필요 시 `AgentRegistry`나 DTO를 통해 데이터에 접근하는 방식으로 전환.

### 🔴 TD-275: Dividend Logic Abstraction Leak (High)
- **현상 (Phenomenon)**: 배당금 지급 시 모든 Household를 O(N*M)으로 순회하며 주주를 찾음.
- **원인 (Cause)**: 주주 명부(Shareholder Registry) 부재로 인한 비효율적 검색 로직.
- **해결책 제안 (Proposed Solution)**: `ShareholderRegistry` 서비스를 도입하여 O(1) 또는 O(K) 검색이 가능하도록 개선.

### 🟡 TD-274: Bank Class Saturation (Medium)
- **현상 (Phenomenon)**: `Bank` 클래스가 700라인을 초과하며 입금, 대출, 청산 등 과도한 책임을 가짐.
- **원인 (Cause)**: 금융 서비스 로직의 미분별 수집.
- **해결책 제안 (Proposed Solution)**: `LoanManager`, `DepositManager` 등으로 기능을 분리하여 단일 책임 원칙 준수.

> **Note**: For details on active items, see relevant insights.
