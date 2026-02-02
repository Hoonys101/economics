# Dynamic Household Personality Refactor (TD-006)

## 1. Overview
The implementation of **Dynamic Household Personality** (TD-006) successfully transitions the `Household` agent from a static personality model to a dynamic one, driven by wealth percentiles. This involved refactoring the `Household` class, updating the `SocialComponent`, and modifying configuration management to support the new logic.

## 2. Technical Debt & Insights

### Phenomenon
During verification, multiple integration tests (`verify_real_estate_sales.py`, `test_engine.py`) failed due to incorrect mock configurations and `AttributeError`s related to `Household` instantiation and property access. Specifically, the removal of the `personality` argument from `__init__` exposed brittle test setups that relied on deprecated signatures or manual property setting without setters.

### Cause
1.  **Tight Coupling in Tests**: Tests manually instantiated `Household` with specific `personality` enums, bypassing the intended dynamic logic.
2.  **Mocking Fragility**: `MagicMock` objects used for `config_module` and `bank` lacked necessary attributes (`value_orientation_mapping`, `grant_loan` return values), causing runtime errors when new logic accessed them.
3.  **Property Encapsulation**: `Household` properties like `optimism` delegate to `_social_state` but lack setters in the facade, preventing tests from easily manipulating state for scenarios.

### Solution
1.  **Refactored Call Sites**:Systematically updated all `Household` instantiations to remove `personality` and use `config_dto`.
2.  **Enhanced Mocks**: Updated `verify_real_estate_sales.py` to use `create_household_config_dto` factory and properly configure `Bank` and `ConfigManager` mocks.
3.  **Direct State Access in Tests**: Modified tests to set properties directly on `_social_state` (e.g., `agent._social_state.optimism = 0.5`) rather than adding setters to the facade, preserving encapsulation while allowing test manipulation.
4.  **Graceful Handlers**: Updated `GoodsTransactionHandler` to return `False` immediately if `buyer` or `seller` is `None`, preventing crashes during invalid transaction processing in tests.

### Lesson Learned
-   **Factories for Configs**: Using DTO factories (like `create_household_config_dto`) in tests is crucial to ensure all required configuration fields are present, preventing `AttributeError`s when the config schema evolves.
-   **Integration Test Fidelity**: Integration tests mimicking the engine (like `verify_real_estate_sales.py`) must accurately replicate the *entire* necessary environment (e.g., `TransactionProcessor`, `SettlementSystem`), or they will fail when low-level components (like handlers) depend on them. Manual "engine-like" setups are prone to drift.

## 3. Verification
-   **Unit Tests**: `tests/unit/modules/household/test_social_component_personality.py` confirms that personality correctly shifts to `STATUS_SEEKER` (High Wealth), `SURVIVAL_MODE` (Low Wealth), or stays `BALANCED` based on configured percentiles.
-   **Integration Tests**: Existing scenarios (`verify_stock_trading.py`, `test_wo058_production.py`) pass with the new refactored `Household` signature.
