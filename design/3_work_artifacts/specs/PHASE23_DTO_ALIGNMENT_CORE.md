# Mission Spec: Phase 23 - DTO Alignment (Core & Orchestration)

This mission aligns the `SimulationState` DTO with `WorldState` core attributes.

## Checklist

- [ ] **simulation/dtos/api.py**
    - [ ] [MODIFY] Rename `SimulationState.government` -> `primary_government`.
    - [ ] [MODIFY] Add `SimulationState.governments: List[Any] = field(default_factory=list)`.
    - [ ] [MODIFY] Rename `SimulationState.god_commands` -> `god_command_snapshot`.
- [ ] **simulation/world_state.py**
    - [ ] [VERIFY] `government` property sync with `governments[0]`.
- [ ] **simulation/orchestration/tick_orchestrator.py**
    - [ ] [MODIFY] In `_create_simulation_state_dto`, map `state.government` to `primary_government`.
    - [ ] [MODIFY] Map `state.governments` to `governments`.
    - [ ] [MODIFY] Map `god_commands_for_tick` to `god_command_snapshot`.
- [ ] **simulation/orchestration/phases/intercept.py**
    - [ ] [MODIFY] Replace `state.god_commands` with `state.god_command_snapshot`.
- [ ] **simulation/orchestration/phases/government_programs.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.
- [ ] **simulation/orchestration/phases/taxation_intents.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.
- [ ] **simulation/systems/registry.py**
    - [ ] [MODIFY] Replace any DTO field access logic.
- [ ] **modules/governance/api.py**
    - [ ] [VERIFY] `GodCommandDTO` definition alignment if applicable.

## Total Files: 8
