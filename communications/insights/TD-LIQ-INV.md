# Technical Insight Report: TD-LIQ-INV Protocol Purity

## 1. Problem Phenomenon
The `InventoryLiquidationHandler` relied on dynamic `getattr` and `hasattr` calls to access internal configuration of agents, specifically `fire_sale_discount` and `goods`. This created an implicit coupling between the liquidation system and the concrete implementation of `Firm` agents. Changes to `FirmConfigDTO` structure could silently break liquidation logic without type checker warnings.

Symptoms:
-   `InventoryLiquidationHandler` contained code like `getattr(agent.config, "fire_sale_discount", 0.2)`.
-   Integration tests were fragile and failed when internal structures changed.
-   `Firm` class implementation of `get_liquidation_config` also used defensive `hasattr` checks, masking potential configuration errors.

## 2. Root Cause Analysis
The root cause was a violation of the "Protocol Purity" architectural guardrail. The liquidation system was accessing internal state directly instead of using a defined interface contract.
-   The system lacked a strict contract (`IConfigurable`) for retrieving liquidation parameters.
-   Unit and Integration tests were mocking `Firm` objects loosely, without adhering to a strict protocol spec, leading to tests that passed even when the underlying contract was violated or incomplete.
-   Integration tests for `LiquidationManager` were particularly brittle, mocking `Firm` but not its protocol methods (`get_all_claims`, `get_all_items`, `get_liquidation_config`), causing the manager to receive empty data and tests to fail silently or with confusing assertions.

## 3. Solution Implementation Details
The solution involved refactoring to enforce Protocol Purity:

1.  **Protocol Definition**: `IConfigurable` protocol and `LiquidationConfigDTO` were utilized (already present in `modules/simulation/api.py`).
2.  **Firm Implementation**:
    -   Refactored `Firm.get_liquidation_config` to remove `hasattr` safety nets and access `self.config.fire_sale_discount` directly. This ensures that if the config is missing the attribute, it raises an error early rather than using a default silently.
    -   Ensured `Firm` explicitly implements `IConfigurable`.
3.  **Handler Refactor**: Verified `InventoryLiquidationHandler` uses `agent.get_liquidation_config()` and `isinstance(agent, IConfigurable)` check.
4.  **Test Refactoring**:
    -   Updated `tests/integration/test_liquidation_waterfall.py` to correctly mock the protocol methods.
    -   Mocked `get_liquidation_config`, `get_all_items`, and `get_all_claims` using `side_effect` to simulate real logic or return consistent test data.
    -   Fixed `LiquidationManager` instantiation in tests to include the required `shareholder_registry` mock.
    -   Ensured `assert_any_call` matches the actual implementation strings ("Agent" vs "Firm").

## 4. Lessons Learned & Technical Debt
-   **Test Fragility**: Integration tests that mock too much internal structure (like `firm.hr.employees` without mocking the `get_all_claims` method that uses it) are highly fragile. When the system under test (`LiquidationManager`) delegates logic back to the mocked object (`Firm`), the mock must faithfully reproduce that logic or the test becomes invalid.
-   **Mocking Protocols**: When mocking objects that implement protocols, it is crucial to mock the protocol methods (`get_X`) explicitly. Simply setting attributes (`firm.inventory`) is insufficient if the consumer uses the accessor method (`firm.get_all_items()`).
-   **Legacy Aliases**: The `Firm` class and tests still use some legacy aliases (e.g., `firm.finance` aliasing `firm.finance_state`). These should be cleaned up in a future "God Class" refactor (TD-073) to strictly enforce the new State/Engine architecture.
-   **Dependency Injection**: The `LiquidationManager` constructor signature change (adding `shareholder_registry`) was not reflected in the integration test, causing silent failures (handler not initialized). Tests must use strict typing or be updated when signatures change.
