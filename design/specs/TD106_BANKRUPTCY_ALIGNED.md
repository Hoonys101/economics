# Spec: TD-106 Bankruptcy Ledger Connection

## 1. Objective

To ensure the zero-sum integrity of the simulation by connecting the `Firm.liquidate_assets()` process to the `SettlementSystem`. When a firm goes bankrupt, the value of its liquidated assets must be formally recorded as a loss in the central financial ledger, preventing "money leaks."

## 2. Logic Steps (Pseudo-code)

The change will be implemented entirely within `simulation/systems/ma_manager.py`.

### 2.1. `SettlementSystem` (Conceptual)

A new method must be added to the `SettlementSystem` interface.

```python
# In simulation/systems/settlement_system.py (or its interface)

class SettlementSystem:
    # ... existing methods ...

    def record_liquidation_loss(self, firm: "Firm", amount: float, tick: int):
        """
        Records the value destroyed during a firm's bankruptcy and liquidation.
        This ensures the value is accounted for in the simulation's total wealth.

        Args:
            firm: The firm that went bankrupt.
            amount: The value of assets liquidated (and thus destroyed).
            tick: The simulation tick when the event occurred.
        """
        # 1. Log the event to a dedicated transaction log (e.g., self.liquidation_log).
        # 2. Debit the simulation's total wealth tracker by 'amount'.
        # 3. Log a clear message: f"LIQUIDATION: Firm {firm.id} liquidated, destroying {amount} in value."
        pass
```

### 2.2. `MAManager._execute_bankruptcy`

The existing method will be modified to call the new `SettlementSystem` endpoint.

```python
# In simulation/systems/ma_manager.py

class MAManager:
    # ...

    def _execute_bankruptcy(self, firm: "Firm", tick: int):
        # 1. Liquidate assets. This call remains unchanged.
        recovered = firm.liquidate_assets()
        self.logger.info(f"BANKRUPTCY | Firm {firm.id} liquidated. Recovered Cash: {recovered:,.2f}.")

        # 2. [NEW] Record the asset destruction in the central ledger.
        # This is the core change to fix the money leak.
        if hasattr(self.simulation, 'settlement_system') and self.simulation.settlement_system:
            self.simulation.settlement_system.record_liquidation_loss(
                firm=firm,
                amount=recovered,
                tick=tick
            )
        else:
            # Fallback or error if the settlement system is missing
            self.logger.error(f"CRITICAL: SettlementSystem not found. Liquidation loss of {recovered} for Firm {firm.id} is NOT RECORDED.")

        # 3. Fire all employees. This logic remains unchanged.
        for emp in list(firm.hr.employees):
            emp.quit()

        # 4. Deactivate the firm. This logic remains unchanged.
        firm.is_active = False
```

## 3. Interface Specification (API)

- **`Firm.liquidate_assets()`**: No change. Signature and return value (`float`) remain the same.
- **`MAManager._execute_bankruptcy()`**: No change to signature. The modification is internal.
- **`SettlementSystem`**: Requires the addition of the new public method `record_liquidation_loss(firm, amount, tick)`.

There are no changes to DTOs.

## 4. Verification Plan

The existing test suite for `test_ma_manager.py` must be updated.

1.  **Test Case**: `test_execute_bankruptcy_records_loss_in_ledger`
    - **Setup**:
        - Create a `Firm` instance with a defined amount of assets.
        - Mock the `simulation` object on the `MAManager` instance.
        - The mocked `simulation` object must have a mocked `settlement_system` attribute.
        - The `firm.liquidate_assets()` method should be patched to return a predictable value (e.g., `1000.0`).
    - **Execution**:
        - Call `ma_manager._execute_bankruptcy(firm, current_tick)`.
    - **Assert**:
        - Assert that `firm.is_active` is `False`.
        - Assert that the mocked `settlement_system.record_liquidation_loss` was called **exactly once**.
        - Assert that it was called with the correct arguments: `firm=firm`, `amount=1000.0`, `tick=current_tick`.

## 5. 🚨 Risk & Impact Audit (Summary of TD-106)

- **Architectural Constraint**: The logic **must** reside in `MAManager._execute_bankruptcy` to maintain the existing architectural pattern where `MAManager` is the sole mediator for `SettlementSystem` interactions. `Firm` objects must not access the ledger directly.
- **Financial Integrity**: This change is critical to fix the "money leak" where asset value was destroyed without a corresponding entry in the global ledger, violating the zero-sum principle.
- **Test Impact**: Existing tests for bankruptcy will fail as they do not account for the new call to `SettlementSystem`. The test suite **must** be updated as described in the Verification Plan.
- **Scope**: The change is confined to `MAManager` and the `SettlementSystem` interface. The signature of `firm.liquidate_assets()` is unaffected.

---

##  JULES: Routine Reporting Mandate

- **Insight & Tech Debt Log**: Upon completion of this task, document any new insights, challenges, or identified technical debt. Create or update a report in the `communications/insights/` directory.
- **File Naming**: `YYYY-MM-DD_TD106_bankruptcy_ledger_findings.md`.
- **Content**: Note any difficulties in mocking the `SettlementSystem`, unexpected dependencies, or suggestions for improving the M&A / Bankruptcy process.
