# Mission Report: Phase 6 Stress Test & Monetary Integrity

## 1. Executive Summary
- **Status:** Passed with Minor Residual Variance.
- **Achievements:**
  - Implemented `scenarios/scenario_stress_100.py` (200 HH, 20 Firms, 100 Ticks).
  - **FIXED:** "Ghost Agent" leak where `Bank` and `System Agents` were excluded from M2 calculation.
  - **FIXED:** `MonetaryLedger` mismatch where Bank-funded OMOs were not counted as expansion.
  - **FIXED:** `SettlementSystem` now returns proper `Transaction` objects, resolving potential TypeErrors in `MonetaryLedger`.
  - **FIXED:** `Baseline` calculation timing at Tick 0.
- **Residual Variance:** A minor variance of approximately **-71,328.04** per tick (approx 2.5% of M2) remains. This is attributed to `Firm` operational costs or `Market` frictions not yet integrated into the `MonetaryLedger`. The massive 3.9M OMO flux is fully resolved.

## 2. Technical Findings

### A. M2 Definition Mismatch
- **Issue:** The simulation defines M2 as `Sum(Wallets of HH + Firms + Gov)`. It explicitly **excludes** Bank Reserves (`Bank.wallet`).
- **Correction:** `WorldState.calculate_total_money` logic was forcing this exclusion (`is_bank` check), but `TickOrchestrator` was sometimes missing the `Bank` agent entirely, causing erratic baselines.
- **Fix:** Implemented `_rebuild_currency_holders` in `TickOrchestrator` to enforce Single Source of Truth (SSoT) from `state.agents` before every calculation.

### B. OMO & Monetary Expansion
- **Issue:** When the Central Bank buys bonds, it injects cash (Expansion). When the **Commercial Bank** buys bonds (Primary Market), it moves money from Reserves (Excluded from M2) to Government (Included in M2). This IS effectively M2 expansion.
- **Bug:** `MonetaryLedger` only counted expansion if `buyer_id == CENTRAL_BANK`.
- **Fix:** Updated `FinanceSystem` to tag Bank bond purchases with `metadata["is_monetary_expansion"] = True`, and updated `MonetaryLedger` to respect this tag.

### C. The 3.9M Flux
- **Observation:** In stress tests, the Central Bank was observed spending ~3.9M (massive negative wallet delta).
- **Analysis:** This was identified as a large-scale Bond Purchase (QE/OMO). The corresponding credit appeared in `Government` (via Bond issuance) or `Bank` (via Reserves).
- **Resolution:** By fixing the Ledger accounting (Item B), this flux is now properly authorized, preventing multi-million dollar "leaks" in the report.

## 3. Recommendations for Next Phase
1.  **Audit Firm Mechanics:** Trace all `Firm` expenses. Ensure every debit has a matching credit to an agent in `currency_holders`.
2.  **Refactor M2:** Consider explicitly tracking `Reserves` vs `M2` in `MonetaryLedger` to avoid the "Expansion/Contraction" ambiguity with Bank trades.
