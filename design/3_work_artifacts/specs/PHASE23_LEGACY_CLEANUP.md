# Mission Spec: Phase 23 - Legacy Modernization & API Cleanup

This mission resolves deprecated imports, stale lifecycle calls, and obsolete protocols.

## Checklist

### Legacy Imports & Code Removal
- [ ] **simulation/systems/demographic_manager.py**
    - [ ] [MODIFY] Change `from simulation.factories.agent_factory import HouseholdFactory` -> `from simulation.factories.household_factory import HouseholdFactory`.
- [ ] **simulation/initialization/initializer.py**
    - [ ] [MODIFY] Change `from simulation.factories.agent_factory import HouseholdFactory` -> `from simulation.factories.household_factory import HouseholdFactory`.
- [ ] **simulation/factories/agent_factory.py**
    - [ ] [DELETE] Remove file (Logic has migrated to `household_factory.py`).
- [ ] **simulation/systems/api.py**
    - [ ] [DELETE] Remove `ITransactionManager` protocol.

### Stale Lifecycle Logic
- [ ] **tests/system/test_engine.py**
    - [ ] [MODIFY] Replace `sim.lifecycle_manager._handle_agent_liquidation(state)` with `sim.lifecycle_manager.execute(state)`.
- [ ] **scripts/audit_zero_sum.py**
    - [ ] [MODIFY] Replace `sim.lifecycle_manager._handle_agent_liquidation(sim_state)` with `Simulation.run_tick` or `DeathSystem.execute`.

### Cockpit Logic Modernization
- [ ] **tests/integration/test_tick_normalization.py**
    - [ ] [MODIFY] Rename `state.system_command_queue = deque()` to `state.system_commands = []`.
- [ ] **tests/orchestration/test_state_synchronization.py**
    - [ ] [MODIFY] Rename `ws.system_command_queue` to `ws.system_commands`.

### Tax Agency Modernization
- [ ] **simulation/systems/tax_agency.py**
    - [ ] [MODIFY] Deprecate/Remove `collect_tax`. Use `settlement_system.transfer`.
- [ ] **tests/unit/systems/test_tax_agency.py**
    - [ ] [MODIFY] Align with `SettlementSystem` usage.
- [ ] **tests/unit/agents/test_government.py**
    - [ ] [MODIFY] Align with `SettlementSystem` usage.
- [ ] **tests/integration/test_government_tax.py**
    - [ ] [MODIFY] Align with `SettlementSystem` usage.

## Total Files: 12
