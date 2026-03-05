# Phase 4.1 Wave 5.2: Account Registry & ID Hardening Insight Report

## Architectural Insights

### Account Registry Separation
- **Before**: `ISettlementSystem` inherited `IBankRegistry` (Account Lookup), and `SettlementSystem` implemented account tracking internally using `defaultdict(set)`. This coupled the Settlement System with account registry logic.
- **After**:
    - `IBankRegistry` (Account Lookup version) was renamed to `IAccountRegistry` in `modules/finance/api.py`.
    - `IBankRegistry` (Bank State Registry version) remains as is, resolving the shadowing conflict.
    - Created `modules/finance/registry/account_registry.py` implementing `IAccountRegistry`.
    - `SettlementSystem` now delegates account tracking to an instance of `AccountRegistry`, injected or defaulted in `__init__`.
- **Benefit**: Decouples concerns. `SettlementSystem` focuses on transactions, `AccountRegistry` focuses on mapping agents to banks.

### ID Hardening
- **AgentID Usage**: The new `IAccountRegistry` and `AccountRegistry` strictly use `AgentID` in method signatures and type hints, enforcing better type safety compared to raw `int`.
- **Protocol Fidelity**: `ISettlementSystem` now inherits `IAccountRegistry`, accurately reflecting its capability to look up accounts (via delegation).

## Regression Analysis

- **Existing Tests**:
    - `tests/finance` and `tests/simulation` passed without modification.
    - `SettlementSystem` remains backward compatible as it still exposes `register_account` etc., which delegate to the registry.
- **New Tests**:
    - `tests/finance/test_account_registry.py` was added to verify the integration and the new component.

## Test Evidence

### `pytest tests/finance`
```
tests/finance/test_circular_imports_fix.py::test_finance_system_instantiation_and_protocols PASSED [  5%]
tests/finance/test_circular_imports_fix.py::test_issue_treasury_bonds_protocol_usage
-------------------------------- live log call ---------------------------------
INFO     modules.finance.system:system.py:370 QE_ACTIVATED | Debt/GDP: 250000.00 > 1.5. Buyer: Central Bank
PASSED                                                                   [ 10%]
tests/finance/test_circular_imports_fix.py::test_evaluate_solvency_protocol_usage PASSED [ 15%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_settlement_overdraft_protection
-------------------------------- live log call ---------------------------------
ERROR    simulation.systems.settlement_system:settlement_system.py:339 SETTLEMENT_FAIL | Insufficient funds. Cash: 100, Req: 150.
PASSED                                                                   [ 20%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_settlement_zero_sum
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.settlement_system:engine.py:131 Transaction Record: ID=968f8a44-7fdf-4153-9084-9dc9e0f1ba0c, Status=COMPLETED, Message=Transaction successful.
PASSED                                                                   [ 25%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_central_bank_infinite_funds
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.settlement_system:engine.py:131 Transaction Record: ID=73029275-c778-4456-a6ab-514b1772c843, Status=COMPLETED, Message=Transaction successful.
PASSED                                                                   [ 30%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_real_estate_unit_lien_dto PASSED [ 35%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_housing_system_maintenance_zero_sum
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.settlement_system:engine.py:131 Transaction Record: ID=378cedfb-5d00-4b8f-ba8b-7d83d8ddcd20, Status=COMPLETED, Message=Transaction successful.
PASSED                                                                   [ 40%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_housing_system_rent_zero_sum
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.settlement_system:engine.py:131 Transaction Record: ID=12e42f6d-e89d-4e9c-8144-35b740dfc884, Status=COMPLETED, Message=Transaction successful.
PASSED                                                                   [ 45%]
tests/finance/test_settlement_fx_swap.py::test_execute_swap_success
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.settlement_system:engine.py:131 Transaction Record: ID=swap_1_leg1, Status=COMPLETED, Message=Transaction successful (Batch)
INFO     simulation.systems.settlement_system:engine.py:131 Transaction Record: ID=swap_1_leg2, Status=COMPLETED, Message=Transaction successful (Batch)
PASSED                                                                   [ 50%]
tests/finance/test_settlement_fx_swap.py::test_execute_swap_insufficient_funds_rollback
-------------------------------- live log call ---------------------------------
ERROR    simulation.systems.settlement_system:settlement_system.py:339 SETTLEMENT_FAIL | Insufficient funds. Cash: 100, Req: 400.
PASSED                                                                   [ 55%]
tests/finance/test_settlement_fx_swap.py::test_execute_swap_invalid_amounts
-------------------------------- live log call ---------------------------------
ERROR    simulation.systems.settlement_system:settlement_system.py:352 FX_SWAP_FAIL | Non-positive amounts: {'party_a_id': 101, 'party_b_id': 102, 'amount_a_pennies': -500, 'currency_a': 'USD', 'amount_b_pennies': 400, 'currency_b': 'EUR', 'match_tick': 1, 'rate_a_to_b': 0.8}
PASSED                                                                   [ 60%]
tests/finance/test_settlement_fx_swap.py::test_execute_swap_missing_agent
-------------------------------- live log call ---------------------------------
ERROR    simulation.systems.settlement_system:settlement_system.py:364 FX_SWAP_FAIL | Agents not found. A: 101, B: 102
PASSED                                                                   [ 65%]
tests/finance/test_settlement_integrity.py::TestSettlementIntegrity::test_transfer_float_raises_error PASSED [ 70%]
tests/finance/test_settlement_integrity.py::TestSettlementIntegrity::test_create_and_transfer_float_raises_error PASSED [ 75%]
tests/finance/test_settlement_integrity.py::TestSettlementIntegrity::test_issue_treasury_bonds_float_leak PASSED [ 80%]
tests/finance/test_solvency_logic.py::TestSolvencyLogic::test_solvency_grace_period_solvent PASSED [ 85%]
tests/finance/test_solvency_logic.py::TestSolvencyLogic::test_solvency_grace_period_insolvent PASSED [ 90%]
tests/finance/test_solvency_logic.py::TestSolvencyLogic::test_solvency_established_firm PASSED [ 95%]
tests/finance/test_solvency_logic.py::TestSolvencyLogic::test_firm_implementation PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 20 passed, 2 warnings in 1.01s ========================
```

### `pytest tests/simulation`
```
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_automation_success PASSED [  5%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_automation_max_cap PASSED [ 10%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_capex_success PASSED [ 15%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_negative_amount PASSED [ 21%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_unknown_type PASSED [ 26%]
tests/simulation/components/engines/test_firm_decoupling.py::test_production_engine_decoupled PASSED [ 31%]
tests/simulation/components/engines/test_firm_decoupling.py::test_hr_engine_decoupled PASSED [ 36%]
tests/simulation/components/engines/test_firm_decoupling.py::test_sales_engine_decoupled PASSED [ 42%]
tests/simulation/components/engines/test_production_engine.py::test_produce_success PASSED [ 47%]
tests/simulation/components/engines/test_production_engine.py::test_produce_input_constraint PASSED [ 52%]
tests/simulation/components/engines/test_production_engine.py::test_produce_no_employees PASSED [ 57%]
tests/simulation/components/engines/test_rd_engine.py::test_research_success PASSED [ 63%]
tests/simulation/components/engines/test_rd_engine.py::test_research_failure PASSED [ 68%]
tests/simulation/components/engines/test_rd_engine.py::test_research_negative_amount PASSED [ 73%]
tests/simulation/factories/test_agent_factory.py::test_create_household PASSED [ 78%]
tests/simulation/factories/test_agent_factory.py::test_create_newborn
-------------------------------- live log call ---------------------------------
INFO     simulation.factories.household_factory:ai_driven_household_engine.py:43 AIDrivenHouseholdDecisionEngine initialized (Modularized).
PASSED                                                                   [ 84%]
tests/simulation/test_firm_refactor.py::test_firm_initialization_states PASSED [ 89%]
tests/simulation/test_firm_refactor.py::test_command_bus_internal_orders_delegation
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:88 INTERNAL_EXEC | Firm 1 invested 100.0 in INVEST_AUTOMATION.
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:112 INTERNAL_EXEC | Firm 1 R&D SUCCESS (Budget: 100.0)
PASSED                                                                   [ 94%]
tests/simulation/test_firm_refactor.py::test_produce_orchestration PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 19 passed, 2 warnings in 0.44s ========================
```

### `pytest tests/finance/test_account_registry.py`
```
tests/finance/test_account_registry.py::test_account_registry_integration PASSED [ 50%]
tests/finance/test_account_registry.py::test_settlement_default_registry PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 2 warnings in 0.25s =========================
```
