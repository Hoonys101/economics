# Mission Update: TD-005 Halo Effect Liquidation

## 1. Phenomenon
The legacy `is_visionary` flag provided a hardcoded, unfair advantage to certain firms (doubling bankruptcy threshold and immediate tech adoption), violating market fairness principles. This was a technical debt (TD-005) that needed liquidation.

## 2. Cause
The `is_visionary` flag was likely an early simulation shortcut to ensure some firms survived or led innovation without full simulation mechanics. It created a "Halo Effect" that was not emergent but imposed.

## 3. Solution
We successfully liquidated TD-005 by:
1.  **Removing `is_visionary`**: Completely removed the flag from `Firm`, `ServiceFirm`, `FirmSystem`, `FirmTechInfoDTO`, and `TechnologyManager`.
2.  **Implementing Brand Resilience**: Replaced the hardcoded bankruptcy buffer with an emergent `Brand Resilience` mechanic.
    *   **Logic**: `FinanceDepartment` now calculates `resilience_ticks` based on `BrandManager.awareness` and a configurable `BRAND_RESILIENCE_FACTOR` (default 0.05).
    *   **Effect**: High brand awareness grants firms extra "ticks" of consecutive losses before bankruptcy, simulating market trust and customer loyalty providing a safety net.
3.  **Updating Tech Adoption**: Removed the "immediate adoption by visionaries" logic. All firms now follow the same probabilistic adoption rules based on R&D investment and sector, ensuring a level playing field.

## 4. Lesson Learned
*   **Emergent vs. Imposed**: Replacing hardcoded traits with emergent systems (like Brand Resilience) creates a more robust and realistic simulation. It allows "Visionary-like" behavior to be earned (via Brand Investment) rather than assigned.
*   **Configuration Alignment**: We ensured `FIRM_CLOSURE_TURNS_THRESHOLD` and `BANKRUPTCY_CONSECUTIVE_LOSS_THRESHOLD` are aligned and the check is centralized in `FinanceDepartment`, exposed via `is_bankrupt` flag, which `AgentLifecycleManager` now respects.
*   **Verification Rigor**: We verified that critical flags like `is_bankrupt` are properly initialized in `Firm` constructor to prevent regression, even if the logic moving to a component suggested potential risk.

## 5. Verification
*   Unit tests confirmed that firms with 0 brand awareness fail exactly at the threshold, while firms with high awareness survive longer proportional to their awareness.
*   Tech manager tests confirmed that tech unlocks work based on cost thresholds without visionary shortcuts.
*   Verification script `scripts/verify_firm_init.py` confirmed `Firm.is_bankrupt` is correctly initialized.
