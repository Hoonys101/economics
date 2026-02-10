I will now begin the process of analyzing the test failures and updating the `ARCH_TESTS.md` file as requested.

First, I will read the existing `ARCH_TESTS.md` to understand its current structure and content.
Now that I have the current content, I will analyze the test failures and the full structure of the `tests/unit` directory to create an updated and comprehensive `ARCH_TESTS.md`.

My analysis of the `pytest_failures.log` reveals several major categories of errors, all stemming from the ongoing architectural refactoring:

1.  **Constructor Signature Changes**: A significant number of tests fail with `TypeError` because they are instantiating `Firm` and `Household` objects using an outdated constructor signature (e.g., passing `id=...`). The new constructors require different arguments, likely `core_config` and `engine` DTOs.
2.  **DTO Refactoring & State Access**: Many tests fail with `AttributeError`. This is because they try to access attributes like `.assets` or `._econ_state` directly on agent mocks. The agent state has been refactored into nested DTOs, so tests need to be updated to access state through the correct DTO path (e.g., `state.econ_state.wallet.get_balance()`).
3.  **API and Protocol Mismatches**: Failures like `TypeError: ... got an unexpected keyword argument 'currency'` indicate that the method signatures in interfaces (Protocols) have changed, but the mock objects used in tests have not been updated to match the new signature.
4.  **Incomplete or Incorrect Mocking**: Many `MagicMock` objects are not configured correctly. They either lack necessary attributes (e.g., `profit_history_ticks`), causing `AttributeError`s downstream, or they return another `MagicMock` by default when a primitive value (like a `float` or `int`) is expected, leading to `TypeError`s in subsequent operations.
5.  **Logic and Data Structure Changes**: Some tests fail on `AssertionError` because the underlying logic has changed, or data structures are different (e.g., a test expecting a `float` receives a `dict`).

Based on this, I will now formulate the new `ARCH_TESTS.md` content and write it to the file.
I have analyzed the test failures and the structure of the `tests/unit/` directory. Based on this analysis, I have prepared the updated content for `design/1_governance/architecture/ARCH_TESTS.md`.

Since I cannot directly write to the file, I am providing the complete and final version of the document below.

```markdown
# Unit Test Architecture & Cleanup Campaign Reference

## Executive Summary
This document provides a comprehensive and up-to-date overview of the unit test architecture within the `tests/unit/` directory. The test suite is extensive, but its structure has grown organically, leading to many misplaced files and inconsistent testing patterns. This analysis serves as a master reference to guide the ongoing effort to clean up, restructure, and improve the unit tests for better maintainability and clarity.

## 1. Structural Analysis of Test Failures
Recent test failures (e.g., `TypeError`, `AttributeError`, `Dataclass` issues) are primarily symptoms of a large-scale architectural refactoring. The core reasons are:

- **Constructor Mismatches**: The most common failure is a `TypeError` on `Household.__init__()` and `Firm.__init__()`. Tests are using outdated constructor signatures (e.g., passing `id=...`). The new architecture requires `core_config: AgentCoreConfigDTO` and `engine: IDecisionEngine` arguments, which are missing in dozens of test setups.
- **DTO/State Object Transition**: The codebase has migrated from direct object attribute manipulation (e.g., `agent.assets = 100`) to using nested, often immutable, Data Transfer Objects (DTOs) (e.g., `EconStateDTO`). Tests written for the old architecture fail with `AttributeError` when they try to access or set attributes that now reside within a DTO (e.g., `context.state.econ_state.wallet`).
- **Inconsistent/Incomplete Mocking**: Mocks are frequently not updated to reflect new realities. This leads to `AttributeError` when a test tries to access a newly added attribute on an old mock (e.g., a mock `config` object missing `profit_history_ticks`). It also causes `TypeError` when a `MagicMock` returns another mock instead of a primitive value (e.g., comparing a mock to an `int`).
- **Component-Based Refactoring**: Logic is being moved from large agent classes (e.g., `Household`) into smaller, focused components or managers (e.g., `ConsumptionManager`, `LifecycleComponent`). Tests targeting the old agent methods are now obsolete or fail because the logic has moved.
- **API and Protocol Drift**: Method signatures in interfaces (Protocols) have changed (e.g., `withdraw()` now requires a `currency` keyword argument), but test mocks have not been updated, causing `TypeError` on keyword arguments.

## 2. Module-to-Source Mapping & Relocation Plan

The following table maps each unit test file to its source module and provides a **Target Path** for the recommended restructuring. Files in the `tests/unit` root are the highest priority for relocation.

| Current Test Path | Source Module Tested | Recommended Target Path |
| :--- | :--- | :--- |
| `tests/unit/factories.py` | _Test Helper/Factory_ | `tests/unit/helpers/factories.py` |
| `tests/unit/test_ai_driven_firm_engine.py` | `simulation/decisions/ai_driven_firm_engine.py` | `tests/unit/simulation/decisions/test_ai_driven_firm_engine.py` |
| `tests/unit/test_ai_training_manager.py` | `simulation/ai/ai_training_manager.py` | `tests/unit/simulation/ai/test_ai_training_manager.py` |
| `tests/unit/test_api_extensions.py` | `simulation/viewmodels/economic_indicators_viewmodel.py` | `tests/unit/simulation/viewmodels/test_economic_indicators_viewmodel.py` |
| `tests/unit/test_api_history.py` | _N/A (Placeholder)_ | _(Remove or Implement)_ |
| `tests/unit/test_bank.py` | `simulation/bank.py` | `tests/unit/simulation/test_bank.py` |
| `tests/unit/test_bank_decomposition.py` | `simulation/bank.py` | `tests/unit/simulation/test_bank.py` (Merge) |
| `tests/unit/test_config_parity.py` | `config.py`, `simulation/utils/config_factory.py` | `tests/unit/utils/test_config_parity.py` |
| `tests/unit/test_consumption_manager_survival.py` | `simulation/decisions/household/consumption_manager.py` | `tests/unit/modules/household/test_consumption_manager.py` (Merge) |
| `tests/unit/test_diagnostics.py` | `simulation/world_state.py` | `tests/unit/simulation/test_world_state_diagnostics.py` |
| `tests/unit/test_factories.py` | `simulation/orchestration/factories.py` | `tests/unit/simulation/orchestration/test_factories.py` |
| `tests/unit/test_firms.py` | `simulation/firms.py` | `tests/unit/simulation/agents/test_firm.py` |
| `tests/unit/test_firm_profit.py` | `simulation/firms.py` | `tests/unit/simulation/agents/test_firm.py` (Merge) |
| `tests/unit/test_handlers_fix.py` | `simulation/systems/handlers/*` | `tests/unit/simulation/systems/handlers/` (Distribute) |
| `tests/unit/test_household_ai.py` | `simulation/ai/household_ai.py` | `tests/unit/simulation/ai/test_household_ai.py` |
| `tests/unit/test_household_decision_engine_new.py`| `simulation/decisions/ai_driven_household_engine.py` | `tests/unit/simulation/decisions/household/test_ai_driven_household_engine.py` (Merge) |
| `tests/unit/test_household_refactor.py` | `simulation/core_agents.py` (`Household`) | `tests/unit/simulation/agents/test_household.py` |
| `tests/unit/test_household_system2.py` | `simulation/ai/household_system2.py` | `tests/unit/simulation/ai/test_household_system2.py` |
| `tests/unit/test_learning_tracker.py` | `simulation/ai/learning_tracker.py` | `tests/unit/simulation/ai/test_learning_tracker.py` |
| `tests/unit/test_ledger_manager.py` | `scripts/ledger_manager.py` | `tests/unit/scripts/test_ledger_manager.py` |
| `tests/unit/test_logger.py` | `utils/logger.py` | `tests/unit/utils/test_logger.py` |
| `tests/unit/test_market_adapter.py` | `modules/market/api.py` | `tests/unit/modules/market/test_api.py` |
| `tests/unit/test_marketing_roi.py` | `simulation/firms.py` (Marketing Logic) | `tests/unit/simulation/agents/test_firm.py` (Merge) |
| `tests/unit/test_markets_v2.py` | `simulation/markets/order_book_market.py` | `tests/unit/simulation/markets/test_order_book_market.py` (Merge) |
| `tests/unit/test_monetary_ledger_repayment.py` | `modules/government/components/monetary_ledger.py` | `tests/unit/modules/government/components/test_monetary_ledger.py` |
| `tests/unit/test_phase1_refactor.py` | `simulation/orchestration/phases.py` | `tests/unit/simulation/orchestration/test_phases.py` |
| `tests/unit/test_portfolio_macro.py` | `simulation/decisions/portfolio_manager.py` | `tests/unit/simulation/decisions/test_portfolio_manager.py` |
| `tests/unit/test_real_estate_lien.py` | `simulation/models.py` | `tests/unit/simulation/test_models.py` |
| `tests/unit/test_repository.py` | `simulation/db/repository.py` | `tests/unit/simulation/db/test_repository.py` |
| `tests/unit/test_sensory_purity.py` | `simulation/systems/sensory_system.py` | `tests/unit/simulation/systems/test_sensory_system.py` |
| `tests/unit/test_socio_tech.py` | `simulation/ai/household_ai.py` | `tests/unit/simulation/ai/test_household_ai.py` (Merge) |
| `tests/unit/test_stock_market.py` | `simulation/markets/stock_market.py` | `tests/unit/simulation/markets/test_stock_market.py` |
| `tests/unit/test_taxation_system.py` | `modules/government/taxation/system.py` | `tests/unit/modules/government/taxation/test_system.py` |
| `tests/unit/test_tax_collection.py` | `simulation/agents/government.py` | `tests/unit/simulation/agents/test_government.py` (Merge) |
| `tests/unit/test_tax_incidence.py` | `simulation/engine.py` (Integration) | `tests/unit/simulation/test_engine_integrations.py` |
| `tests/unit/test_transaction_engine.py` | `modules/finance/transaction/engine.py` | `tests/unit/modules/finance/transaction/test_engine.py` |
| `tests/unit/test_transaction_processor.py` | `simulation/systems/transaction_processor.py` | `tests/unit/simulation/systems/test_transaction_processor.py` |
| `tests/unit/test_watchtower_hardening.py` | `simulation/metrics/economic_tracker.py`, `...` | `tests/unit/simulation/metrics/test_economic_tracker.py` |
| `tests/unit/test_wo157_dynamic_pricing.py`| `simulation/components/engines/sales_engine.py` | `tests/unit/simulation/components/engines/test_sales_engine.py` |
| `tests/unit/agents/test_government.py` | `simulation/agents/government.py` | `tests/unit/simulation/agents/test_government.py` (Merge) |
| `tests/unit/components/test_agent_lifecycle.py`| `simulation/components/agent_lifecycle.py` | `tests/unit/simulation/components/test_agent_lifecycle.py` |
| `tests/unit/components/test_demographics_component.py`| `simulation/components/demographics_component.py` | `tests/unit/simulation/components/test_demographics_component.py` |
| `tests/unit/components/test_market_component.py`| `simulation/components/market_component.py` | `tests/unit/simulation/components/test_market_component.py` |
| `tests/unit/corporate/*` | `simulation/decisions/firm/*` | `tests/unit/simulation/decisions/firm/` (Relocate files) |
| `tests/unit/decisions/*` | `simulation/decisions/*` | `tests/unit/simulation/decisions/` (Relocate files) |
| `tests/unit/finance/call_market/test_service.py`| `modules/finance/call_market/service.py` | `tests/unit/modules/finance/call_market/test_service.py` |
| `tests/unit/finance/test_bank_service_interface.py`| `simulation/bank.py`, `modules/finance/api.py` | `tests/unit/modules/finance/test_bank_service_interface.py` |
| `tests/unit/finance/test_credit_scoring.py` | `modules/finance/credit_scoring.py` | `tests/unit/modules/finance/test_credit_scoring.py` |
| `tests/unit/finance/test_finance_system_refactor.py`| `modules/finance/system.py` | `tests/unit/modules/finance/test_system.py` (Merge) |
| `tests/unit/governance/test_judicial_system.py` | `modules/governance/judicial/system.py` | `tests/unit/modules/governance/judicial/test_system.py` |
| `tests/unit/household/engines/*` | `modules/household/engines/*` | `tests/unit/modules/household/engines/` (Relocate files) |
| `tests/unit/household/test_snapshot_assembler.py`| `modules/household/services.py` | `tests/unit/modules/household/test_services.py` |
| `tests/unit/markets/*` | `simulation/markets/*`, `modules/market/*` | `tests/unit/simulation/markets/` & `tests/unit/modules/market/` |
| `tests/unit/modules/analysis/test_bubble_observatory.py`| `modules/analysis/bubble_observatory.py` | (No change) |
| `tests/unit/modules/common/config/test_impl.py` | `modules/common/config/impl.py` | (No change) |
| `tests/unit/modules/common/config_manager/test_config_manager.py` | `modules/common/config_manager/impl.py` | (No change) |
| `tests/unit/modules/finance/central_bank/test_cb_service.py` | `modules/finance/central_bank/service.py` | (No change) |
| `tests/unit/modules/finance/*` | `modules/finance/*` | (Distribute files) |
| `tests/unit/modules/government/components/*` | `modules/government/components/*` | (No change) |
| `tests/unit/modules/government/*` | `modules/government/*` | (Distribute files) |
| `tests/unit/modules/household/*` | `modules/household/*` | (No change) |
| `tests/unit/modules/memory/test_memory_v2.py` | `modules/memory/V2/*` | (No change) |
| `tests/unit/modules/system/execution/*` | `modules/system/execution/*` | (No change) |
| `tests/unit/orchestration/*` | `simulation/orchestration/*` | `tests/unit/simulation/orchestration/` (Relocate files) |
| `tests/unit/sagas/test_orchestrator.py` | `modules/finance/sagas/orchestrator.py` | `tests/unit/modules/finance/sagas/test_orchestrator.py` |
| `tests/unit/systems/handlers/*` | `simulation/systems/handlers/*`, `modules/market/handlers/*`| (Distribute files) |
| `tests/unit/systems/*` | `simulation/systems/*` | `tests/unit/simulation/systems/` (Relocate files) |
| `tests/unit/utils/test_config_factory.py` | `simulation/utils/config_factory.py` | `tests/unit/simulation/utils/test_config_factory.py` |

## 3. Coverage Gaps
Based on the comprehensive file review, the following source modules still appear to be **untested or undertested**:

- **`modules/analytics/`**: Core analytics logic and services.
- **`modules/events/`**: DTOs and event definitions.
- **`modules/hr/`**: The main HR service and components.
- **`modules/housing/`**: The `modules/housing` directory exists but has no tests.
- **`modules/inventory/`**: The core inventory management logic.
- **`modules/memory/`**: V1 of the memory system.
- **`modules/simulation/`**: The API/DTOs module itself lacks specific validation tests.
- **`scripts/`**: Most scripts are untested, with the exception of `ledger_manager.py`.

## 4. Test File Count by Domain
The test suite is heavily focused on `systems`, `decisions`, `agents`, and `finance`.

| Domain | Test File Count | Notes |
| :--- | :--- | :--- |
| **Agents & Core (`simulation`)** | ~10 | `test_firms`, `test_household_refactor`, `test_bank`, etc. |
| **AI & Decisions (`simulation`)** | ~25 | `test_ai_*`, `decisions/*`, `corporate/*`. High volume, needs consolidation. |
| **Finance (`modules`)** | ~11 | `finance/*`, `modules/finance/*`, `sagas/*`. |
| **Government (`modules`)** | ~6 | `test_government`, `modules/government/*`, etc. |
| **Household (`modules`)** | ~10 | `household/*`, `modules/household/*`. |
| **Systems (`simulation`/`modules`)** | ~30+ | `systems/*`, `test_transaction_processor`, etc. Largest category. |
| **Markets (`simulation`/`modules`)** | ~7 | `test_markets*`, `test_stock_market`, etc. |
| **Framework/Utils** | ~10 | `test_logger`, `test_repository`, `factories.py`, `mocks`, etc. |
| **Total** | **~100+** | Some files test multiple domains. |

## 5. Recommended Restructuring
The current structure, with a majority of files in the `tests/unit` root, is difficult to navigate. The presence of subdirectories like `agents/` and `modules/` is a good start, but this organization must be completed to mirror the source code.

**Recommendation:** Strictly mirror the `modules/` and `simulation/` source code structure within `tests/unit/`.

### Proposed `tests/unit/` Structure:
```
tests/unit/
├── simulation/
│   ├── ai/
│   ├── agents/
│   ├── components/
│   ├── db/
│   ├── decisions/
│   │   ├── household/
│   │   └── firm/
│   ├── markets/
│   ├── orchestration/
│   ├── systems/
│   │   └── handlers/
│   └── ...
├── modules/
│   ├── analysis/
│   ├── common/
│   │   ├── config/
│   │   └── config_manager/
│   ├── finance/
│   │   ├── call_market/
│   │   ├── central_bank/
│   │   └── sagas/
│   ├── governance/
│   ├── household/
│   │   └── engines/
│   ├── market/
│   └── ...
├── scripts/
└── utils/
```

### Action Items for Cleanup Campaign:

1.  **Create New Directory Structure:** Implement the proposed directory structure in `tests/unit/`.
2.  **Move Existing Tests:** Relocate each test file from its current location to its new **Target Path** as specified in the table above.
3.  **Update Imports:** Adjust relative and absolute imports within the moved test files to ensure they can still find their source modules and helpers.
4.  **Consolidate Duplicates:** Merge tests for the same module into a single, comprehensive file. For example, `test_ai_training_manager.py` and `test_ai_training_manager_new.py` should become one file at `tests/unit/simulation/ai/test_ai_training_manager.py`.
5.  **Address Gaps:** Begin creating new test files for the untested modules identified in the "Coverage Gaps" section, placing them in the correct new directory from the start.
6.  **Review Skipped Tests:** Systematically review tests marked with `@pytest.mark.skip` or `@unittest.skip`. Determine if they are obsolete and can be deleted, or if they need to be updated to test the new DTO-based, component-driven architecture.
```
