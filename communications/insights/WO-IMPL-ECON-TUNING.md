# Insight Report: ECON-BEHAVIORAL-TUNING-SPEC

## 1. [Architectural Insights]
- **TD-ECON-ZOMBIE-FIRM**: The systemic failure of basic food firms due to negative profit loops was addressed by introducing the `FirmPricingStrategyDTO`. The `PricingEngine.calculate_price` logic was refactored to implement a hard floor constraint (`floor_price_pennies`) derived from a markup over the unit cost estimate. Furthermore, an emergency margin extension of 20% (`target_price *= 1.2`) kicks in when the firm's assets drop below the defined `buffer_capital_pennies`. This robustly solves the Zombie Firm trap without leaking state.
- **TD-WAVE3-TALENT-VEIL**: To prevent bloating monolithic agent structures or introducing cyclic dependencies, innate talent (`hidden_talent`) was introduced purely as an `Optional[float]` on `AgentStateData` within `simulation/dtos/api.py`. It is generated probabilistically (`random.uniform(0.0, 0.5)` offset from `base_xp`) during `Household` initialization in `simulation/core_agents.py` and stored as a dictionary per domain, ensuring the Agent core logic remains decoupled from the specific application usage while still fulfilling the veil pattern.
- **TD-WAVE3-MATCH-REWRITE**: The labor matching logic in `modules/labor/system.py` was refactored into a completely stateless operation (`execute_labor_matching`). The matching engine now accepts `JobMatchContextDTO`, which contains lists of `JobSeekerDTO` and `JobOfferDTO` rather than raw Agent instances. It returns a pure `LaborMatchingResultDTO` encompassing the `matched_pairs`, agreed wages, and unmatched entities. This adheres closely to Container/Component isolation, allowing the `LaborMarket.match_market` orchestrator to apply the structural changes derived from the stateless results without coupling the two logic phases.

## 2. [Regression Analysis]
- **Issue**: Modifying `JobMatchContextDTO` directly caused issues with existing tests that assumed a certain iteration shape in the old monolithic matching loop inside `LaborMarket.match_market` and the structure of Nash Bargaining outputs.
- **Resolution**: Refactored the backward-compatible translation layer within `LaborMarket.match_market` to precisely hydrate the `LaborMarketMatchResultDTO` using the true original reservation wage fetched via `JobSeekerDTO` to calculate the `surplus_pennies` appropriately rather than calculating it against the final agreed wage.
- **Type Compliance**: Pydantic was successfully installed to ensure the module dependencies for `DEFAULT_CURRENCY` loading within `simulation/dtos/api.py` resolved correctly, preventing import failures at application startup.
- **DTO Initialization**: Missing parameter assignments during `PricingInputDTO` instantiation inside `simulation/firms.py` were corrected to populate the `assets` fields properly for the Zombie Firm prevention logic to consume without attribute errors.

## 3. [Test Evidence]
```text
=========================== short test summary info ============================
SKIPPED [1] tests/integration/test_server_integration.py:16: websockets is mocked
SKIPPED [1] tests/security/test_god_mode_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/security/test_server_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/security/test_websocket_auth.py:13: websockets is mocked
SKIPPED [1] tests/system/test_server_auth.py:11: websockets is mocked, skipping server auth tests
SKIPPED [1] tests/test_server_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/test_ws.py:11: fastapi is mocked
SKIPPED [1] tests/market/test_dto_purity.py:26: Pydantic is mocked
SKIPPED [1] tests/market/test_dto_purity.py:54: Pydantic is mocked
SKIPPED [1] tests/modules/system/test_global_registry.py:101: Pydantic is mocked
SKIPPED [1] tests/modules/system/test_global_registry.py:132: Pydantic is mocked
XFAIL tests/integration/scenarios/test_scenario_runner.py::TestScenarioRunner::test_run_scenario[/app/tests/integration/scenarios/definitions/gold_standard.json] - TD-ARCH-MOCK-POLLUTION: VectorizedHouseholdPlanner uses numpy ops which fail with MagicMocks from tests.
XFAIL tests/integration/scenarios/test_scenario_runner.py::TestScenarioRunner::test_run_scenario[/app/tests/integration/scenarios/definitions/industrial_revolution.json] - TD-ARCH-MOCK-POLLUTION: VectorizedHouseholdPlanner uses numpy ops which fail with MagicMocks from tests.
=========== 1148 passed, 11 skipped, 2 xfailed, 1 warning in 12.01s ============
```
