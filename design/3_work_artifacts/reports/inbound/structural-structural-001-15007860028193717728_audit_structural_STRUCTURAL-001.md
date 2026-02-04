# Structural Audit Report [STRUCTURAL-001]

**Date:** 2025-05-21
**Auditor:** Jules (AI)
**Task ID:** STRUCTURAL-001
**Scope:** Structural integrity, God Class detection, Abstraction Leaks.

---

## 1. Executive Summary
This audit scanned the codebase for structural issues defined in `AUDIT_STRUCTURAL.md`. No critical "God Classes" (> 800 lines) were found, but two files are approaching the limit. Several abstraction leaks were identified where raw agent objects are passed into service components or accessed improperly, violating the Law of Demeter and Purity Gates.

---

## 2. Saturation Report (God Class Candidates)
No file currently exceeds 800 lines. However, the following are near saturation and require monitoring or decomposition:

| File | Lines | Risk Level | Recommendation |
|------|-------|------------|----------------|
| `simulation/systems/settlement_system.py` | 766 | High | Monitor. If it grows, split into sub-handlers (e.g., `TransferHandler`, `SagaHandler`). |
| `simulation/orchestration/phases.py` | 764 | High | **Refactor Priority.** Split phases into separate files under `simulation/orchestration/phases/`. |

---

## 3. Abstraction Leak Audit (Dependency Hell)

### 3.1. FinanceDepartment Leak (Critical)
- **Location:** `simulation/components/finance_department.py`
- **Method:** `process_profit_distribution`
- **Issue:** Accesses private internal state of `Household` agents directly:
  ```python
  shares = household._econ_state.portfolio.to_legacy_dict().get(self.firm.id, 0.0)
  ```
- **Violation:** Law of Demeter, Agent Encapsulation. `_econ_state` is private.
- **Remediation:** Introduce `IShareholderRegistry` or use a DTO-based interface to query shareholdings without exposing the entire agent state.

### 3.2. WelfareService Raw Agent Leak (Medium)
- **Location:** `modules/government/welfare/service.py`
- **Method:** `run_welfare_check`
- **Issue:** Iterates over a list of raw `Household` objects (`List[Any]`) and uses `hasattr` checks:
  ```python
  if hasattr(agent, "needs") and hasattr(agent, "is_employed"):
  ```
- **Violation:** Loose coupling. Services should ideally operate on DTOs (`WelfareContextDTO`) or a strict Interface (`IWelfareRecipient`).
- **Remediation:** Define `IWelfareRecipient` protocol or pass a list of DTOs containing only necessary data (assets, employment status, needs).

### 3.3. WelfareService State Leak (Medium)
- **Location:** `modules/government/welfare/service.py`
- **Method:** `run_welfare_check`
- **Issue:** Directly modifies `Government`'s history buffer:
  ```python
  self.government.gdp_history.append(current_gdp)
  ```
- **Violation:** Component modifying Owner's state directly.
- **Remediation:** `Government` should update its own history based on data returned by the service, or provide a dedicated method `update_history(gdp)`.

---

## 4. Sequence & Logic Anomalies

### 4.1. Deprecated Method Usage
- **Location:** `simulation/systems/transaction_manager.py`
- **Issue:** Calls `government.collect_tax(...)`.
- **Note:** `Government.collect_tax` raises a DeprecationWarning advising to use `settlement.settle_atomic`.
- **Recommendation:** Refactor `TransactionManager` to use `ISettlementSystem` directly for tax transfers.

---

## 5. Verdict
**Status:** **WARNING**
While no blocking God Classes exist, the identified abstraction leaks in `FinanceDepartment` and `WelfareService` undermine the architecture's modularity. The `Phases` file is also becoming a monolith.

**Action Items:**
1. Refactor `FinanceDepartment` to remove direct access to `_econ_state`.
2. Refactor `WelfareService` to use protocols or DTOs.
3. Plan decomposition of `simulation/orchestration/phases.py`.