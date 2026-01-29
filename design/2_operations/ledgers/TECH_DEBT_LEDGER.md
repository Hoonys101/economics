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

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints / Strategy change | Abandoning C++ Native path for now |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Attempted monolithic refactor; failed due to 'Mock-Magic' and context leaks. | Architectural Bloat / Testing Failure |

---

## ✅ Resolved Debts (해결된 부채)

| ID | Date | Description | Solution | Impact | Status |
|---|---|---|---|---|---|
| TD-102 | 2026-01-23 | Residual Evaporation (Inheritance Leak) | Residual Catch-all (WO-112) | Systemic Deflation / Float Leak | **RESOLVED** |
| TD-104 | 2026-01-23 | Bank Interface Ghosting | Formalize `IBankService` Protocol (WO-113) | Design-Impl Gap | **RESOLVED** |
| TD-085 | 2026-01-22 | Firm Decision Mutual Exclusivity | Sequential processing in Firm Engine | GDP Ceiling | **RESOLVED** |
| TD-086 | 2026-01-22 | AI Agent Infant Survival | Configurable Engine Selection | Demographic Arch | **RESOLVED** |
| TD-074 | 2026-01-21 | `main.py` & `config.py` corruption | Restore from Git history | Blocked system | **RESOLVED** |
| TD-075 | 2026-01-21 | `Household` Facade Bloat | Refactored via EconComponent delegation | Maintenance overhead | **RESOLVED** |
| TD-076 | 2026-01-21 | `ProductionDepartment.produce` Redundancy | Refactor TFP calculation | Code readability | **RESOLVED** |
| TD-105 | 2026-01-24 | Positive Drift (+320) | Fix Reflux atomic transfer (TD-105) | Zero-sum violation | **RESOLVED** |
| TD-106 | 2026-01-24 | Bankruptcy Money Leak | Link Bankruptcy to Settlement (TD-106) | Zero-sum violation | **RESOLVED** |
| TD-112 | 2026-01-25 | Inheritance Rounding | Integer distribution (TD-112) | System Crash | **RESOLVED** |
| TD-110 | 2026-01-24 | Phantom Tax Revenue | Enforce Settle->Record pattern (WO-120) | Budget analytics failure | **RESOLVED** |
| TD-119 | 2026-01-26 | Implicit IBankService | Formalize IBankService Protocol (WO-120) | Interface Consistency | **RESOLVED** |
| TD-111 | 2026-01-24 | Reflux Alchemy (M2 Inflation) | Exclude `RefluxSystem` balance from M2 calculation | Monetary Integrity | **RESOLVED** |
| TD-116 | 2026-01-26 | Inheritance Residual Evaporation | Integer Distribution (Core Track) | Zero-Sum Integrity | **RESOLVED** |
| TD-120 | 2026-01-27 | Refactor TransactionProcessor Tax Calls | TaxAgency Injection (Track Bravo) | Maintenance Risk | **RESOLVED** |
| TD-121 | 2026-01-26 | Newborn Money Leak (DOA) | Initial Needs Config Injection (WO-121) | Agent Viability | **RESOLVED** |
| TD-101 | 2026-01-27 | Shadow Economy (Direct Mutation) | Enforce `SettlementSystem` usage (WO-125) | Zero-sum violation | **RESOLVED** |
| TD-117 | 2026-01-27 | DTO-Only Decisions (Regression) | Enforce Purity Gate (WO-125) | Purity Gate Violation | **RESOLVED** |
| TD-123 | 2026-01-27 | God Class: `Household` | Decompose into Stateless Components (WO-123) | Maintenance Overhead | **RESOLVED** |
| TD-124 | 2026-01-27 | God Class: `TransactionProcessor` | Split into 6-Layer Architecture (WO-124) | Scalability Risk | **RESOLVED** |
| TD-126 | 2026-01-27 | Implicit Bank Protocol | Formalize `IBankService` (TD-126) | Design-Impl Gap | **RESOLVED** |
| TD-130 | 2026-01-28 | Reflux System (Dark Pools) | Operation Sacred Refactoring (Purge Reflux) | Monetary Integrity | **RESOLVED** |
| TD-131 | 2026-01-28 | Monolithic TickScheduler | Operation Sacred Refactoring (Decomposition) | Architectural Clarity | **RESOLVED** |
| TD-103 | 2026-01-28 | Leaky AI Abstraction (Abstraction Wall) | Implemented DTO-only DecisionContext & Purity Gate (WO-135) | Encapsulation Purity | **RESOLVED** |
| TD-135 | 2026-01-28 | DTO Schema Inconsistency | Centralized DTOs in `simulation/api.py` (WO-135.2) | Interface Clarity | **RESOLVED** |
| TD-133 | 2026-01-28 | Global Config Pollution | Centralized `ScenarioStrategy` DTO & DI (WO-136) | Config Purity | **RESOLVED** |
| TD-134 | 2026-01-28 | Scenario-Specific Branching | Unified Strategy Flags in `ScenarioStrategy` (WO-136) | Architectural Clarity | **RESOLVED** |

---

## 🧐 SESSION INSIGHTS (2026-01-28)

### 1. Operation Abstraction Wall (WO-135)
- **현상**: 에이전트가 전역 `config` 및 라이브 객체에 직접 의존하여 결합도 위험 및 테스트 복잡성 증가.
- **해결**: `ConfigFactory` 도입, `DecisionContext`를 통한 DTO 주입, `verify_purity.py` 정적 분석 도구 통합.
- **교훈**: 아키텍처 원칙은 반드시 자동화된 도구(Linter/Purity Gate)로 강제해야 하며, DTO 기반 설계가 병렬 개발의 토대가 됨.

### 2. Operation Sacred Refactoring
- **현상**: `EconomicRefluxSystem`이라는 모호한 자금 싱크 존재 및 생산 단계 누락으로 인한 경제 왜곡.
- **해결**: `Reflux` 완전 삭제 및 국고 귀속(`Esheatment`) 로직 구현. `TickScheduler`를 7단계 `IPhaseStrategy`로 분해.
- **교훈**: "물리적 시간의 선후 관계"를 명시적인 오케스트레이션 페이즈로 관리하는 것이 경제 시스템의 인과 관계 증명에 필수적임.

### 3. Phase 23 Reactivation (WO-053)
- **현상**: 산업 혁명 시나리오가 아키텍처 변경으로 작동 불능 상태였음.
- **해결**: DTO 호환형 `verify_phase23.py` 수리 및 대규모 생산성 향상(`TFP=3.0`) 적용.
- **인사이트**: 풍요의 시대(Abundance)는 가격 수준의 급격한 하락을 동반하며, 이는 생존율을 높여 인구 폭증의 임계점(Critical Point)을 돌파하게 만듦.

### 4. Household Modularization (WO-141)
- **현상**: `HouseholdStateDTO.inventory` 필드는 공식적으로 `List[GoodsDTO]`로 정의될 수 있으나, 실제 의사결정 로직에서는 `household.inventory.get("basic_food")`와 같이 `Dict[str, float]`처럼 사용되고 있습니다.
- **원인**: 레거시 구현이 딕셔너리 형태의 접근에 의존하고 있었으며, 이번 리팩토링에서 동작 동등성을 유지하기 위해 해당 사용법을 그대로 유지했습니다. 이로 인해 공식 DTO 계약과 실제 구현 간의 불일치가 발생했습니다.
- **해결**: `HouseholdStateDTO`의 `inventory` 타입을 `Dict[str, float]`으로 명확히 확정하거나, 모든 관련 코드를 `List[GoodsDTO]`를 순회하여 사용하도록 리팩토링해야 합니다. 이 불일치는 향후 혼란과 잠재적 런타임 오류를 방지하기 위해 반드시 해결되어야 합니다.
- **교훈**: 대규모 리팩토링은 공식 데이터 계약(DTO)과 실제 구현 간의 숨겨진 불일치를 발견하는 계기가 될 수 있습니다. 동작 동등성 테스트는 기존의 코드 스멜을 유지하도록 강제할 수 있으며, 이러한 부분은 명시적인 기술 부채로 기록하고 추적해야 합니다.

---

---

## 📅 REPAYMENT PLAN: "THE GREAT RESET" (Phase 24-26)

| Milestone | Target Debts | Objective | Tooling |
| :--- | :--- | :--- | :--- |
| **Step 1: Purity Guard** | TD-101, TD-102 | Create `SettlementSystem` to centralize all asset movements. | ✅ **DONE** (WO-112) |
| **Step 2: Abstraction Wall** | TD-103, TD-078 | Complete DTO-only conversion for all AI Decision Engines. | ✅ **DONE** (WO-135) |
| **Step 3: Formal Registry** | TD-104, TD-084 | Formalize all module interfaces (Bank, Tax, Govt) as Protocols. | ✅ **DONE** (WO-113) |
| **Step 4: Structural Reset** | TD-123, TD-124 | Split God Classes (`Household`, `TransactionProcessor`). | ✅ **DONE** (WO-123, WO-124) |
| **Step 5: Normalize Sequence** | TD-106, TD-109 | Normalize Tick Sequence. | **PLANNED** (Phase 26) |
