# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| (No Active Items) | | | | |

## 🏭 2. FIRMS & CORPORATE

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (No Active Items) | | | | |

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
| (No Active Items) | | | | | |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-196 | 2026-02-03 | ConfigManager Tight Coupling | Hard to mock; requires manual instantiation | - | **LOW** |
| TD-203 | 2026-02-03 | SettlementSystem Unit Test Stale | Tests not updated after Saga refactor | - | **HIGH** |
| TD-210 | 2026-02-04 | Test Dependency Bloat (`numpy`) | `conftest.py` imports CentralBank | [Review](../../_archive/gemini_output/pr_review_settlement-system-tests-2138438581752818541.md) | **LOW** |
| (No Active Items) | | | | | |


## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-150 | 2026-01-29 | Ledger Process | Loss of context | [Spec](../../3_work_artifacts/specs/spec_td150_ledger_automation.md) | **ACTIVE** |
| TD-183 | 2026-02-01 | Sequence Documentation | Migration gaps | - | **ACTIVE** |
| TD-188 | 2026-02-01 | Config Path Doc Drift | `PROJECT_STATUS.md` stale | - | **ACTIVE** |
| TD-193 | 2026-02-03 | Fragmented Politics | Spec vs Code drift | - | **WARNING** |
| (No Active Items) | | | | | |
| TD-204 | 2026-02-03 | BubbleObservatory SRP | God class risk | [Insight](../../communications/insights/TD-161_SRP.md) | **MEDIUM** |
| TD-205 | 2026-02-03 | Phase3_Transaction God Class | Responsibility overload | [Insight](../../communications/insights/TD-161_SRP.md) | **MEDIUM** |
| TD-188 | 2026-02-04 | Dual Liquidation Logic Conflict | Write-off (Firm) vs Sell-off (Manager) mismatch | [Insight](../../communications/insights/TD-187_LIQUIDATION_REFACTOR.md) | **MEDIUM** |
| TD-208 | (RESOLVED) | | | | |
| TD-209 | 2026-02-04 | Hardcoded Agent Identifiers | String-based IDs in Registry | [Review](../../_archive/gemini_output/pr_review_liquidation-manager-srp-1350862452554077041.md) | **MEDIUM** |
| TD-213 | 2026-02-03 | Multi-Currency Transition Debt | Logic still dependent on `DEFAULT_CURRENCY` | [Insight](../../communications/insights/PH33_DEBUG.md) | **MEDIUM** |
| TD-220 | 2026-02-04 | Central Bank ID Mismatch (Str vs Int) | Inconsistent mapping in Wallet owner_id | [Review](../../_archive/gemini_output/pr_review_wo-4.2a-wallet-abstraction-7751802173364783425.md) | **LOW** |
| TD-224 | 2026-02-04 | Advisor-Policy Hardcoded Mapping | Firing logic coupled to tags | [Review](../../_archive/gemini_output/pr_review_wo-4.4-policy-lockout-15026198363404100995.md) | **MEDIUM** |
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

---

> **Note**: For details on active items, see relevant insights.
