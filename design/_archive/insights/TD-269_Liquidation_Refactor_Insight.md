# Technical Insight: LiquidationManager Refactoring (TD-269)

## 1. Problem Phenomenon
The `LiquidationManager` was tightly coupled to the internal implementation of the `Firm` agent, specifically relying on the `firm.finance` attribute. This caused failures in verification scripts like `audit_zero_sum.py` when they encountered `Firm` instances that had been refactored to use a composition-based architecture (where `finance` was replaced by `finance_state` and `finance_engine`).

**Symptoms:**
- `AttributeError: 'Firm' object has no attribute 'finance'` in `LiquidationManager.initiate_liquidation`.
- `audit_zero_sum.py` failing to complete the liquidation escheatment check.
- `TaxService` and `HRService` attempting to access non-existent `firm.finance` and `firm.hr` attributes.

## 2. Root Cause Analysis
- **Violations of Law of Demeter:** `LiquidationManager` was accessing deep internal state of `Firm` (`firm.finance.total_debt`, `firm.decision_engine.loan_market.bank`).
- **Legacy Dependencies:** Auxiliary services (`HRService`, `TaxService`) were not updated to reflect the architectural shift from "Components" (`firm.hr`) to "State+Engine" (`firm.hr_state`, `firm.hr_engine`).
- **Missing Abstraction:** There was no formal contract defining how an entity should be liquidated, leading to ad-hoc attribute checks (`hasattr(firm, 'finance')`).

## 3. Solution Implementation Details
To resolve this, we introduced a protocol-based abstraction layer:

1.  **`ILiquidatable` Protocol**: Defined in `modules/finance/api.py`. This protocol enforces a contract for any agent that can be liquidated, requiring methods to:
    -   `liquidate_assets(current_tick)`: Write off non-cash assets.
    -   `get_all_claims(ctx)`: return a list of standardized `Claim` objects (Tier 1-4).
    -   `get_equity_stakes(ctx)`: Return a list of `EquityStake` objects (Tier 5).

2.  **`LiquidationContext`**: A DTO to pass necessary services (`HRService`, `TaxService`, `ShareholderRegistry`) to the agent during liquidation, avoiding permanent coupling.

3.  **Refactored `Firm`**: The `Firm` agent now implements `ILiquidatable`. It encapsulates the logic to gather claims from its internal state (`hr_state`, `finance_state`) and external services, exposing only the standardized data to `LiquidationManager`.

4.  **Refactored `LiquidationManager`**:
    -   Removed all `hasattr` checks and direct attribute access.
    -   Now operates exclusively on the `ILiquidatable` interface.
    -   Uses `ShareholderRegistry` injected via constructor to handle equity distribution, removing global state traversal.

5.  **Service Fixes**: Updated `HRService` and `TaxService` to access `hr_state` and `finance_state` respectively, fixing the legacy crashes.

## 4. Lessons Learned & Technical Debt Identified
-   **Protocol vs. Implementation**: Defining clear protocols (`ILiquidatable`) is critical for decoupling systems. The previous tight coupling made refactoring `Firm` incredibly risky.
-   **Dependency Injection**: Injecting `ShareholderRegistry` into `LiquidationManager` (and `AgentLifecycleManager`) clarified ownership and removed hidden dependencies on the global `SimulationState`.
-   **Legacy Debt**: The `InventoryLiquidationHandler` still relies on run-time checks (`isinstance(agent, IInventoryHandler)`) and `getattr(agent, 'config')`. A future refactor should standardize `IConfigurable` or similar to remove `getattr`.
-   **PublicManager Insolvency**: During verification, it was noted that `PublicManager` had 0 funds and failed to pay for liquidated inventory. This indicates a need to bootstrap `PublicManager` with funds or allow it to mint money for asset recovery (System Debt).
