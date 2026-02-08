# Structural Audit Report [STRUCTURAL-002]

**Date:** 2025-05-21
**Auditor:** Jules (AI)
**Task ID:** STRUCTURAL-002
**Scope:** Structural integrity, God Class detection, Abstraction Leaks in Decision Engines.

---

## 1. Executive Summary
This audit scanned the codebase for structural issues defined in the audit protocol. No critical "God Classes" (> 800 lines) were found, maintaining the structural integrity of the main components. However, three files are approaching the limit (Near Misses).

A significant number of abstraction leaks were identified, particularly in `HREngine` and `FinanceEngine`, where raw agent objects (`agent`, `government`, `household`) are passed into service methods. This violates the Purity Gates principle and increases coupling.

---

## 2. Saturation Report (God Class Candidates)
No file currently exceeds 800 lines. The following are near saturation (> 600 lines) and require monitoring:

| File | Lines | Risk Level | Recommendation |
|------|-------|------------|----------------|
| `simulation/firms.py` | 730 | High | **Firm** class is growing. Consider extracting more logic to Engines (e.g., `ProductionEngine`, `SalesEngine`). |
| `simulation/agents/government.py` | 665 | Medium | **Government** agent. Monitor growth. Consider extracting policy logic to `PolicyManagers`. |
| `simulation/systems/settlement_system.py` | 653 | Medium | **SettlementSystem**. Monitor. If it grows, split into sub-handlers. |

---

## 3. Abstraction Leak Audit (Dependency Hell)

### 3.1. HREngine Leaks (Critical)
- **Location:** `simulation/components/engines/hr_engine.py`
- **Method:** `fire_employee(..., agent: Any, ...)`
- **Issue:** The `agent` (Firm) object is passed directly, likely to check wallet balance.
- **Violation:** Purity Gate. The Engine should operate on DTOs or Interfaces.
- **Remediation:** Pass `wallet: IWallet` explicitly or use a `FirmDTO` containing financial state.
- **Method:** `process_payroll(..., government: Optional[Any], ...)`
- **Issue:** Raw `Government` object passed for tax calculation.
- **Remediation:** Pass a `TaxService` or `GovernmentDTO` containing tax rates.

### 3.2. FinanceEngine Leaks (Critical)
- **Location:** `simulation/components/engines/finance_engine.py`
- **Methods:** `generate_financial_transactions`, `invest_in_automation`, `invest_in_rd`, `invest_in_capex`, `pay_ad_hoc_tax`.
- **Issue:** Heavy reliance on raw `agent` and `government` objects.
- **Violation:** Strong coupling between Finance Engine and Agent implementation.
- **Remediation:** Refactor to accept `FinanceStateDTO`, `MarketContextDTO`, and specific `TaxContextDTO`.

### 3.3. SalesEngine Leaks (Medium)
- **Location:** `simulation/components/engines/sales_engine.py`
- **Method:** `generate_marketing_transaction`
- **Issue:** Raw `government` object passed.
- **Remediation:** Pass tax/fee context instead of the full agent.

### 3.4. Decision Engine Leaks (Medium)
- **Location:** `simulation/decisions/*`
- **Issue:** Functions like `propose_actions`, `place_buy_orders` often take `agent` or `household` as arguments.
- **Note:** While some of these might be typed as DTOs in some places, the variable names suggest raw object usage in others.
- **Remediation:** Ensure all decision engines strictly use `AgentStateDTO` (e.g., `HouseholdStateDTO`, `FirmStateDTO`) and never the raw agent class.

---

## 4. Verdict
**Status:** **WARNING**
The absence of God Classes is positive, but the persistent abstraction leaks in the Core Engines (`HR`, `Finance`) are technical debt that hinders testing and modularity.

**Action Items:**
1.  **Refactor `HREngine.fire_employee`**: Change signature to accept `wallet` and `settlement_system` only, or a `FiringContextDTO`.
2.  **Refactor `HREngine.process_payroll`**: Abstract `government` into a `TaxProvider` interface.
3.  **Refactor `FinanceEngine`**: Remove direct dependencies on `agent` and `government`.