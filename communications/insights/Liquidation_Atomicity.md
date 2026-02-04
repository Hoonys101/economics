# Insight: Liquidation Atomicity (WO-212)

## Overview
This mission unifies the "Firm write-offs" and "Manager sell-offs" into an atomic sequence within `LiquidationManager`. This prevents monetary leaks where assets could be destroyed without compensation or compensation received without asset destruction, ensuring accounting integrity.

## Changes
- **Atomic Sequence**: `LiquidationManager.initiate_liquidation` now orchestrates the entire process:
  1. **Sell-offs**: Handlers (e.g., `InventoryLiquidationHandler`) sell assets to `PublicManager`.
  2. **Write-offs**: `Firm.liquidate_assets()` is called to write off remaining assets (Inventory, Capital Stock, Automation) and finalize bankruptcy state.
- **Redundancy Removal**: Removed manual asset clearing from `AgentLifecycleManager` to prevent race conditions and duplicate logic.

## Technical Debt & Observations
- **`Firm.liquidate_assets` Scope**: Currently, this method handles inventory, capital stock, and automation. If future assets are added, they must be included here or in a handler.
- **Handler vs. Write-off Overlap**: `InventoryLiquidationHandler` clears inventory upon successful sale. `Firm.liquidate_assets` clears inventory unconditionally. This redundancy is safe (clearing empty dict) and ensures no assets leak if the handler fails or skips.
- **Dependency on `PublicManager`**: The liquidation process heavily relies on `PublicManager` having funds to buy assets. If `PublicManager` is insolvent, assets are written off (destroyed) via `Firm.liquidate_assets`, which is the correct fallback behavior (loss realized).
