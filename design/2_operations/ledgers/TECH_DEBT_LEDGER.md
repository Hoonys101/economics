# Technical Debt Ledger (기술부채 관리대장)

## 🟡 DEFERRED (Phase 27+ 상환 예정)

| ID | Date | Description | Remediation Plan | Impact | Status |
|---|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect in `firms.py` | Implementation of dynamic "Interview" system | Marginal Product of Labor 이론 위배 | **DEFERRED** |
| TD-006 | 2026-01-12 | Deterministic Class Caste (`core_agents.py`) | Dynamic Education Market implementation | Agency 상실 및 Class 고착화 강제 | **DEFERRED** |
| TD-007 | 2026-01-12 | Industrial Revolution Stress Test Config | Natural Equilibrium Config Tuning | 비현실적 경제 상태 (무한 수요) | **PENDING_IMPLEMENTATION** (Phase 28) |
| TD-073 | 2026-01-20 | Firm Component State Ownership | Transfer data ownership (assets, employees) from Firm to specialized departments | Architectural purity | **DEFERRED** (Phase D) |

---

## 🔴 ACTIVE (즉시 상환 필요)

| ID | Date | Description | Remediation Plan | Impact | Status |
|---|---|---|---|---|---|
| **TD-122** | 2026-01-26 | **Test Directory Organization** | Structure tests into unit/api/stress | Maintenance overhead | **DEFERRED** |
| **TD-132** | 2026-01-28 | **Hardcoded Government ID** | Dynamically resolve Government ID from WorldState | Registry Inconsistency Risk | **RESOLVED** |
| **TD-136** | 2026-01-28 | **Purity Gate Hardening** | Externalize rules from `verify_purity.py` to `pyproject.toml` | Maintainability | **RESOLVED** |
| **TD-140** | 2026-01-29 | **God File: `db/repository.py`** | Refactor database operations into specialized DAO/Repository mixins | 745+ LOC complexity | **ACTIVE** |
| **TD-141** | 2026-01-29 | **God File: `ai_driven_household_engine.py`** | Split logic into Sensory/Planning/Execution modules | 636+ LOC complexity | **ACTIVE** |
| **TD-142** | 2026-01-29 | **God File: `corporate_manager.py`** | Use Departmental Delegation (similar to WO-123) | 629+ LOC complexity | **ACTIVE** |
| **TD-143** | 2026-01-29 | **Hardcoded Placeholders (WO-XXX)** | Replace all `WO-XXX` tags in manuals with template variables or specific links | Documentation Debt | **ACTIVE** |
| **TD-118** | 2026-01-29 | **DTO Contract-Implementation Mismatch** | Refactor `HouseholdStateDTO.inventory` usage to respect List type or update DTO to Dict | Potential Runtime Errors / Confusion | **ACTIVE** |
| **TDL-028** | 2026-01-29 | **Inconsistent Order Object Structure** | Unify `Order` DTO interface or use ABC for `MarketOrder`/`StockOrder` separation | High Cognitive Load / Runtime Errors | **ACTIVE** |
| **TD-149** | 2026-01-29 | **Tight Coupling in Analysis Modules** | Implement `ISimulationState` protocol for observer modules | Reduced modularity | **RESOLVED** |
| **TD-150** | 2026-01-29 | **Ledger Management Process** | Document ledger format changes and historical data migration strategy | Loss of context | **ACTIVE** |
| **TD-151** | 2026-01-29 | **Partial DTO Adoption in Engine** | `Simulation.get_market_snapshot` returns `MarketSnapshotDTO`, but internal `_prepare_market_data` still returns generic Dict | Inconsistent Internal/External API | **ACTIVE** |
| **TD-152** | 2026-01-29 | **Hardcoded thresholds in StormVerifier** | Externalize ZLB, Deficit Spending thresholds, and `basic_food` string into `VerificationConfigDTO` | Configuration Flexibility / Maintainability | **RESOLVED** |
| **TD-153** | 2026-01-29 | **Hardcoded Stress Test Parameters** | Externalize stress test parameters in `scripts/run_stress_test_wo148.py` to a config file | Limited Reusability | **RESOLVED** |
| **TD-154** | 2026-01-29 | **Perfect Storm: Binary Outcome Bias** | Refactor `stress_test_perfect_storm.py` to focus on "Phenomena Reporting" (Resilience, Policy Synergy) rather than Pass/Fail verdicts | Loss of Economic Insight | **RESOLVED** |
| **TD-155** | 2026-01-29 | **Unsafe Dynamic Module Import** | Restrict `importlib` in `PhenomenaAnalyzer` to `modules.analysis.detectors` package and enforce whitelist | Security Risk (RCE) | **RESOLVED** |
| **TD-156** | 2026-01-30 | **Systemic Monetary Leak (M2 Drift)** | Audit all asset transfer points in `SettlementSystem` and `TransactionProcessor` for double-accounting or roundings. | Zero-Sum Violation (~900k drift) | **RESOLVED** (WO-996) |
| **TD-157** | 2026-01-30 | **Price-Consumption Deadlock** | Refactor `BasicMarket` to respond to inventory scarcity and fix Household demand elasticity. | Economic Collapse (Static Price) | **IN_PROGRESS** (Animal Spirits) |
| **TD-158** | 2026-01-30 | **Critical Housing System Leak** | Refactor `housing_system.py` (Rent/Loan/Trade) to use `SettlementSystem.transfer` instead of direct asset modification. | Direct Bypass of Monetary Integrity | **RESOLVED** (WO-996) |
| **TD-159** | 2026-01-30 | **Legacy Inheritance Redundancy** | Remove direct `_add_assets` calls in `demographic_manager.py` (Lines 303, 310); defer to `TransactionProcessor`. | Potential Double-Counting/Leak | **ACTIVE** |
| **TD-160** | 2026-01-30 | **Transaction-Tax Atomicity Failure** | Implement transaction-level atomicity in `TransactionProcessor` so taxes are always collected with the trade. | Policy Revenue Leak | **ACTIVE** |
| **TD-162** | 2026-01-30 | **Bloated God Class: Household** | Decompose `core_agents.py` (952 LOC) into Stateless Components (Bio, Econ, Social). | Maintenance/Testing Overhead | **ACTIVE** |
| **TD-163** | 2026-01-30 | **Test Suite Degradation (85+ Failures)** | Dedicated Test Restoration Sprint. Fix DTO mismatches in unit tests. | Zero Regression Guard | **CRITICAL** |
| **TD-164** | 2026-01-30 | **Missing Fractional Reserve (Full-Reserve Only)** | Implement WO-024 (Fractional Reserve Banking). | Economic Stagnation / Liquidity Bottleneck | **CRITICAL** |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints / Strategy change | Abandoning C++ Native path for now |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Attempted monolithic refactor; failed due to 'Mock-Magic' and context leaks. | Architectural Bloat / Testing Failure |

---

## 📅 REPAYMENT PLAN: "THE GREAT RESET" (Phase 24-26)

| Milestone | Target Debts | Objective | Tooling |
| :--- | :--- | :--- | :--- |
| **Step 1: Purity Guard** | TD-101, TD-102 | Create `SettlementSystem` to centralize all asset movements. | ✅ **DONE** (WO-112) |
| **Step 2: Abstraction Wall** | TD-103, TD-078 | Complete DTO-only conversion for all AI Decision Engines. | ✅ **DONE** (WO-135) |
| **Step 3: Formal Registry** | TD-104, TD-084 | Formalize all module interfaces (Bank, Tax, Govt) as Protocols. | ✅ **DONE** (WO-113) |
| **Step 4: Structural Reset** | TD-123, TD-124 | Split God Classes (`Household`, `TransactionProcessor`). | ✅ **DONE** (WO-123, WO-124) |
