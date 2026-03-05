# Wave 4.2: Marriage Market & Household Merger
**Mission Key**: `phase41_wave4_marriage`
**Date**: 2025-05-15

## Architectural Decisions

### 1. The "Merger" Model
The mission calls for a "Household Merger". Given the existing `Household` class structure (which represents a single agent/individual with singular `BioState` and `EconState`), a true multi-person household refactor (God Class refactor) is out of scope for this wave.

Therefore, we adopt the **"Asset Merger & Dependent Spouse"** model:
- **Marriage Event**: Two eligible agents (Households) are matched.
- **Role Assignment**: One agent becomes the **Head** (Primary), the other becomes the **Spouse** (Secondary). Selection can be random or based on income/wealth.
- **Asset Transfer**: All assets from the Secondary agent are transferred to the Primary agent.
    - **Cash**: Transferred via `ISettlementSystem` (Zero-Sum Integrity).
    - **Portfolio**: Merged into Primary's portfolio using `Portfolio.merge()`.
    - **Inventory**: Items moved to Primary's inventory.
    - **Real Estate**: Ownership transferred to Primary.
- **Dependent Transfer**: Any children of the Secondary agent are added to the Primary agent's `children_ids`.
- **State Change**:
    - Primary agent records `spouse_id = Secondary.id`.
    - Secondary agent records `spouse_id = Primary.id` but is set to `is_active = False`.
    - Secondary agent effectively "retires" from independent economic activity but remains in the simulation as a linked entity (for potential future use or history).

### 2. Needs Scaling (The "Two-Mouth" Problem)
Since the merged household is represented by a single `Household` agent (the Head), the simulation would default to single-person consumption. To correct this:
- We modify `NeedsEngine` to detect if a `spouse_id` is present.
- We calculate a `household_size` factor (1 + Spouse + Children).
- We scale the `base_growth` of needs (specifically `survival`/food) by this factor.
- This ensures the merged household consumes more resources, maintaining economic demand balance.

### 3. Implementation Details
- **MarriageSystem**: A new system in `simulation/systems/lifecycle/marriage_system.py` handles matchmaking and execution.
- **Settlement**: Uses `ISettlementSystem` for cash transfers to ensure auditability.
- **Housing**: Updates `RealEstateUnit.owner_id` directly and synchronizes agent `owned_properties` lists.
- **Lifecycle**: Integrated into `AgentLifecycleManager` to run every tick (or periodically).

## Regression Risks & Mitigation
- **Labor Supply Shock**: Merging households removes one active worker from the labor market. This is an accepted economic consequence (simulating a single-earner household model for now). Future waves may implement "Dual Income" logic by aggregating labor offers.
- **Needs Imbalance**: If scaling is off, households might starve or hoard. We test `NeedsEngine` scaling to ensure reasonable growth rates.
- **Asset Loss**: If transfers fail, assets disappear. We use transactional logic (or explicit sequential steps with checks) to prevent leaks.
