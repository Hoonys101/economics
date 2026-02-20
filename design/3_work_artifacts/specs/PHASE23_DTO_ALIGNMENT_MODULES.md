# Mission Spec: Phase 23 - DTO Alignment (Modules)

This mission updates business logic modules to reflect the `SimulationState` DTO renaming (`government` -> `primary_government`).

## Checklist

- [ ] **modules/finance/system.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.
- [ ] **modules/government/taxation/system.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.
- [ ] **modules/government/infrastructure/service.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.
- [ ] **modules/government/welfare/service.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.
- [ ] **simulation/systems/tax_agency.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.
- [ ] **simulation/systems/ma_manager.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.
- [ ] **simulation/systems/settlement_system.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.
- [ ] **scripts/hunt_leak.py**
    - [ ] [MODIFY] Replace `state.government` with `state.primary_government`.

## Total Files: 8
