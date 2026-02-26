# Insight Report: High-Performance Scenario Loader (WO-REBIRTH-SCENARIO-LOADER)

## 1. Architectural Insights
### Data Persistence & DTOs
- **Persistence DTOs**: We introduced `HouseholdPersistenceDTO` and `FirmPersistenceDTO` in `simulation/dtos/persistence.py`. These serve as wrappers around the immutable `SnapshotDTO`s, adding transient state fields (e.g., `distress_tick_counter`, `credit_frozen_until_tick`) that are necessary for a "Warm-Start" but not typically exposed in the read-only snapshot.
- **Serialization Strategy**: Implemented `SimulationEncoder` to handle complex types (`deque`, `Enum`, `Wallet`, `Portfolio`) natively. This allows us to store the full agent state in a single JSON column (`state_json`) in the SQLite database, simplifying schema management while retaining flexibility.
- **Enum Hydration**: A critical challenge was restoring Enums (like `IndustryDomain` and `Personality`) from JSON strings. We added explicit hydration logic in `SimulationInitializer` to convert string values back to their Enum members, preventing `AttributeError` in downstream logic that expects Enum comparisons.

### Scenario Strategy & Deep Merge
- **Deep Merge for Shocks**: To support granular scenario overrides via `shocks.json`, we implemented a `deep_merge` utility. This allows `shocks.json` to selectively update nested dictionary fields (e.g., `exogenous_productivity_shock["ENERGY"]`) in `ScenarioStrategy` without wiping out the entire dictionary configuration.

### Random Number Generation
- **Multi-Layer Seeding**: The loader now explicitly restores both `random.seed()` and `np.random.seed()` from the source run's seed. This guarantees that "Rebirth" runs are statistically deterministic relative to their source, enabling A/B testing of interventions (Shocks) against a control baseline.

## 2. Regression Analysis
During development, several issues were identified and resolved:
1.  **SQLite Schema Mismatch**: The `seed` column was added to `simulation_runs`, but initial tests failed due to a discrepancy between the in-memory fixture setup and the repository's expected schema. This was resolved by verifying the `CREATE TABLE` and `INSERT` statements aligned.
2.  **DTO Attribute Errors**: `HouseholdPersistenceDTO` initially lacked the `major` field, causing `AttributeError` during restoration. We refactored `Household.restore_from_persistence_dto` to rely on the `major` field nested within `HouseholdSnapshotDTO.econ_state`, and ensured the hydration logic correctly populated this nested field from the JSON data.
3.  **Config Injection**: The integration test required extensive mocking of the configuration module. We hardened the `SimulationInitializer` to be more robust against missing config keys by using `getattr` with defaults or explicit DTO checks.

## 3. Test Evidence
### `pytest tests/simulation/test_scenario_loader.py` Output
```text
tests/simulation/test_scenario_loader.py::test_batch_load_from_db
-------------------------------- live log call ---------------------------------
INFO     simulation.db.run_repository:run_repository.py:31 Started new simulation run with ID: 1, Seed: 42
INFO     simulation.db.run_repository:run_repository.py:31 Started new simulation run with ID: 2, Seed: 42
INFO     simulation.db.run_repository:run_repository.py:31 Started new simulation run with ID: 3, Seed: 42
PASSED                                                                   [ 33%]
tests/simulation/test_scenario_loader.py::test_load_shocks_deep_merge PASSED [ 66%]
tests/simulation/test_scenario_loader.py::test_seed_consistency
-------------------------------- live log call ---------------------------------
INFO     simulation.db.run_repository:run_repository.py:31 Started new simulation run with ID: 1, Seed: 12345
INFO     simulation.db.run_repository:run_repository.py:31 Started new simulation run with ID: 2, Seed: 12345
PASSED                                                                   [100%]
```

### Full Simulation Test Suite (`tests/simulation`)
```text
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_initialization PASSED [  3%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_step_delegates_to_strategy PASSED [  7%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_omo_execution PASSED [ 11%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_snapshot_construction PASSED [ 14%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_automation_success PASSED [ 18%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_automation_max_cap PASSED [ 22%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_capex_success PASSED [ 25%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_negative_amount PASSED [ 29%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_unknown_type PASSED [ 33%]
tests/simulation/components/engines/test_firm_decoupling.py::test_production_engine_decoupled PASSED [ 37%]
tests/simulation/components/engines/test_firm_decoupling.py::test_hr_engine_decoupled PASSED [ 40%]
tests/simulation/components/engines/test_firm_decoupling.py::test_sales_engine_decoupled PASSED [ 44%]
tests/simulation/components/engines/test_production_engine.py::test_produce_success PASSED [ 48%]
tests/simulation/components/engines/test_production_engine.py::test_produce_input_constraint PASSED [ 51%]
tests/simulation/components/engines/test_production_engine.py::test_produce_no_employees PASSED [ 55%]
tests/simulation/components/engines/test_rd_engine.py::test_research_success PASSED [ 59%]
tests/simulation/components/engines/test_rd_engine.py::test_research_failure PASSED [ 62%]
tests/simulation/components/engines/test_rd_engine.py::test_research_negative_amount PASSED [ 66%]
tests/simulation/factories/test_agent_factory.py::test_create_household PASSED [ 70%]
tests/simulation/factories/test_agent_factory.py::test_create_newborn PASSED [ 74%]
tests/simulation/test_firm_refactor.py::test_firm_initialization_states PASSED [ 77%]
tests/simulation/test_firm_refactor.py::test_command_bus_internal_orders_delegation PASSED [ 81%]
tests/simulation/test_firm_refactor.py::test_produce_orchestration PASSED [ 85%]
tests/simulation/test_initializer.py::TestSimulationInitializer::test_registry_linked_before_bootstrap PASSED [ 88%]
tests/simulation/test_scenario_loader.py::test_batch_load_from_db PASSED [ 92%]
tests/simulation/test_scenario_loader.py::test_load_shocks_deep_merge PASSED [ 96%]
tests/simulation/test_scenario_loader.py::test_seed_consistency PASSED [100%]
```
