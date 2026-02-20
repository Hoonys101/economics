# Mission Spec: Phase 23 - DTO Alignment (Tests)

This mission updates all unit and integration tests to align with the `SimulationState` DTO renaming.

## Checklist

- [ ] **tests/unit/systems/test_finance.py**
- [ ] **tests/unit/agents/test_government.py**
- [ ] **tests/orchestration/test_tick_orchestrator.py**
- [ ] **tests/unit/systems/handlers/test_housing_handler.py**
- [ ] **tests/unit/test_transaction_handlers.py**
- [ ] **tests/modules/governance/test_cockpit_flow.py**
- [ ] **tests/modules/governance/test_system_command_processor.py**
- [ ] **tests/integration/test_cockpit_integration.py**
- [ ] **tests/integration/scenarios/verify_m2_fix.py**
- [ ] **tests/integration/scenarios/verify_stock_trading.py**
- [ ] **tests/integration/test_reporting_pennies.py**
- [ ] **tests/unit/test_factories.py**
- [ ] **tests/unit/test_government_structure.py**
- [ ] **tests/unit/systems/test_liquidation_manager.py**
- [ ] **tests/unit/systems/lifecycle/test_death_system.py**
- [ ] **tests/unit/test_phase1_refactor.py**
- [ ] **tests/unit/test_tax_incidence.py**

## Target Action
- Replace all mock attribute assignments or assertions:
    - `state.government` -> `state.primary_government`
    - `ws.government` -> `ws.primary_government` (where State DTO mock is used)

## Total Files: 17
