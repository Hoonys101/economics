# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-030 | 2026-02-05 | Agent Lifecycle-M2 Desync | Performance (O(N) rebuild) | [Walkthrough](../../../brain/7064e76f-bfd2-423d-9816-95b56f05a65f/walkthrough.md) | **ACTIVE** |

## 🏭 2. FIRMS & CORPORATE

| (No Active Items) | | | | | |

## 🧠 3. DECISION & AI ENGINE (`ARCH_AI_ENGINE.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 💹 4. MARKETS & ECONOMICS

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | | |

## 💸 5. SYSTEMS & TRANSACTIONS (`ARCH_TRANSACTIONS.md`)

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-015 | 2026-02-05 | Divergent Metric Calculation | SSoT Deviation | [Review](../../_archive/gemini_output/pr_review_ph6-watchtower-dashboard-15887853336717342464.md) | **ACTIVE** |
| TD-029 | 2026-02-05 | Residual Macro Leak (-71,328) | Baseline Variance | [Walkthrough](../../../brain/7064e76f-bfd2-423d-9816-95b56f05a65f/walkthrough.md) | **PLANNED** |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-125 | 2026-02-05 | Watchtower Contract Mismatch | API Desync | [Review](../../_archive/gemini_output/pr_review_ph6-watchtower-scaffold-18088587128119282769.md) | **ACTIVE** |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | | |


## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | | |
| TD-188 | 2026-02-04 | Config Path Doc Drift | `PROJECT_STATUS.md` stale | **ACTIVE** |
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
| TD-028 | 2026-02-05 | M2 Calculation Synchronization | Fixed via `_rebuild_currency_holders` (SSoT) | [Insight](../../communications/insights/mission_report_stress_test.md) |
| TD-231/232 | 2026-02-05 | System Integrity Cleanup (SalesTax/Inheritance) | [Audit](../../3_work_artifacts/reports/inbound/refactor_sales-tax-atomicity-inheritance-381587902011087733_audit_economic_WO_SALESTAX.md) | [Insight](../../communications/insights/Bundle_C_System_Integrity.md) |
| TD-225/223 | 2026-02-05 | Liquidation & DTO Unification | [Spec](../../3_work_artifacts/specs/TD-225_Unified_Liquidation.md) | [Insight](../../communications/insights/Bundle_C_System_Integrity.md) |
| TD-193 | 2026-02-04 | Fragmented Politics Sync | [Spec](../../3_work_artifacts/specs/WO-4.5_Adaptive_Brain.md) | - |
| TD-238 | 2026-02-05 | Phases.py Decomposition | [Structural Audit](../../3_work_artifacts/reports/inbound/structural-structural-001-15007860028193717728_audit_structural_STRUCTURAL-001.md) | [Insight](../../communications/insights/Bundle_C_System_Integrity.md) |

| TD-240 | 2026-02-05 | Post-Merge Type Error (Altman Z) | [trace_leak error] | [Insight](../../communications/insights/TD-213-B_MultiCurrency_Migration.md) |
| TD-213-B | 2026-02-05 | Logic-wide Multi-Currency Migration | [Spec](../../3_work_artifacts/drafts/draft_232153__ObjectivenResolve_TD213B.md) | [Insight](../../communications/insights/TD-213-B_MultiCurrency_Migration.md) |
| TD-226/227/228 | 2026-02-05 | Gov Decoupling & SRP Refactor | [Spec](../../3_work_artifacts/drafts/draft_232211__ObjectivenResolve_TD226_.md) | [Insight](../../communications/insights/Bundle_A_Government_Welfare.md) |
| TD-233 | 2026-02-05 | FinanceDept LoD Violation | [Structural Audit](../../3_work_artifacts/reports/inbound/structural-structural-001-15007860028193717728_audit_structural_STRUCTURAL-001.md) | [Insight](../../communications/insights/TD-213-B_MultiCurrency_Migration.md) |
| TD-191 | 2026-02-03 | Weak Typing in Housing Logic | [Spec](../../3_work_artifacts/specs/spec_td191_tp_refactor.md) | [Insight](../../communications/insights/TD-191_ENCAPSULATION.md) |
| TD-198 | 2026-02-03 | MortgageApplicationDTO Inconsistency | [Spec](../../3_work_artifacts/specs/spec_h1_housing_v3_saga_blueprint.md) | [Insight](../../communications/insights/TD-198_SAGA.md) |
| TD-195 | 2026-02-03 | Loan ID Consistency (Int vs Str) | ^ | ^ |
| TD-199 | 2026-02-03 | SettlementSystem Mocking Fragility | ^ | ^ |
| TD-180 | 2026-02-04 | Test Suite Bloat & Factory Sync | [Spec](../../3_work_artifacts/specs/spec_td180_test_refactor.md) | [Insight](../../communications/insights/TD-180-Test-Refactor.md) |
| TD-190 | 2026-02-04 | Config Shadowing & God Object | [Spec](../../3_work_artifacts/specs/spec_td190_config_refactor.md) | [Insight](../../communications/insights/TD-190_Config_Refactor.md) |
| TD-161 | 2026-02-04 | Registry Decoupling & Phase Decomposition | [Spec](../../3_work_artifacts/specs/spec_td161_arch_refactor.md) | [Insight](../../communications/insights/TD-161_Architecture_Refactoring.md) |
| TD-211 | 2026-02-03 | `trace_leak.py` NameError Fix | [Spec](../../3_work_artifacts/drafts/draft_183800_Author_specification_for_Multi.md) | [Insight](../../communications/insights/PH33_DEBUG.md) |
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
| TD-230 | 2026-02-04 | M2 Integrity: Newborn Tracking leak | Fixed via LifecycleManager currency_holders update | [Walkthrough](../../../brain/a4ca8651-e1d6-40f9-96b7-5133429de32b/walkthrough.md) |

---

## 🏗️ ACTIVE DEBT DETAILS (최근 식별된 상세 부채)

### 🔴 TD-125: Frontend-Backend Contract Mismatch (High)
- **현상 (Phenomenon)**: Watchtower UI 스캐폴딩 과정에서 프론트엔드 TypeScript 인터페이스와 백엔드 Python DTO 간의 구조적 불일치 발견.
- **원인 (Cause)**: 구현 전 API 계약에 대한 동기화된 SSoT(Single Source of Truth) 부재.
- **해결책 제안 (Proposed Solution)**: 백엔드 DTO를 `PH6-WT-001` 계약에 맞게 수정하거나, 프론트엔드에 Adapter Pattern을 도입하여 데이터 형식을 변환할 것.

### 🟡 TD-015: Divergent Metric Calculation (Medium)
- **현상 (Phenomenon)**: 동일한 핵심 경제 지표(예: M2 Leak)를 계산하는 로직이 시스템 내 여러 위치(`TickOrchestrator`, `DashboardService`)에 분산되어 존재함.
- **원인 (Cause)**: 지표 계산을 중앙화된 서비스 대신 각 모듈 범위 내에서 독립적으로 구현함.
- **해결책 제안 (Proposed Solution)**: 모든 핵심 경제 지표 계산 로직을 `EconomicIndicatorTracker` 등으로 중앙화하고 SSoT 원칙 확립.

---

> **Note**: For details on active items, see relevant insights.
