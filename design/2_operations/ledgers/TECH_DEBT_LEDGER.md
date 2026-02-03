# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-180 | 2026-02-01 | TestFile Bloat: `test_firm_decision_engine_new.py` | 828 lines; indicator of complex engine surface | **WARNING** |
| TD-201 | 2026-02-03 | Orphaned `reset_tick_flow` Method (Government) | M2 Delta tracking broken; potential data rot | **HIGH** |
| TD-202 | 2026-02-03 | Missing Escheated Asset Liquidation Logic | Dead assets (stocks) accumulate on Gov balance sheet | **MEDIUM** |

## 🏭 2. FIRMS & CORPORATE

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (No Active Items) | | | | |

## 🧠 3. DECISION & AI ENGINE (`ARCH_AI_ENGINE.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 💹 4. MARKETS & ECONOMICS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 💸 5. SYSTEMS & TRANSACTIONS (`ARCH_TRANSACTIONS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-160 | 2026-02-02 | Non-Atomic Inheritance (Direct Asset Transfer) | Money leaks during death; Partial state corruption | **CRITICAL** |
| TD-187 | 2026-02-02 | Severance Pay Race Condition | Over-withdrawal during firm liquidation | **HIGH** |
| TD-187-DEBT | 2026-02-03 | Hardcoded Logic & Fragile State in Liquidation | `LiquidationManager` uses hardcoded `haircut` (20%) and directly manipulates `PublicManager` state (`.managed_inventory`), breaking encapsulation. | Refactoring |
| TD-192 | 2026-02-03 | Direct Asset Manipulation (_assets Bypassing SettlementSystem) | Zero-Sum breakage; Magic Money leaks | **CRITICAL** |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-191 | 2026-02-03 | Weak Typing & DTO Contract Violation (Any Abuse) | Runtime errors; Maintenance nightmare | **FIXED** |
| TD-194 | 2026-02-03 | HouseholdStateDTO Fragmentation | Missing critical financial fields for DTI | **MEDIUM** |
| TD-198 | 2026-02-03 | MortgageApplicationDTO Inconsistency | Field name mismatches between APIs | **MEDIUM** |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-196 | 2026-02-03 | ConfigManager Tight Coupling | Hard to mock; requires manual instantiation | **LOW** |
| TD-199 | 2026-02-03 | SettlementSystem Mocking Fragility | hasattr check conflicts with MagicMock | **MEDIUM** |

## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-150 | 2026-01-29 | Ledger Management Process | Loss of context | **ACTIVE** |
| TD-183 | 2026-02-01 | Sequence Deviation Documentation | Fast-Fail Liquidation needs ARCH entry | **ACTIVE** |
| TD-188 | 2026-02-01 | Inconsistent Config Path Doc | `PROJECT_STATUS.md` path mismatch | **ACTIVE** |
| TD-190 | 2026-02-03 | Magic Number Proliferation (Hardcoded Simulation Constants) | Hard to tune/test; Fragile logic | **MEDIUM** |
| TD-193 | 2026-02-03 | Fragmented Implementation: Half-baked Political System | Spec (Leviathan) vs Code (ruling_party) drift; logic duplication | **WARNING** |
| TD-195 | 2026-02-03 | Loan ID Consistency (Int vs Str) | Potential KeyError in Saga/Market logic | **MEDIUM** |
| TD-197 | 2026-02-03 | Legacy HousingManager Dependency | Dual logic paths; architectural confusion | **MEDIUM** |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints | Abandoned C++ |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Failed due to 'Mock-Magic' leaks | Architectural Bloat |

---

### [2026-02-03] Weak Typing & Encapsulation Violation (TD-191)

- **현상 (Phenomenon)**:
  - `Any` 타입을 광범위하게 사용하여 런타임에 `AttributeError` 또는 `KeyError`가 발생할 위험이 높았음.
  - 시스템 로직(e.g., `HousingTransactionHandler`)이 에이전트(`Household`)의 내부 상태(`_econ_state.owned_properties`)를 직접 조작하여 캡슐화 원칙을 위반함.

- **원인 (Cause)**:
  - 초기 개발 단계에서 빠른 프로토타이핑을 위해 타입 검사를 느슨하게 적용함.
  - 객체 간의 책임과 경계가 명확히 정의되지 않아, 외부 객체가 내부 구현에 깊이 의존하게 됨.

- **해결 (Solution)**:
  - `Any`를 구체적인 `Protocol`과 `DTO`로 대체하여 컴파일 타임에 타입 정합성을 검증함. (`FiscalMonitor`, `CrisisMonitor` 등)
  - 에이전트에 상태를 변경하는 공개 메서드(`add_property`, `remove_property`)를 추가하고, 외부에서는 이 메서드를 통해서만 상태 변경을 요청하도록 수정 ("Tell, Don't Ask" 원칙 적용).
  - 변경 사항을 검증하기 위한 단위 테스트를 추가함.

- **교훈 (Lesson Learned)**:
  - 느슨한 타이핑은 단기적인 개발 속도를 높일 수 있지만, 장기적으로는 시스템의 복잡성과 예측 불가능성을 증가시켜 유지보수 비용을 급격히 상승시킨다.
  - 객체의 내부 상태는 반드시 캡슐화되어야 하며, 상태 변경은 명시적인 인터페이스(메서드)를 통해서만 이루어져야 한다.

---

### [2026-02-03] Atomic Housing Purchase Saga (V3) - (TD-198, TD-199)

- **현상 (Observation)**:
  1.  **테스트 Mock의 취약성**: `SettlementSystem`에서 `hasattr`로 에이전트 타입을 검사하는 로직이 `MagicMock`의 자동 속성 생성 기능과 충돌하여 테스트 시 논리 오류를 유발함.
  2.  **DTO 비호환성**: `housing_planner_api`와 `housing_purchase_api` 간 `MortgageApplicationDTO`의 필드명이 달라 호환성 레이어가 필요해짐.

- **원인 (Cause)**:
  1.  엄격한 인터페이스나 타입 체크 대신, 유연하지만 모호한 `hasattr` 방식에 의존.
  2.  기능 개발 과정에서 API DTO 명세가 파편화됨.

- **해결 (Resolution)**:
  1.  `unittest.mock.MagicMock` 생성 시 `spec` 인자를 사용하여 Mock 객체의 속성을 명시적으로 제한함.
  2.  `LoanMarket`에 임시 호환성 로직을 추가하여 두 DTO를 모두 처리함.

- **교훈 (Lesson Learned)**:
  - 핵심 로직에서는 `hasattr`보다 `isinstance`나 인터페이스 기반의 명시적 타입 체크를 사용하여 예측 가능성을 높여야 한다.
  - API DTO는 프로젝트 전반에 걸쳐 일관성을 유지하도록 관리해야 하며, 변경 시 파급 효과를 분석하고 통합 리팩토링 계획을 수립해야 한다.

---
