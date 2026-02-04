# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | |

## 🏭 2. FIRMS & CORPORATE

| TD-213-B | 2026-02-04 | Logic-wide Multi-Currency Migration | Firms, Metrics, and AI still hardcoded to `DEFAULT_CURRENCY` | [Report](../../reports/temp/report_20260204_141709_Architectural.md) | **CRITICAL** |
| (No Active Items) | | | | | |

## 🧠 3. DECISION & AI ENGINE (`ARCH_AI_ENGINE.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 💹 4. MARKETS & ECONOMICS

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | |

## 💸 5. SYSTEMS & TRANSACTIONS (`ARCH_TRANSACTIONS.md`)

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | | |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-223 | 2026-02-04 | Loan DTO Duplication | Conflict between MortgageApplication and Request DTOs | [Review](../../_archive/gemini_output/pr_review_loan-saga-pattern-7704923262937636606.md) | **LOW** |
| (No Active Items) | | | | | |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | | |


## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-225 | 2026-02-04 | Dual Liquidation Logic Conflict | Write-off (Firm) vs Sell-off (Manager) mismatch | [Spec](../../3_work_artifacts/specs/TD-225_Unified_Liquidation.md) | **HIGH** |
| TD-205 | 2026-02-04 | Phase3_Transaction God Class | Responsibility overload | [Spec](../../3_work_artifacts/specs/TD-205_Transaction_Decomposition.md) | **ACTIVE** |
| (No Active Items) | | | | | |
| (No Active Items) | | | | | |
| (No Active Items) | | | | | |
| TD-183 | 2026-02-04 | Sequence Documentation Drift | Need to update Gov decision loops | **ACTIVE** |
| TD-188 | 2026-02-04 | Config Path Doc Drift | `PROJECT_STATUS.md` stale | **ACTIVE** |
| TD-193 | 2026-02-04 | Fragmented Politics Sync | Spec vs Code drift | [Spec](../../3_work_artifacts/specs/WO-4.5_Adaptive_Brain.md) | **RESOLVED** |
| TD-226 | 2026-02-04 | Government God Class & Hidden Deps | Components tightly coupled to central Agent | [Audit](../../3_work_artifacts/drafts/draft_134448_Synchronize_project_documentat.md) | **NEW** |
| TD-227 | 2026-02-04 | Gov Module Circular Dependency | Agent vs Components high-risk loop | ^ | **NEW** |
| TD-228 | 2026-02-04 | WelfareManager SRP Violation | Handles Tax, Welfare, and Stimulus | ^ | **NEW** |
| TD-229 | 2026-02-04 | Gov Module Test Coverage | High risk of undetected regressions | ^ | **CRITICAL** |
| TD-300 | 2026-02-04 | Unstable Gov DTO structures | Defensive `hasattr` checks required in snapshots | ^ | **NEW** |
| (No Active Items) | | | | |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact | Refs |
|---|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints | Abandoned C++ | - |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Failed due to 'Mock-Magic' leaks | Architectural Bloat | - |

## ✅ RESOLVED DEBTS (상환 완료)

| ID | Resolution Date | Description | Spec Ref | Insight Report |
|---|---|---|---|---|
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

---

> **Note**: For details on active items, see relevant insights.
