# WO-4.0: Household God Class Decomposition (Mixins)

**Status**: 🟢 Ready for Implementation (PR-Chunk #1)
**Target**: `simulation/core_agents.py`
**Goal**: Address `TD-214` by decomposing the 970-line `Household` class into logical Mixins.

## 1. Scope of Work
- Create a new package `modules/household/mixins/`.
- Partition internal `Household` logic into 5 specialized mixin classes.
- Inherit `Household` from these mixins without changing its public API.

## 2. Implementation Details

### 2.1. Mixin Partitioning
Create the following files in `modules/household/mixins/`:
1.  **`_properties.py` (`HouseholdPropertiesMixin`)**: Move all `@property` getters/setters for assets, inventory, needs, age, etc.
2.  **`_lifecycle.py` (`HouseholdLifecycleMixin`)**: Move `update_needs`, `consume`, `apply_leisure_effect`.
3.  **`_financials.py` (`HouseholdFinancialsMixin`)**: Move `adjust_assets`, `modify_inventory`, `add_labor_income`.
4.  **`_reproduction.py` (`HouseholdReproductionMixin`)**: Move `clone`, `get_heir`.
5.  **`_state_access.py` (`HouseholdStateAccessMixin`)**: Implement public accessors `get_bio_state()`, `get_econ_state()`, `create_snapshot_dto()`.

### 2.2. Facade Refactoring
Update `simulation/core_agents.py`:
- Import all 5 mixins.
- Change `class Household(BaseAgent, ...):` to include all 5 mixins.
- Ensure `__init__` correctly initializes component references used by mixins.

## 3. Verification
- Run existing unit tests for `Household`.
- Verify that `HouseholdSnapshotAssembler` in `modules/household/services.py` now uses public accessors instead of `_bio_state` protected access (`TD-217`).
