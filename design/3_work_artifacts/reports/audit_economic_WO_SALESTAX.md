# Economic Integrity Audit: Sales Tax & Inheritance [WO-SALESTAX]

**Auditor**: Jules
**Date**: 2024-05-23
**Focus**: Sales Tax Atomicity & Inheritance Leaks

## 1. Executive Summary
This audit identified two critical economic integrity issues:
1.  **Sales Tax Non-Atomicity in Planning**: The `CommerceSystem` checks for affordability based on raw goods price, ignoring the applicable sales tax. This leads to transaction failures at execution time when the `GoodsTransactionHandler` correctly attempts to deduct the full amount (Price + Tax).
2.  **Inheritance Leaks & Encapsulation Violation**: The `InheritanceManager` bypasses the `TransactionProcessor` and `SettlementSystem` abstractions during asset liquidation. It manually executes transfers and directly mutates agent state (Portfolio, Property Ownership), creating a risk of state desynchronization and complicating future refactors.

## 2. Detailed Findings

### 2.1 Sales Tax Atomicity (CommerceSystem)
-   **Location**: `simulation/systems/commerce_system.py`, method `plan_consumption_and_leisure`.
-   **Issue**:
    ```python
    cost = b_amt * food_price
    if household._econ_state.assets >= cost:
        # ... generate transaction ...
    ```
-   **Impact**: Households with `Assets = Price` will attempt to buy, but fail during `GoodsTransactionHandler` execution because `Assets < Price + Tax`. This causes unnecessary processing overhead and potential starvation/dissatisfaction artifacts in the simulation.
-   **Remediation**: Update the affordability check to include `SALES_TAX_RATE`.

### 2.2 Inheritance Leaks (InheritanceManager)
-   **Location**: `simulation/systems/inheritance_manager.py`, method `process_death`.
-   **Issue**:
    -   **Manual Transfer**: Calls `settlement_system.transfer(...)` directly instead of using a standard Transaction type.
    -   **Direct Mutation**:
        ```python
        del deceased._econ_state.portfolio.holdings[firm_id]
        unit.owner_id = government.id
        deceased.owned_properties.remove(unit.id)
        ```
    -   **Architecture Violation**: Bypasses the `TransactionProcessor` dispatcher pattern which is designed to centralize side-effects (like ownership updates) in Handlers (`MonetaryTransactionHandler`, `AssetTransferHandler`).
-   **Impact**:
    -   High coupling between `InheritanceManager` and Agent internal structures.
    -   Risk of "Ghost Assets" if the transfer succeeds but the manual deletion fails (or vice versa), though current code executes them sequentially.
    -   Duplication of asset transfer logic which already exists in `MonetaryTransactionHandler`.
-   **Remediation**: Refactor `process_death` to construct `Transaction` objects with type `asset_liquidation` and execute them via `simulation.transaction_processor.execute()`. This leverages the existing `MonetaryTransactionHandler` which safely handles the side-effects.

## 3. Action Plan
1.  **Refactor `CommerceSystem`**: Inject tax rate into planning logic.
2.  **Refactor `InheritanceManager`**: Delegate liquidation execution to `TransactionProcessor`.
