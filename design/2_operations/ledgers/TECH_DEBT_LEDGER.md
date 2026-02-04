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
| TD-187 | 2026-02-02 | Severance Pay Race Condition | Over-withdrawal during liq. | [Spec](../../3_work_artifacts/specs/TD-187_Severance_Waterfall.md) | **HIGH** |
| TD-187-DEBT | 2026-02-03 | Hardcoded Logic in Liquidation | Breaking encapsulation | - | Refactoring |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-194 | 2026-02-03 | HouseholdStateDTO Fragmentation | Missing critical fields | - | **MEDIUM** |
| TD-206 | 2026-02-03 | MortgageApplicationDTO Precision | Debt vs Payment mismatch | - | **MEDIUM** |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-196 | 2026-02-03 | ConfigManager Tight Coupling | Hard to mock; requires manual instantiation | - | **LOW** |
| TD-203 | 2026-02-03 | SettlementSystem Unit Test Stale | Tests not updated after Saga refactor | - | **HIGH** |
| TD-210 | 2026-02-04 | Test Dependency Bloat (`numpy`) | `conftest.py` imports CentralBank | [Review](../../_archive/gemini_output/pr_review_settlement-system-tests-2138438581752818541.md) | **LOW** |
| TD-212 | 2026-02-03 | Float-based Asset Callers | Legacy code accessing `assets` as `float` | [Spec](../../3_work_artifacts/drafts/draft_183800_Author_specification_for_Multi.md) | **MEDIUM** |
| TD-216 | 2026-02-04 | Orchestrator Coupling (`TickOrchestrator`) | Direct dependency on `Government` methods | [Insight](../../3_work_artifacts/reports/inbound/structural-god-class-9257244532893801478_audit_structural_god_class.md) | **MEDIUM** |


## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-150 | 2026-01-29 | Ledger Process | Loss of context | [Spec](../../3_work_artifacts/specs/spec_td150_ledger_automation.md) | **ACTIVE** |
| TD-183 | 2026-02-01 | Sequence Documentation | Migration gaps | - | **ACTIVE** |
| TD-188 | 2026-02-01 | Config Path Doc Drift | `PROJECT_STATUS.md` stale | - | **ACTIVE** |
| TD-193 | 2026-02-03 | Fragmented Politics | Spec vs Code drift | - | **WARNING** |
| TD-197 | 2026-02-03 | HousingManager Legacy | Architectural confusion | - | **MEDIUM** |
| TD-204 | 2026-02-03 | BubbleObservatory SRP | God class risk | [Insight](../../communications/insights/TD-161_SRP.md) | **MEDIUM** |
| TD-205 | 2026-02-03 | Phase3_Transaction God Class | Responsibility overload | [Insight](../../communications/insights/TD-161_SRP.md) | **MEDIUM** |
| TD-207 | 2026-02-03 | Synchronous Loan Staging | Logic drift | - | **LOW** |
| TD-208 | 2026-02-04 | Secured Loan SRP (Liquidation) | Logic inside Manager | [Review](../../_archive/gemini_output/pr_review_liquidation-manager-srp-1350862452554077041.md) | **MEDIUM** |
| TD-209 | 2026-02-04 | Hardcoded Agent Identifiers | String-based IDs in Registry | [Review](../../_archive/gemini_output/pr_review_liquidation-manager-srp-1350862452554077041.md) | **MEDIUM** |
| TD-213 | 2026-02-03 | Multi-Currency Transition Debt | Logic still dependent on `DEFAULT_CURRENCY` | [Insight](../../communications/insights/PH33_DEBUG.md) | **MEDIUM** |
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

---

> **Note**: For details on active items, see relevant insights.
