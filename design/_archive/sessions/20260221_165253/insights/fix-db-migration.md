# Insight: Fix Database Schema Drift & Auto-Migration

## 1. Architectural Insights
- **Schema Drift Detected**: The `transactions` table in SQLite databases was often missing the `total_pennies` column due to inconsistent schema definitions (`schema.py` vs `db_manager.py`) and legacy databases.
- **Migration Strategy**: Implemented `SchemaMigrator` (implementing `IDatabaseMigrator` protocol) to auto-detect and fix schema drift on `SimulationRepository` initialization. It executes `ALTER TABLE` and backfills `total_pennies` using `price * quantity`.
- **Protocol Enforced**: `CentralBank` agent was not compliant with `ICentralBank` protocol (missing `IMonetaryOperations`), causing runtime failures in strict solvency checks (`SettlementSystem`). This was fixed by implementing missing methods and explicit inheritance.
- **Test Integrity**: Found `tests/system/test_engine.py` was using hardcoded agent IDs (1, 2) conflicting with reserved System Agent IDs (Government=1, Bank=2). This caused Government to overwrite a Household in the registry, leading to "Insufficient Funds" errors in tests as Government has 0 initial cash. Updated tests to use safe ID ranges (200+).

## 2. Regression Analysis
- **Failure**: `tests/system/test_engine.py` failed initially.
- **Cause 1**: `CentralBank` did not implement `ICentralBank`, causing `SettlementSystem._prepare_seamless_funds` to return False (rejecting infinite liquidity), which failed the `Bootstrapper` injection logic.
- **Fix 1**: Updated `CentralBank` to inherit `ICentralBank` and implement `execute_open_market_operation` and `process_omo_settlement`.
- **Cause 2**: Test setup created Households with IDs `1` and `2`. `SimulationInitializer` registers `Government` at ID `1`. This overwrote Household 1 with Government (which has 0 cash).
- **Fix 2**: Updated `test_engine.py` to use IDs `201, 202` for households, avoiding system reserved range (0-100).

## 3. Test Evidence
```
tests/test_db_migration.py::test_fresh_install_transactions_table_created PASSED [ 33%]
tests/test_db_migration.py::test_migration_adds_total_pennies PASSED             [ 66%]
tests/test_db_migration.py::test_idempotency PASSED                              [100%]

tests/system/test_engine.py::TestSimulation::test_simulation_initialization PASSED [ 33%]
tests/system/test_engine.py::TestSimulation::test_prepare_market_data_basic PASSED [ 38%]
tests/system/test_engine.py::TestSimulation::test_prepare_market_data_no_goods_market PASSED [ 44%]
tests/system/test_engine.py::TestSimulation::test_prepare_market_data_with_best_ask PASSED [ 50%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_goods_trade PASSED [ 55%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_labor_trade PASSED [ 61%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_research_labor_trade PASSED [ 66%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_invalid_agents PASSED [ 72%]
tests/system/test_engine.py::test_handle_agent_lifecycle_removes_inactive_agents PASSED [ 77%]
```
