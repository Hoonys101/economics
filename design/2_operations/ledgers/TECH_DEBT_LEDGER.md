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
| TD-024 | 2026-02-05 | Multi-Currency Type Fragility | System-wide TypeError risk | [Insight](../../communications/insights/Bundle6_EngineHardening.md) | **ACTIVE** |
| TD-025 | 2026-02-05 | Brittle Dependency Injection in Saga | Hidden failures | [Insight](../../communications/insights/Bundle6_EngineHardening.md) | **ACTIVE** |

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

## 🏗️ ACTIVE DEBT DETAILS (최근 식별된 상세 부채)

### 🔴 TD-125: Frontend-Backend Contract Mismatch (High)
- **현상 (Phenomenon)**: Watchtower UI 스캐폴딩 과정에서 프론트엔드 TypeScript 인터페이스와 백엔드 Python DTO 간의 구조적 불일치 발견.
- **원인 (Cause)**: 구현 전 API 계약에 대한 동기화된 SSoT(Single Source of Truth) 부재.
- **해결책 제안 (Proposed Solution)**: 백엔드 DTO를 `PH6-WT-001` 계약에 맞게 수정하거나, 프론트엔드에 Adapter Pattern을 도입하여 데이터 형식을 변환할 것.

### 🟡 TD-015: Divergent Metric Calculation (Medium)
- **현상 (Phenomenon)**: 동일한 핵심 경제 지표(예: M2 Leak)를 계산하는 로직이 시스템 내 여러 위치(`TickOrchestrator`, `DashboardService`)에 분산되어 존재함.
- **원인 (Cause)**: 지표 계산을 중앙화된 서비스 대신 각 모듈 범위 내에서 독립적으로 구현함.
- **해결책 제안 (Proposed Solution)**: 모든 핵심 경제 지표 계산 로직을 `EconomicIndicatorTracker` 등으로 중앙화하고 SSoT 원칙 확립.

### 🟡 TD-024: Multi-Currency Type Fragility
- **Phenomenon**: `float`를 기대하던 시스템 전반에서 `MultiCurrencyWallet` (Dict) 도입으로 `TypeError`가 발생.
- **Cause**: 각 서브시스템이 `Wallet` 객체 대신 `float` 타입에 직접 의존하고 있었음.
- **Solution (Short-term)**: `balance.get(DEFAULT_CURRENCY, 0.0)`을 사용하여 방어적으로 기본 통화에 접근.
- **Lesson/Action Item**: `Wallet` 클래스에 `cash` 프로퍼티나 `__float__` 같은 어댑터 인터페이스를 제공하여 하위 호환성을 보장하고, DTO를 통한 타입 강제를 강화해야 함.

### 🟡 TD-025: Brittle Dependency Injection in Saga Handlers
- **Phenomenon**: `HousingTransactionSagaHandler`가 서비스 객체(`housing_service`)가 없는 `SimulationState` DTO를 받아 충돌 발생.
- **Cause**: `SettlementSystem.process_sagas`가 전체 `WorldState`나 `Simulation` 인스턴스 대신 상태 DTO만을 전달함.
- **Solution (Short-term)**: `getattr(simulation, 'housing_service', None)`으로 회피.
- **Lesson/Action Item**: Saga 처리기에 의존성을 주입하는 방식을 리팩토링하여 필요한 모든 서비스(World/Simulation)를 명시적으로 전달하도록 수정해야 함.

---

> **Note**: For details on active items, see relevant insights.
