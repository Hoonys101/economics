# Report on Mock Drift Patterns and Test Suite Robustness

## Executive Summary
The test suite exhibits patterns of "Mock Drift" where manually constructed test doubles diverge from evolving production code's DTOs and interface contracts. This leads to fragile tests prone to breakage during architectural refactors. A partially implemented "Mock Factory" and "Golden Fixture" system exists, offering a path to more robust testing.

## Detailed Analysis

### 1. Mock Drift Patterns Identified

-   **AttributeError (Float vs. Dictionary Assets)**: Tests frequently initialized agent assets as simple floats (`agent.assets = 1000.0`), but production code refactored to use dictionary-based wallets (e.g., `agent.wallet.get_balance(currency)` or `agent.assets.get(currency)`).
    -   **Evidence**:
        *   `tests\unit\test_bank_decomposition.py:L26` (`self.agent.assets = {DEFAULT_CURRENCY: 1000.0}`) shows adaptation to dictionary, but many others still use float for direct `assets` property.
        *   `tests\unit\systems\test_settlement_system.py:L22` (`self._assets = float(assets)`) in `MockAgent` directly sets float assets, with a mock wallet on top.
        *   `tests\unit\systems\test_commerce_system_logging.py:L14-16` (`h1.assets = 10.0`, `h1._econ_state.assets = 10.0`) manually sets both flat and nested float assets.
-   **TypeError (Float not iterable for `last_tick_revenue`)**: An accumulator `last_tick_revenue` was initialized as a float but later accessed as a dictionary, leading to runtime errors.
    -   **Evidence**: `design_archive\insights\2026-02-11_Mock_Drift_Root_Cause_Analysis.md:L30-32` explicitly mentions this symptom and its fix (`self.last_tick_revenue = {DEFAULT_CURRENCY: 0.0}`). `tests\unit\modules\system\execution\test_public_manager.py:L99` demonstrates the correct dictionary initialization in its test.
-   **TypeError (Comparisons between `MagicMock` and `int`/`float`)**: When complex DTOs or nested objects were passed as `MagicMock` without proper structure, subsequent access to their attributes returned new `MagicMock` objects instead of expected primitive values, causing type-related comparison errors.
    -   **Evidence**:
        *   `tests\unit\test_ai_training_manager.py:L40-42` manually `del`s mocked attributes (`q_consumption`, `q_work`, `q_investment`) to avoid iteration errors, indicating the mock's structure did not align with expected attribute presence.
        *   `tests\unit\test_household_decision_engine_new.py:L48-132` features an extensive `mock_config` fixture that manually sets numerous config attributes. This is fragile to changes in config structure or DTOs.

### 2. Proposed Standardized Mocking Strategy

The project already has foundational elements for improved mocking. The strategy should focus on consistent adoption and maintenance:

1.  **Leverage and Expand `tests\unit\mocks\mock_factory.py`**:
    *   **Action**: All new agent-related mocks (e.g., Household, Firm, Government) should be created using methods from `MockFactory` (or similar dedicated factories).
    *   **Current Usage**: `tests\unit\factories.py` uses `MockFactory` to create DTOs, and `tests\unit\mocks\mock_factory.py` provides `create_mock_firm` and `create_mock_household`. This is excellent, but not universally applied.
    *   **Enhancement**: Ensure these factories take `spec` arguments where appropriate (`MagicMock(spec=Household)`) to enable strict type-checking during mock attribute access.
    *   **Benefit**: Centralizes mock creation, making them easier to update and ensuring they reflect the latest DTO/Protocol structure.

2.  **Full Adoption of Golden Fixtures**:
    *   **Action**: For complex, stateful agents (e.g., `Household`, `Firm`) that have many nested DTOs and evolve frequently, transition from `MockFactory` to serialization-based "Golden Fixtures." The `tests\conftest.py` has a robust mechanism for this.
    *   **Current Usage**: `conftest.py:L142-L177` outlines and supports golden fixtures (e.g., `golden_households`, `golden_firms`).
    *   **Enhancement**:
        *   **Automate Generation**: Integrate golden fixture generation (`scripts/fixture_harvester.py`) into the CI/CD pipeline or as a pre-commit hook to ensure they are always up-to-date with the latest simulation state schema.
        *   **Broaden Usage**: Encourage using `golden_households` and `golden_firms` fixtures in integration-level unit tests, especially where the full complexity of an agent's state is relevant.
    *   **Benefit**: Golden fixtures capture realistic, entire agent states, drastically reducing manual mock setup and ensuring tests operate on data structures consistent with live simulation data.

### 3. Ensuring Robustness After Architectural Refactors

-   **Interface-Driven Testing**: Adhere to the principle of testing through public interfaces rather than inspecting internal (`_econ_state`) or mocked (`MagicMock().some_attribute`) private attributes. This decouples tests from internal implementation details.
    -   **Evidence**: `design_archive\insights\2026-02-11_Mock_Drift_Root_Cause_Analysis.md:L18-20` recommends this by stating tests should prefer `agent.get_balance(currency)`.
-   **Explicit Configuration in Mocks**: When mocking configuration objects for tests, explicitly define all attributes that the System Under Test (SUT) might access. This reduces implicit reliance on `MagicMock`'s auto-creation of attributes.
    -   **Evidence**: The verbose `mock_config` fixtures in `tests\unit\test_household_decision_engine_new.py` and `tests\unit\systems\test_demographic_manager_newborn.py` illustrate this, though they should ideally be maintained centrally (e.g., in `mocks/mock_config.py`).
-   **Early Integration of Type Hints and DTOs**: Any significant architectural change involving data structures should first be reflected in DTOs and type hints. This provides static analysis benefits and guides mock/fixture updates.

## Conclusion
"Mock Drift" has been a notable source of test fragility. By consistently utilizing and expanding the existing `MockFactory` for simpler mocks, fully adopting and automating "Golden Fixtures" for complex agent states, and strictly adhering to interface-driven testing, the test suite can achieve significantly higher robustness against future architectural refactors.
