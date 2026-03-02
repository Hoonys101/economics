# [S3-1] Scenario Diagnosis Fixtures Fix

## [Architectural Insights]
The architectural review of `tests/integration/scenarios/diagnosis/conftest.py` identified a significant technical debt: the `mock_config_module` fixture was creating a "Duct-Tape" mock by copying the entire global `config` module, leaking global state into the isolated diagnosis scenarios. Furthermore, factory functions (`create_household`, `create_firm`) in `tests/utils/factories.py` assumed global contexts and dependencies.

To resolve this and align with the "Clean Room" isolation specification:
1.  **Duct-Tape Mocking Mitigated:** The `mock_config_module` fixture in `conftest.py` was removed and replaced with a `mock_config_registry` fixture that correctly yields a pure `MagicMock(spec=IConfigurationRegistry)`.
2.  **Explicit Context Injection:** The factory functions in `tests/utils/factories.py` were updated to accept explicit `registry` and `config_registry` parameters with safe `None` defaults to ensure backward compatibility with older legacy tests while allowing new tests to break free from the global dependencies.
3.  **Fixture Isolation:** The agent-creation fixtures `simple_household` and `simple_firm` in `conftest.py` were updated to inject these new isolated context registries directly. A new teardown fixture `clean_room_teardown` was added as a safety net against hidden global caching leaks.
4.  **Test Modification:** `test_indicator_aggregation` was updated to accept the new `mock_config_registry` fixture instead of the legacy `mock_config_module` fixture.

## [Regression Analysis]
The test `test_indicator_aggregation` in `test_indicator_pipeline.py` originally expected the `mock_config_module` fixture. When `mock_config_module` was removed, the test failed during setup due to `fixture 'mock_config_module' not found`. This was resolved by updating the fixture injection in `test_indicator_aggregation` to use the newly provided `mock_config_registry`.

A pre-existing failure was detected in `tests/system/test_connectivity_enforcement.py::test_default_transfer_handler_m2_visibility` during full suite testing. This failure is entirely independent of the test fixture isolation performed in this mission and, per system directives, is explicitly ignored in this mission to maintain isolation of the bug fix to a separate designated mission (`wo-test-fix`).

## [Test Evidence]
```
tests/integration/scenarios/diagnosis/test_agent_decision.py::test_household_makes_decision PASSED [ 16%]
tests/integration/scenarios/diagnosis/test_agent_decision.py::test_firm_makes_decision
-------------------------------- live log setup --------------------------------
INFO     simulation.factories.firm_factory:firm_factory.py:82 FirmFactory: Registered bank account for Firm 101 at Bank 2
INFO     simulation.systems.bootstrapper:bootstrapper.py:134 BOOTSTRAPPER | Injected 10000000 capital to Firm 101 via Settlement.
PASSED                                                                   [ 33%]
tests/integration/scenarios/diagnosis/test_api_contract.py::test_api_contract_placeholder PASSED [ 50%]
tests/integration/scenarios/diagnosis/test_dashboard_contract.py::test_dashboard_snapshot_structure
-------------------------------- live log call ---------------------------------
ERROR    simulation.orchestration.persistence_bridge:persistence_bridge.py:54 ❌ [Persistence] Failed to save snapshot: asdict() should be called on dataclass instances
PASSED                                                                   [ 66%]
tests/integration/scenarios/diagnosis/test_indicator_pipeline.py::test_indicator_aggregation PASSED [ 83%]
tests/integration/scenarios/diagnosis/test_market_mechanics.py::test_order_book_matching
-------------------------------- live log setup --------------------------------
INFO     Market_basic_food:order_book_market.py:113 OrderBookMarket basic_food initialized.
-------------------------------- live log call ---------------------------------
INFO     Market_basic_food:order_book_market.py:274 Starting order matching for items: ['basic_food']
PASSED                                                                   [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
========================= 6 passed, 1 warning in 0.21s =========================
```