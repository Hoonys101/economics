# Insight Report: Logic Restoration & Serialization Fixes
**Mission Key**: `PH15-LOGIC-CORE`
**Date**: 2026-02-12
**Author**: Jules

## 1. Phenomenon
Two critical regressions were identified:
1.  **Serialization Data Loss**: The `AgentStateDTO` structure only supported a single `inventory` dictionary. However, agents like `Firm` had evolved to use multiple inventory slots (e.g., `MAIN` for products, `INPUT` for raw materials). This resulted in the loss of input inventory and item quality data during save/load cycles.
2.  **Missing QE Logic**: The `FinanceSystem.issue_treasury_bonds` method hardcoded the Commercial Bank as the buyer for all government bonds. The Quantitative Easing (QE) logic, which should shift the buyer to the Central Bank when the Debt-to-GDP ratio is high, was missing.

## 2. Cause
1.  **DTO Lag**: The internal agent architecture evolved (`InventorySlot` refactoring) faster than the data transfer objects (`AgentStateDTO`) used for persistence. The DTO remained coupled to the legacy single-inventory model.
2.  **Refactoring Oversite**: During the decomposition of `FinanceSystem` into stateless engines, the conditional logic for QE (checking Debt-to-GDP) was inadvertently dropped or simplified to a basic market mechanism.

## 3. Resolution
1.  **Multi-Slot Serialization**:
    -   Updated `AgentStateDTO` to include an `inventories` field: `Dict[str, InventorySlotDTO]`.
    -   Deprecated the old `inventory` field but kept it for backward compatibility in `load_state`.
    -   Updated `Firm` and `Household` orchestrators to map their internal storage (`_inventory`, `_input_inventory`) to these slots during serialization and deserialization.
2.  **QE Restoration**:
    -   Restored logic in `FinanceSystem.issue_treasury_bonds` to calculate `Debt-to-GDP` ratio using `Government.total_debt` and `Government.sensory_data.current_gdp`.
    -   Implemented a dynamic buyer selection: if the ratio exceeds the threshold (default 1.5), the `CentralBank` buys the bonds; otherwise, the `Bank` does.

## 4. Lessons Learned
-   **DTO Evolution**: DTOs used for persistence must be treated as versioned contracts. When internal state structures change (e.g., adding inventory slots), the DTO must be updated simultaneously to prevent silent data loss.
-   **Dependency Checking**: The `FinanceSystem` required access to `Government.total_debt`. We must ensure that mocked dependencies in tests accurately reflect the properties of the real agents to avoid false positives during unit testing.
-   **Legacy Fallbacks**: Implementing legacy fallbacks (checking `state.inventory` if `state.inventories` is empty) is essential for maintaining compatibility with existing save files or tests that use older DTO structures.
