# Mission Order: MISSION-B1-HOUSEHOLD-DTO (Baseline for 2nd Liquidation)

**Task ID**: MISSION-B1-HOUSEHOLD-DTO
**Target Spec**: `design/3_work_artifacts/specs/TD-065_Household_Refactor_Spec.md` (Track A focus)
**Objective**: Prepare DTOs and Interfaces for the upcoming Household decomposition.

## 📋 Instructions
1.  **DTO Definition**: Create `modules/household/dtos.py` and define `HouseholdStateDTO` as a read-only Pydantic/dataclass for external consumers.
2.  **Interface Contracting**: Create `modules/household/api.py` and define `IBioComponent`, `IEconComponent`, and `ISocialComponent` interfaces.
3.  **Baseline Integration**: Prepare `DecisionContext` in `simulation/dtos/api.py` to optionally support `HouseholdStateDTO`.
4.  **No Logic Migration**: Do NOT migrate `Household` logic yet. This mission is purely for establishing the architectural "blueprint".

## 🚨 Constraints
- Strictly follow the "Track A" section of the TD-065 spec.
- No changes to `core_agents.py` logic in this mission.
- Avoid any breaking changes to existing simulation flow.
