# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-180 | 2026-02-01 | TestFile Bloat: `test_firm_decision_engine_new.py` | 828 lines; indicator of complex engine surface | **WARNING** |

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
| TD-187-LEAK | 2026-02-03 | Asset-Rich Cash-Poor Asset Leak | Zero-Sum Violation; PublicManager Seizure | **CRITICAL** |
| TD-192 | 2026-02-03 | Direct Asset Manipulation (_assets Bypassing SettlementSystem) | Zero-Sum breakage; Magic Money leaks | **CRITICAL** |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-191 | 2026-02-03 | Weak Typing & DTO Contract Violation (Any Abuse) | Runtime errors; Maintenance nightmare | **HIGH** |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-150 | 2026-01-29 | Ledger Management Process | Loss of context | **ACTIVE** |
| TD-183 | 2026-02-01 | Sequence Deviation Documentation | Fast-Fail Liquidation needs ARCH entry | **ACTIVE** |
| TD-188 | 2026-02-01 | Inconsistent Config Path Doc | `PROJECT_STATUS.md` path mismatch | **ACTIVE** |
| TD-190 | 2026-02-03 | Magic Number Proliferation (Hardcoded Simulation Constants) | Hard to tune/test; Fragile logic | **MEDIUM** |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints | Abandoned C++ |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Failed due to 'Mock-Magic' leaks | Architectural Bloat |

---

### ID: TD-187-LIQUIDATION-ASSET-LEAK

*   **현상 (Phenomenon)**
    기업 파산 청산 시, 현금성 자산(`finance.balance`)만 채권자에게 분배되고, 재고나 자본재 등 비현금성 자산은 그 가치가 평가/분배되지 않고 `PublicManager`에게 몰수됨.

*   **원인 (Cause)**
    `LiquidationManager`가 오직 기업의 현금 잔고만을 사용하여 청산 폭포(waterfall)를 실행함. 비현금성 자산의 가치를 현금화하여 분배하는 로직이 부재함.

*   **영향 (Impact)**
    자산은 많지만 현금이 부족한(Asset-Rich, Cash-Poor) 기업이 파산할 경우, 직원 퇴직금 등 우선순위 채권이 지급되지 않음. 자산 가치가 채권자가 아닌 국가(PublicManager)에게로 이전되어, 사실상의 부의 불공정 이전이 발생하며 중대한 Zero-Sum 원칙을 위반함.

*   **교훈 (Lesson Learned)**
    기업 청산(liquidation)은 단순한 현금 분배가 아니라, 모든 자산의 공정 가치 평가 및 현금화를 포함하는 복잡한 프로세스임을 인지해야 함. MVP 구현 시 이러한 제약사항과 그 경제적 영향을 명확히 문서화하고 즉시 개선 과제로 등록해야 한다.
