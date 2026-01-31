# TD-066: Household Engine Decomposition & Survival Logic Migration

## Context
The `AIDrivenHouseholdDecisionEngine` was previously a monolithic class containing logic for consumption, labor, investment, and housing. It has been partially refactored into specialized managers (`ConsumptionManager`, `LaborManager`, etc.), but the "Phase 2: Survival Override" logic (panic buying food when starving) remained in the coordinator engine.

## Problem
The persistence of the Survival Override logic in the engine violates the Single Responsibility Principle and the Coordinator Pattern. The engine should strictly orchestrate, while domain logic should reside in managers. Specifically, the logic for deciding *what* to buy (even in emergencies) belongs to the `ConsumptionManager`.

## Solution
1.  **Decomposition**: Move the Survival Override logic into `ConsumptionManager.check_survival_override()`.
2.  **Delegation**: The engine will delegate this check to the manager before proceeding with the standard AI-driven flow.
3.  **Encapsulation**: This completes the extraction of consumption-related decision logic from the engine.

## Impact
- Reduces complexity of `ai_driven_household_engine.py` (further).
- Centralizes all consumption logic (routine and emergency) in `ConsumptionManager`.
- Improves testability of the survival logic.

## Technical Debt / Risks
- **Dependency on `HouseholdActionVector`**: The `ConsumptionManager` now needs to be aware of `HouseholdActionVector` to return the appropriate override signal. This creates a slight coupling to the schema used by the AI engine, but it is necessary for the override mechanism.
- **Context Handling**: The `check_survival_override` method requires raw arguments instead of `ConsumptionContext` because it runs *before* the `action_vector` (required by `ConsumptionContext`) is generated. This introduces a slight inconsistency in method signatures within `ConsumptionManager`. Future refactoring could introduce a `PreDecisionContext`.
