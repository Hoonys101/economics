# Mission Insight Report: TD-187 Liquidation Logic Refactor

## Overview
Refactored `LiquidationManager` to extract hardcoded inventory liquidation logic into `InventoryLiquidationHandler`. This aligns with the SRP and allows for future extension of liquidation logic for other asset types (e.g., Capital Stock, Financial Assets).

## Technical Debt & Observations

### 1. Conflicting Liquidation Logic in `Firm`
During exploration, I found `Firm.liquidate_assets` in `simulation/firms.py`:
```python
    def liquidate_assets(self, current_tick: int = -1) -> float:
        """
        Liquidate assets.
        CRITICAL FIX (WO-018): Inventory and Capital Stock are written off to zero
        instead of being converted to cash, to prevent money creation from thin air.
        Only existing cash (assets) is returned.
        """
        # 1. Write off Inventory
        self.inventory.clear()
        # ...
```
This method essentially destroys assets, whereas `LiquidationManager` attempts to sell them to the System Treasury (`PublicManager`). There is ambiguity about when each is used. If `LiquidationManager` runs, it sells inventory. If `Firm.liquidate_assets` is called independently (e.g., in some other bankruptcy flow), assets are destroyed. We should unify this behavior.

### 2. Handler Injection
Currently, `InventoryLiquidationHandler` is instantiated directly inside `LiquidationManager.__init__`.
```python
        if self.public_manager:
            self.handlers.append(InventoryLiquidationHandler(self.settlement_system, self.public_manager))
```
While this works for now, it creates a coupling. In the future, we might want to inject a list of handlers or a `LiquidationHandlerFactory` to allow for more flexible configuration (e.g., enabling/disabling specific asset liquidations via config).

### 3. Read-Only Dict Mocking in Tests
Encountered an issue where `dict.clear` cannot be mocked directly because it is read-only. Solved by verifying the state of the dictionary (empty vs non-empty) rather than asserting the `clear` method was called.

## Outcome
- Created `simulation/systems/liquidation_handlers.py`.
- Refactored `LiquidationManager` to iterate over handlers.
- Added comprehensive unit tests for the new handler and updated manager tests.
