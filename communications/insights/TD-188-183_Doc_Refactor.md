# Documentation Refactor & Cleanup Insight Report (TD-188-183)

**Mission Key:** TD-188-183
**Author:** Technical Writer (Agent Jules)
**Date:** 2026-02-02

## 1. Discrepancy Analysis (TD-188: PROJECT_STATUS.md)

### A. Incorrect Implementation Path for "Animal Spirits"
- **Current Documentation:** `PROJECT_STATUS.md` lists "Animal Spirits" as implemented in `modules/system/execution/public_manager.py`.
- **Code Reality:**
  - `modules/system/execution/public_manager.py` implements the `PublicManager` class, responsible for **Asset Recovery and Liquidation** (Receiver role).
  - "Animal Spirits" (entrepreneurship and firm creation) is implemented in `simulation/systems/firm_management.py` within the `FirmSystem` class (specifically the `check_entrepreneurship` method).
- **Resolution:** Update the path to `simulation/systems/firm_management.py`.

### B. Configuration Path Clarity
- **Current Documentation:** `initial_needs` externalized to `economy_params.yaml`.
- **Code Reality:**
  - The actual file path is `config/economy_params.yaml`.
  - The configuration key is `NEWBORN_INITIAL_NEEDS`.
- **Resolution:** While the statement is conceptually correct, adding the `config/` prefix and clarifying the key name (`NEWBORN_INITIAL_NEEDS`) improves accuracy.

### C. Other Path Verifications
- `modules/finance/system.py`: Valid. Implements `FinanceSystem`.
- `simulation/orchestration/tick_orchestrator.py`: Valid. Implements `TickOrchestrator`.
- `scripts/verify_purity.py`: Valid. exists.

## 2. Architectural Documentation (TD-183: Liquidation Protocols)

### A. Liquidation Waterfall Protocol (TD-187)
- **Source:** `simulation/systems/liquidation_manager.py`
- **Protocol:**
  1. **Tier 1 (Employee Entitlements):** Unpaid wages (capped at 3 months) and Severance Pay (capped at 3 years tenure).
  2. **Tier 2 (Secured Creditors):** Bank Loans.
  3. **Tier 3 (Unsecured Priority):** Corporate Taxes.
  4. **Tier 4 (General Unsecured):** Residual unsecured debt (placeholder).
  5. **Tier 5 (Equity):** Shareholders (Households/Government).
- **Implementation:** `LiquidationManager.execute_waterfall` iterates through tiers, paying pro-rata if cash is insufficient for a tier.

### B. Fast-Fail Liquidation (Phase 4.5)
- **Source:** `simulation/orchestration/tick_orchestrator.py` and `simulation/orchestration/phases_recovery.py`
- **Concept:** `Phase_SystemicLiquidation` (Phase 4.5) runs immediately after `Phase_Bankruptcy` (Phase 4) and *before* `Phase_Matching`.
- **Purpose:** Ensures insolvent agents are liquidated and removed from market participation within the same tick they fail, preventing "Zombie Agents" from entering valid transactions or distorting price discovery.

## 3. Action Plan
1. Update `design/1_governance/project_status.md` with correct paths.
2. Update `design/1_governance/platform_architecture.md` with new Liquidation Protocol section.
3. Verify hyperlinks.
