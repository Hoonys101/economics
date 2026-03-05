# MISSION_SPEC: WO-SPEC-DTO-SUCCESSION
## Goal
Decouple `AgentLifecycleManager`, `DeathSystem`, `InheritanceManager`, and `LiquidationManager` from `WorldState`.

## Context
These systems handle agent aging, death, asset liquidation, and inheritance distribution. They are currently tightly integrated with the `SimulationState` tick loop.

## Proposed Changes
1. Inject `IShareholderRegistry` and `IEstateRegistry` into `DeathSystem`.
2. Refactor `AgentLifecycleManager.execute` to use domain-specific adapters instead of the whole `SimulationState`.
3. Eliminate `set_state(state)` calls in registries; use explicit query interfaces.

## Verification
- Run `pytest tests/unit/test_lifecycle_manager.py`.
