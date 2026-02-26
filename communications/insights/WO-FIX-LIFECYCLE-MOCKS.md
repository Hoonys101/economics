# Insight Report: WO-FIX-LIFECYCLE-MOCKS

## [Architectural Insights]
- **DTO Construction from Mocks**: The use of factory methods like `from_config_module` in DTOs (e.g., `LifecycleConfigDTO`, `BirthConfigDTO`) enforces strict typing (`int`, `float`) and default value resolution. This pattern exposes incomplete mocks early (via `TypeError` or `AttributeError` on primitive casting) rather than allowing them to propagate silently as `MagicMock` objects, which later cause confusing comparison errors (e.g., `int > MagicMock`).
- **Test Fixture Robustness**: Test fixtures mocking global configuration modules must be comprehensive. When subsystems rely on "God Configs", partial mocking leads to fragile tests. Using typed DTOs encourages mocking only what is necessary, but when a legacy config module is expected, it must fully populate the required keys.

## [Regression Analysis]
- **Broken Tests**:
    - `tests/test_firm_survival.py`: Failed because `AgingSystem` compared `firm.needs` (float) with `config.liquidity_need_increase_rate` (Mock).
    - `tests/system/test_engine.py`: Failed because `BirthConfigDTO.from_config_module` and `LifecycleConfigDTO.from_config_module` tried to cast Mock attributes to `int`/`float`.
- **Fix**:
    - Updated `mock_config_module` fixture in `tests/system/test_engine.py` to include missing keys (`REPRODUCTION_AGE_START`, `DEFAULT_FALLBACK_PRICE`, etc.) with primitive values.
    - Updated `aging_system` fixture in `tests/test_firm_survival.py` to use lowercase attribute names (matching `LifecycleConfigDTO` fields) and primitive values.
- **Alignment**: These fixes align with the "Protocol Purity" and "DTO Purity" guardrails by ensuring that data boundaries (Config -> DTO -> System) are respected even in test environments.

## [Test Evidence]
```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pyproject.toml
plugins: cov-6.0.0, anyio-4.8.0, html-4.1.1, metadata-3.1.1, asyncio-0.25.3
asyncio: mode=Mode.STRICT
collected 14 items

tests/system/test_engine.py::TestSimulation::test_simulation_initialization
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     simulation.systems.bootstrapper:bootstrapper.py:104 BOOTSTRAPPER | Injected 50.0 units to Firm 101 (Genesis)
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 10990000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 101 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:104 BOOTSTRAPPER | Injected 60.0 units to Firm 102 (Genesis)
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 20980000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000250
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 2 workers to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 0 workers to Firm 102
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 2
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
PASSED                                                                   [  7%]
tests/system/test_engine.py::TestSimulation::test_prepare_market_data_basic
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 10990000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 101 via Settlement.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 20980000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000250
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 2 workers to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 0 workers to Firm 102
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 2
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
PASSED                                                                   [ 14%]
tests/system/test_engine.py::TestSimulation::test_prepare_market_data_no_goods_market
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 10990000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 101 via Settlement.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 20980000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000250
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 2 workers to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 0 workers to Firm 102
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 2
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
PASSED                                                                   [ 21%]
tests/system/test_engine.py::TestSimulation::test_prepare_market_data_with_best_ask
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 10990000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 101 via Settlement.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 20980000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000250
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 2 workers to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 0 workers to Firm 102
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 2
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
PASSED                                                                   [ 28%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_goods_trade
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 10990000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 101 via Settlement.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 20980000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000250
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 2 workers to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 0 workers to Firm 102
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 2
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
PASSED                                                                   [ 35%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_labor_trade
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 10990000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 101 via Settlement.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 20980000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000250
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 2 workers to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 0 workers to Firm 102
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 2
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
PASSED                                                                   [ 42%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_research_labor_trade
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 10990000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 101 via Settlement.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 20980000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000250
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 2 workers to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 0 workers to Firm 102
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 2
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
PASSED                                                                   [ 50%]
tests/system/test_engine.py::TestSimulation::test_process_transactions_invalid_agents
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 10990000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 101 via Settlement.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9990000 (BOOTSTRAP_INJECTION) | New Expected M2: 20980000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9990000 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000250
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 2 workers to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:69 BOOTSTRAPPER | Force-assigned 0 workers to Firm 102
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 2
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
PASSED                                                                   [ 57%]
tests/system/test_engine.py::test_handle_agent_lifecycle_removes_inactive_agents
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     simulation.systems.bootstrapper:bootstrapper.py:104 BOOTSTRAPPER | Injected 50.0 units to Firm 101 (Genesis)
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9999000 (BOOTSTRAP_INJECTION) | New Expected M2: 10999000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9999000 capital to Firm 101 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:104 BOOTSTRAPPER | Injected 50.0 units to Firm 102 (Genesis)
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9999500 (BOOTSTRAP_INJECTION) | New Expected M2: 20998500
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9999500 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000220
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 0
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
-------------------------------- live log call ---------------------------------
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +25000 (LIQUIDATION_BAILOUT) | New Expected M2: 20025220
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:81 LIQUIDATION_START | Agent 102 starting liquidation. Assets: 10025000, Total Claims: 0
INFO     simulation.registries.estate_registry:estate_registry.py:28 ESTATE: Agent 102 added to Estate Registry.
INFO     simulation.registries.estate_registry:estate_registry.py:28 ESTATE: Agent 202 added to Estate Registry.
PASSED                                                                   [ 64%]
tests/system/test_engine.py::test_death_system_executes_asset_buyout
-------------------------------- live log setup --------------------------------
ERROR    modules.system.services.schema_loader:schema_loader.py:25 Schema file /app/config/domains/registry_schema.yaml must contain a list of objects.
INFO     simulation.agents.central_bank:central_bank.py:77 CENTRAL_BANK_INIT | Rate: 5.00%, Target Infl: 2.00%, Policy: MonetaryRuleType.TAYLOR_RULE
INFO     simulation.bank:bank.py:71 Bank 2 initialized (Stateless Proxy).
INFO     simulation.agents.government:government.py:180 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
INFO     simulation.loan_market:loan_market.py:35 LoanMarket loan_market initialized with bank service: 2
INFO     simulation.ai.ai_training_manager:ai_training_manager.py:20 AITrainingManager initialized.
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +1000000 (GENESIS_GRANT) | New Expected M2: 1000000
INFO     simulation.systems.bootstrapper:bootstrapper.py:104 BOOTSTRAPPER | Injected 50.0 units to Firm 101 (Genesis)
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9999000 (BOOTSTRAP_INJECTION) | New Expected M2: 10999000
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9999000 capital to Firm 101 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:104 BOOTSTRAPPER | Injected 50.0 units to Firm 102 (Genesis)
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +9999500 (BOOTSTRAP_INJECTION) | New Expected M2: 20998500
INFO     simulation.systems.bootstrapper:bootstrapper.py:123 BOOTSTRAPPER | Injected 9999500 capital to Firm 102 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:143 BOOTSTRAPPER | Injected resources into 2 firms.
INFO     modules.finance.kernel.ledger:ledger.py:37 MONETARY_LEDGER | Baseline M2 set to: 20000220
INFO     simulation.systems.bootstrapper:bootstrapper.py:71 BOOTSTRAPPER | Total force-assigned workers: 0
INFO     simulation.engine:engine.py:97 Simulation initialized and database schema verified.
-------------------------------- live log call ---------------------------------
INFO     modules.finance.kernel.ledger:ledger.py:88 MONETARY_LEDGER | M2 Expansion: +25000 (LIQUIDATION_BAILOUT) | New Expected M2: 20025220
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:81 LIQUIDATION_START | Agent 102 starting liquidation. Assets: 10025000, Total Claims: 0
INFO     simulation.registries.estate_registry:estate_registry.py:28 ESTATE: Agent 102 added to Estate Registry.
INFO     simulation.registries.estate_registry:estate_registry.py:28 ESTATE: Agent 201 added to Estate Registry.
INFO     simulation.registries.estate_registry:estate_registry.py:28 ESTATE: Agent 202 added to Estate Registry.
PASSED                                                                   [ 71%]
tests/test_firm_survival.py::test_solvent_firm_survival PASSED           [ 78%]
tests/test_firm_survival.py::test_insolvent_firm_death PASSED            [ 85%]
tests/test_firm_survival.py::test_zombie_firm_death PASSED               [ 92%]
tests/test_firm_survival.py::test_omo_quantity_calculation
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.central_bank_system:central_bank_system.py:58 OMO: Placing BUY order for 100 bonds (Target: 1000000).
PASSED                                                                   [100%]

======================== 14 passed, 1 warning in 1.56s =========================
```