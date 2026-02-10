# Unit Test Architecture & Cleanup Campaign Reference

## Executive Summary
This document provides a comprehensive overview of the existing unit test architecture within the `tests/unit/` directory. The test suite is extensive, but its structure has grown organically, leading to inconsistent file locations and some potential gaps in coverage. This analysis serves as a master reference to guide a parallel effort in cleaning up, restructuring, and improving the unit tests for better maintainability and clarity.

## 1. Module-to-Source Mapping

The following table maps each unit test file to the primary source module it is intended to test. This provides a clear "as-is" state of the test suite.

| Test File Path | Source Module Tested |
| :--- | :--- |
| `tests/unit/factories.py` | _Test Helper/Factory_ |
| `tests/unit/test_ai_driven_firm_engine.py` | `simulation/decisions/ai_driven_firm_engine.py` |
| `tests/unit/test_ai_training_manager.py` | `simulation/ai/ai_training_manager.py` |
| `tests/unit/test_ai_training_manager_new.py` | `simulation/ai/ai_training_manager.py` |
| `tests/unit/test_api_extensions.py` | `simulation/viewmodels/economic_indicators_viewmodel.py` |
| `tests/unit/test_api_history.py` | _N/A (Placeholder)_ |
| `tests/unit/test_bank.py` | `simulation/bank.py` |
| `tests/unit/test_bank_decomposition.py` | `simulation/bank.py` |
| `tests/unit/test_config_parity.py` | `config.py`, `simulation/utils/config_factory.py` |
| `tests/unit/test_consumption_manager_survival.py` | `simulation/decisions/household/consumption_manager.py` |
| `tests/unit/test_diagnostics.py` | `simulation/world_state.py` |
| `tests/unit/test_factories.py` | `simulation/orchestration/factories.py` |
| `tests/unit/test_firms.py` | `simulation/firms.py` |
| `tests/unit/test_firm_profit.py` | `simulation/firms.py` |
| `tests/unit/test_handlers_fix.py` | `simulation/systems/handlers/*` |
| `tests/unit/test_household_ai.py` | `simulation/ai/household_ai.py` |
| `tests/unit/test_household_ai_consumption.py` | `simulation/decisions/ai_driven_household_engine.py` |
| `tests/unit/test_household_decision_engine_multi_good.py`| `simulation/decisions/ai_driven_household_engine.py` |
| `tests/unit/test_household_decision_engine_new.py`| `simulation/decisions/ai_driven_household_engine.py` |
| `tests/unit/test_household_marginal_utility.py` | `simulation/decisions/ai_driven_household_engine.py` |
| `tests/unit/test_household_refactor.py` | `simulation/core_agents.py` (`Household`) |
| `tests/unit/test_household_system2.py` | `simulation/ai/household_system2.py` |
| `tests/unit/test_learning_tracker.py` | `simulation/ai/learning_tracker.py` |
| `tests/unit/test_ledger_manager.py` | `scripts/ledger_manager.py` |
| `tests/unit/test_logger.py` | `utils/logger.py` |
| `tests/unit/test_marketing_roi.py` | `simulation/firms.py` (Marketing Logic) |
| `tests/unit/test_markets_v2.py` | `simulation/markets/order_book_market.py` |
| `tests/unit/test_market_adapter.py` | `modules/market/api.py` |
| `tests/unit/test_monetary_ledger_repayment.py` | `modules/government/components/monetary_ledger.py` |
| `tests/unit/test_phase1_refactor.py` | `simulation/orchestration/phases.py` |
| `tests/unit/test_portfolio_macro.py` | `simulation/decisions/portfolio_manager.py` |
| `tests/unit/test_real_estate_lien.py` | `simulation/models.py` (`RealEstateUnit`) |
| `tests/unit/test_repository.py` | `simulation/db/repository.py` |
| `tests/unit/test_sensory_purity.py` | `simulation/systems/sensory_system.py` |
| `tests/unit/test_socio_tech.py` | `simulation/ai/household_ai.py` |
| `tests/unit/test_stock_market.py` | `simulation/markets/stock_market.py` |
| `tests/unit/test_taxation_system.py` | `modules/government/taxation/system.py` |
| `tests/unit/test_tax_collection.py` | `simulation/agents/government.py` |
| `tests/unit/test_tax_incidence.py` | `simulation/engine.py` (Integration) |
| `tests/unit/test_transaction_engine.py` | `modules/finance/transaction/engine.py` |
| `tests/unit/test_transaction_processor.py` | `simulation/systems/transaction_processor.py` |
| `tests/unit/test_watchtower_hardening.py` | `simulation/metrics/economic_tracker.py`, `simulation/db/agent_repository.py` |
| `tests/unit/test_wo157_dynamic_pricing.py`| `simulation/components/engines/sales_engine.py` |
| `tests/unit/agents/test_government.py` | `simulation/agents/government.py` |
| `tests/unit/components/test_agent_lifecycle.py`| `simulation/components/agent_lifecycle.py` |
| `tests/unit/components/test_demographics_component.py`| `simulation/components/demographics_component.py` |
| `tests/unit/components/test_market_component.py`| `simulation/components/market_component.py` |
| `tests/unit/corporate/*` | `simulation/decisions/firm/*` |
| `tests/unit/decisions/*` | `simulation/decisions/*` |
| `tests/unit/finance/test_bank_service_interface.py`| `simulation/bank.py`, `modules/finance/api.py` |
| `tests/unit/finance/test_credit_scoring.py` | `modules/finance/credit_scoring.py` |
| `tests/unit/finance/test_finance_system_refactor.py`| `modules/finance/system.py` |
| `tests/unit/finance/call_market/test_service.py`| `modules/finance/call_market/service.py` |
| `tests/unit/governance/test_judicial_system.py` | `modules/governance/judicial/system.py` |
| `tests/unit/household/test_snapshot_assembler.py`| `modules/household/services.py` |
| `tests/unit/household/engines/*` | `modules/household/engines/*` |
| `tests/unit/markets/*` | `simulation/markets/*`, `modules/market/handlers/*` |
| `tests/unit/modules/analysis/test_bubble_observatory.py`| `modules/analysis/bubble_observatory.py` |
| `tests/unit/modules/common/config/*` | `modules/common/config/*` |
| `tests/unit/modules/common/config_manager/*` | `modules/common/config_manager/*` |
| `tests/unit/modules/finance/*` | `modules/finance/*` |
| `tests/unit/modules/government/*` | `modules/government/*` |
| `tests/unit/modules/household/*` | `modules/household/*` |
| `tests/unit/modules/system/execution/*` | `modules/system/execution/*` |
| `tests/unit/orchestration/test_command_service.py`| `simulation/orchestration/command_service.py` |
| `tests/unit/orchestration/test_phase_housing_saga.py`| `simulation/orchestration/phases.py` |
| `tests/unit/sagas/test_orchestrator.py` | `modules/finance/sagas/orchestrator.py` |
| `tests/unit/systems/*` | `simulation/systems/*` |
| `tests/unit/utils/test_config_factory.py` | `simulation/utils/config_factory.py` |

## 2. Coverage Gaps

Based on the project structure and the list of tests, the following source modules appear to be **untested or undertested**:

- `modules/analytics/`
- `modules/events/`
- `modules/hr/`
- `modules/inventory/`
- `modules/memory/` (V1, V2 has tests)
- `modules/simulation/` (The API/DTOs module itself)
- `utils/` (Excluding `logger.py` and `config_factory.py`)
- `scripts/` (Excluding `ledger_manager.py`)

## 3. Test File Count by Domain

The test suite is heavily focused on `systems`, `decisions`, `agents`, and `finance`.

| Domain | Test File Count | Notes |
| :--- | :--- | :--- |
| **Agents & Core** | 8 | `test_firms`, `test_household_refactor`, etc. |
| **AI & Decisions** | 24 | `test_ai_*`, `decisions/*`, `corporate/*`, etc. High volume. |
| **Finance & Sagas** | 16 | `test_bank*`, `finance/*`, `sagas/*`, etc. |
| **Systems** | 28 | `systems/*`, `test_transaction_processor`, etc. Largest category. |
| **Markets** | 6 | `test_markets*`, `test_stock_market`, etc. |
| **Modules (Misc)** | 8 | `modules/analysis`, `modules/common`, `modules/memory` etc. |
| **Framework/Utils** | 8 | `test_logger`, `test_repository`, `factories.py`, etc. |
| **Total** | **108** | |

## 4. Recommended Restructuring

The current structure, with most files in the root of `tests/unit`, is becoming unwieldy. The presence of subdirectories like `agents/`, `components/`, and `modules/` indicates a move towards better organization, which should be completed.

**Recommendation:** Mirror the source code structure within `tests/unit/`.

### Proposed `tests/unit/` Structure:

```
tests/unit/
├── simulation/
│   ├── ai/
│   │   ├── test_ai_training_manager.py
│   │   ├── test_household_ai.py
│   │   └── test_household_system2.py
│   ├── agents/
│   │   ├── test_government.py
│   │   └── ...
│   ├── components/
│   │   └── ...
│   ├── db/
│   │   └── test_repository.py
│   ├── decisions/
│   │   ├── test_ai_driven_firm_engine.py
│   │   ├── household/
│   │   │   └── test_consumption_manager.py
│   │   └── firm/
│   │       ├── test_corporate_orchestrator.py
│   │       └── ...
│   ├── markets/
│   │   ├── test_order_book_market.py
│   │   └── test_stock_market.py
│   ├── orchestration/
│   │   ├── test_phases.py
│   │   └── test_factories.py
│   ├── systems/
│   │   ├── test_commerce_system.py
│   │   ├── test_firm_management.py
│   │   └── handlers/
│   │       └── test_housing_handler.py
│   └── ...
├── modules/
│   ├── analysis/
│   │   └── test_bubble_observatory.py
│   ├── common/
│   │   └── config/
│   │       └── test_impl.py
│   ├── finance/
│   │   ├── test_system.py
│   │   ├── call_market/
│   │   │   └── test_service.py
│   │   └── sagas/
│   │       └── test_orchestrator.py
│   └── ...
├── scripts/
│   └── test_ledger_manager.py
└── utils/
    ├── test_logger.py
    └── test_config_factory.py

```

### Action Items for Cleanup Campaign:

1.  **Create New Directory Structure:** Implement the proposed directory structure.
2.  **Move Existing Tests:** Relocate each test file from `tests/unit/` to its new corresponding location (e.g., `tests/unit/test_bank.py` -> `tests/unit/simulation/test_bank.py`).
3.  **Update Imports:** Adjust relative imports within the test files to reflect their new locations.
4.  **Consolidate Duplicates:** Merge tests for the same module (e.g., `test_ai_training_manager.py` and `test_ai_training_manager_new.py`) into a single, comprehensive file.
5.  **Address Gaps:** Begin creating new test files for the untested modules identified in the "Coverage Gaps" section.
