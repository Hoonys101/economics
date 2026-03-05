# MISSION_SPEC: WO-SPEC-DTO-VITAL-STATS
## Goal
Decouple `DemographicManager`, `ImmigrationManager`, and `BirthSystem` from `WorldState`.

## Context
These systems handle population growth, immigration, and birth event tracking. They currently access registries and configuration through `WorldState`.

## Proposed Changes
1. Inject `IAgentRegistry` into `DemographicManager`.
2. Pass `ImmigrationConfigDTO` and `BirthConfigDTO` directly.
3. Decouple `BirthSystem` from `SimulationState` by using `BirthContextDTO`.

## Verification
- Run `pytest tests/unit/test_demographic_manager.py`.
