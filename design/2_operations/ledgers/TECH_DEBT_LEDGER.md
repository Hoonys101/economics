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
| TD-198 | 2026-02-03 | MortgageApplicationDTO Inconsistency | Field name mismatches between APIs | **FIXED** |
| TD-206 | 2026-02-03 | MortgageApplicationDTO Precision | Uses total debt instead of monthly payments | **MEDIUM** |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-196 | 2026-02-03 | ConfigManager Tight Coupling | Hard to mock; requires manual instantiation | **LOW** |
| TD-199 | 2026-02-03 | SettlementSystem Mocking Fragility | hasattr check conflicts with MagicMock | **FIXED** |
| TD-203 | 2026-02-03 | SettlementSystem Unit Test Stale | Tests not updated after Saga refactor | **HIGH** |

## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-150 | 2026-01-29 | Ledger Management Process | Loss of context | **ACTIVE** |
| TD-183 | 2026-02-01 | Sequence Deviation Documentation | Fast-Fail Liquidation needs ARCH entry | **ACTIVE** |
| TD-188 | 2026-02-01 | Inconsistent Config Path Doc | `PROJECT_STATUS.md` path mismatch | **ACTIVE** |
| TD-190 | 2026-02-03 | Magic Number Proliferation (Hardcoded Simulation Constants) | Hard to tune/test; Fragile logic | **MEDIUM** |
| TD-193 | 2026-02-03 | Fragmented Implementation: Half-baked Political System | Spec (Leviathan) vs Code (ruling_party) drift; logic duplication | **WARNING** |
| TD-195 | 2026-02-03 | Loan ID Consistency (Int vs Str) | Potential KeyError in Saga/Market logic | **FIXED** |
| TD-197 | 2026-02-03 | Legacy HousingManager Dependency | Dual logic paths; architectural confusion | **MEDIUM** |
| TD-204 | 2026-02-03 | BubbleObservatory SRP Violation | Handles calculation, logging, and alerts | **MEDIUM** |
| TD-205 | 2026-02-03 | Phase3_Transaction God Class | Too many responsibilities (Tax, Banks, Infra) | **MEDIUM** |
| TD-161 | 2026-02-03 | RealEstateUnit Dependency on Registry | Data model depends on service interface | **HIGH** |
| TD-207 | 2026-02-03 | Synchronous Loan Staging | Logic drift from "Staging" spec (immediate grant) | **LOW** |

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

### [2026-02-03] Multi-Tick Housing Saga & Lien System Integration (TD-198, TD-195, TD-199)

- **현상 (Phenomenon)**:
    - 주택 거래가 틱 간 상태를 유지하지 못해 파산이나 데이터 불일치에 취약했음.
    - `MortgageApplicationDTO` 필드 불일치(TD-198)와 Loan ID 타입 혼선(TD-195)으로 인한 기동성 저하.
    - `SettlementSystem` 테스트 시 `MagicMock`이 `hasattr` 체크를 방해하여 거짓 양성(False Positive) 발생(TD-199).

- **원인 (Cause)**:
    - 초기 설계의 단순성 지향이 복잡한 다자간 거래(사가) 환경에서 한계에 도달함.
    - 파편화된 API 개발로 DTO 명세가 중앙에서 관리되지 않음.

- **해결 (Solution)**:
    - **5단계 상태 머신**: INITIATED부터 TRANSFER_TITLE까지의 명시적 상태 전이 로직 구현.
    - **Lien 시스템**: `RealEstateUnit`에 `liens: List[LienDTO]`를 도입하여 다중 담보 지원 및 하위 호환성 확보.
    - **DTO 중앙화**: `modules/market/housing_planner_api.py`를 정본으로 하여 `MortgageApplicationDTO` 통일.
    - **Mocking 정교화**: `spec` 인자를 사용하여 `MagicMock`의 속성 노출을 제한하여 `hasattr` 호환성 확보.

- **교훈 (Lesson Learned)**:
    - 복잡한 도메인(부동산 금융)은 초기부터 사가 패턴과 같은 분산 트랜잭션 설계를 고려해야 함.
    - 데이터 모델과 서비스 인터페이스 간의 경계를 명확히 하고, DTO는 일관된 소스에서 관리되어야 함.

---

### [2026-02-03] RealEstateUnit Dependency & SRP Violations (TD-161, TD-204, TD-205)

- **현상 (Observation)**:
    - `RealEstateUnit`이 `is_under_contract` 상태 조회를 위해 서비스 계층(`IRealEstateRegistry`)을 직접 참조함. (TD-161)
    - `BubbleObservatory`와 `Phase3_Transaction`이 너무 많은 책임을 보유한 "God Class" 형태를 띰.

- **위험 (Risk)**:
    - 데이터 객체가 무거워져 직렬화 및 테스트가 어려워짐.
    - 모듈 간 결합도가 높아져 특정 기능 변경이 전체 시스템에 예기치 못한 영향을 미침.

- **향후 계획 (Next Steps)**:
    - `RealEstateUnit`의 행위 로직을 `HousingService`로 완전히 이전하여 순수 데이터 컨테이너로 리팩토링.
    - `BubbleObservatory`의 측정(Tracker)과 알림(Alert) 로직 분리.
    - `Phase3_Transaction`의 과다한 프로세싱 로직을 하위 전문 Phase로 분산 배치.

---
