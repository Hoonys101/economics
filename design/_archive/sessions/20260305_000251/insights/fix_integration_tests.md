# Integration Scenario Audit & Fix Report

## [Architectural Insights]
- **Mock Pollution (GC Leaks)**: Discovered that `MagicMock` instances injected deeply into simulated objects (e.g., `_econ_state` and `_social_state` in `Household`) bypass domain data boundaries, creating heavy cyclic references that leak memory over multiple iterations. Fixed this by introducing lightweight `DummyHousehold` structures using simple properties (`DummyEconState`, `DummyBioState`, `DummySocialState`) in `tests/integration/scenarios/test_stress_scenarios.py`, reducing reliance on `MagicMock`.
- **Global GC Cleanup**: Removed manual, inline garbage collection loops (`gc_collect_harder()`) from `test_scenario_runner.py` and converted it to an `autouse=True` fixture in the root `conftest.py`. This standardizes Mock object reset logic across the entire integration suite and prevents memory pollution between parameterized tests. The test setup dependency injections must eventually be fully refactored, but this acts as an immediate reliable safeguard.
- **E2E Test Fragility**: The Playwright frontend test `test_e2e_playwright.py` utilized hardcoded `time.sleep(5)` for delays and left daemon threads running after completion. Replaced threading with `multiprocessing.Process` to enable definitive explicit `terminate()` upon teardown, and transitioned hard sleeps to Playwright's native `page.wait_for_selector("canvas", timeout=10000)`, making it faster and significantly more resilient.
- **Mock Module Fix**: Fastapi was originally mocked with a `return_value=None`, causing a collection crash `AttributeError: 'NoneType' object has no attribute 'get'` in router initialization across tests. Updated `tests/conftest.py`'s `ShallowModuleMock` to instantiate `MagicMock()` on getattr calls, allowing tests to bypass missing imports properly.

## [Regression Analysis]
- **Verify Leviathan**: The test suite `verify_leviathan.py` skipped assertions due to complex `MagicMock` failures involving `ConfigWrapper`. When patching the configurations to include proper types (e.g., `TICKS_PER_YEAR = 100`, `ANNUAL_WEALTH_TAX_RATE = 0.0`), the system successfully resolved TypeErrors. We verified that `SmartLeviathanPolicy` strictly applies its AI-driven policy actions directly to `corporate_tax_rate` and the test (`test_ai_policy_execution`) was updated to enforce strict `assert government.corporate_tax_rate < 0.2` and ensure `decide_policy` is correctly called, bringing back robust test validation.
- **Test Runner Timeout Avoidance**: Removed the `xfail` marker originally associated with `TD-ARCH-MOCK-POLLUTION` in `test_scenario_runner.py` now that mock leakage is addressed.

## [Test Evidence]

```
=========================== short test summary info ============================
PASSED tests/integration/scenarios/test_e2e_playwright.py::test_frontend_flow
PASSED tests/integration/scenarios/test_stress_scenarios.py::TestPhase28StressScenarios::test_deflation_asset_shock
PASSED tests/integration/scenarios/test_stress_scenarios.py::TestPhase28StressScenarios::test_consumption_pessimism
PASSED tests/integration/scenarios/test_stress_scenarios.py::TestPhase28StressScenarios::test_supply_shock
PASSED tests/integration/scenarios/test_stress_scenarios.py::TestPhase28StressScenarios::test_panic_selling_order_generation
PASSED tests/integration/scenarios/test_stress_scenarios.py::TestPhase28StressScenarios::test_hoarding_amplification
PASSED tests/integration/scenarios/test_stress_scenarios.py::TestPhase28StressScenarios::test_debt_repayment_priority
PASSED tests/integration/scenarios/verify_leviathan.py::test_opinion_aggregation
PASSED tests/integration/scenarios/verify_leviathan.py::test_opinion_lag
PASSED tests/integration/scenarios/verify_leviathan.py::test_election_flip
PASSED tests/integration/scenarios/verify_leviathan.py::test_ai_policy_execution
================================================================================
```
