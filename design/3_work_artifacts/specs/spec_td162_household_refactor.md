# Specification: TD-162 - Household God Class Decomposition

## 1. Problem Definition

- **ID**: TD-162
- **Description**: The `Household` class in `simulation/core_agents.py` has become a "God Class," exceeding 977 lines and violating the Single Responsibility Principle (SRP).
- **Root Cause**: Continuous feature additions have overloaded the class with multiple, distinct responsibilities including lifecycle management, economic decision-making, state access, and social behavior orchestration. The established decomposition pattern (delegating to stateless components) has not been fully applied to newer functionalities, leading to bloat.
- **Impact**:
    - **High Maintenance Overhead**: Difficult to understand, modify, and debug.
    - **Poor Testability**: The large surface area and mixed concerns make unit testing complex and brittle.
    - **Increased Risk of Regression**: Changes in one area (e.g., inventory management) can have unforeseen consequences on another (e.g., needs fulfillment).

## 2. Detailed Implementation Plan

This refactoring will strictly follow the existing architectural pattern of a Facade (`Household`) delegating to stateless Components, with state held in dedicated DTOs.

### Step 1: Introduce New Specialized Components

Create the following new stateless component classes within the `modules/household/` directory:

1.  **`modules/household/inventory_manager.py` -> `InventoryManager`**: This component will manage the household's physical possessions.
2.  **`modules/household/lifecycle_manager.py` -> `LifecycleManager`**: This component will orchestrate aging, needs decay, and death checks, centralizing logic currently split between `update_needs` and `social_component`.
3.  **`modules/household/financial_manager.py` -> `FinancialManager`**: This component will manage assets, income tracking, and financial state properties.

### Step 2: Refactor State DTOs

The state held in `BioStateDTO` and `EconStateDTO` will be reorganized for better cohesion.

- **Modify `modules/household/dtos.py`**:
    - Create a new `InventoryStateDTO` to hold inventory-related data currently in `EconStateDTO`.
    - Create a new `FinancialStateDTO` to hold asset and income data from `EconStateDTO`.

```python
# In modules/household/dtos.py

@dataclass
class InventoryStateDTO:
    inventory: Dict[str, float]
    inventory_quality: Dict[str, float]
    durable_assets: List[Dict[str, Any]]

@dataclass
class FinancialStateDTO:
    assets: float
    portfolio: Portfolio
    labor_income_this_tick: float
    capital_income_this_tick: float
    initial_assets_record: float
    credit_frozen_until_tick: int

# Modify EconStateDTO
@dataclass
class EconStateDTO:
    # Remove fields moved to InventoryStateDTO and FinancialStateDTO
    # ... (is_employed, current_wage, etc. remain)
    pass

# Modify HouseholdStateDTO (for decision context) to flatten/include these
# ...
```

The `Household` class will now hold instances of these new DTOs: `self._inventory_state: InventoryStateDTO`, `self._financial_state: FinancialStateDTO`.

### Step 3: Implement New Components and Delegate Logic

- **`InventoryManager`**:
    - Implement `add_item(state: InventoryStateDTO, item_id: str, quantity: float) -> InventoryStateDTO`.
    - Implement `remove_item(state: InventoryStateDTO, item_id: str, quantity: float) -> InventoryStateDTO`.
    - Implement `add_durable_asset(state: InventoryStateDTO, asset: Dict) -> InventoryStateDTO`.
    - **Refactor `Household`**: The methods `modify_inventory` and `add_durable_asset` will now delegate to this manager, passing and replacing the `_inventory_state` DTO.

- **`LifecycleManager`**:
    - Implement `update_needs(state: BioStateDTO, config: HouseholdConfigDTO) -> BioStateDTO`: This will contain the logic for needs decay over time.
    - Implement `check_for_death(state: BioStateDTO, needs: Dict[str, float], config: HouseholdConfigDTO) -> bool`: Checks survival conditions.
    - **Refactor `Household.update_needs`**: This method will become a simple orchestrator, calling the `LifecycleManager` and other components (`BioComponent.age_one_tick`). The core logic from `social_component.update_psychology` related to needs decay and death will move here.

- **`FinancialManager`**:
    - Implement `add_assets(state: FinancialStateDTO, amount: float) -> FinancialStateDTO`.
    - Implement `sub_assets(state: FinancialStateDTO, amount: float) -> FinancialStateDTO`.
    - Implement `record_labor_income(state: FinancialStateDTO, income: float) -> FinancialStateDTO`.
    - **Refactor `Household`**: The `_add_assets`, `_sub_assets`, and `add_labor_income` methods will delegate to this manager. The `assets` property will now get its value from `self._financial_state.assets`.

### Step 4: Update the `Household` Facade

- The `Household` `__init__` method will be updated to initialize the new state DTOs.
- Properties like `assets`, `inventory`, `durable_assets`, etc., will be re-wired to point to the correct fields in the new, more granular state DTOs.
- Methods that were refactored will be replaced with simple calls to the new components, passing the relevant state DTO and receiving the updated DTO back.

**Example: Refactored `_add_assets`**
```python
# In Household class
@override
def _add_assets(self, amount: float) -> None:
    # self._econ_state.assets += amount (Old)
    self._financial_state = self.financial_manager.add_assets(self._financial_state, amount)
    self._assets = self._financial_state.assets # Update legacy property
```

## 3. Verification Criteria

1.  **New Unit Tests for Components**:
    - `tests/modules/household/test_inventory_manager.py`: Must be created to test adding, removing, and querying inventory and durables in a pure, functional way.
    - `tests/modules/household/test_lifecycle_manager.py`: Must be created to test needs decay and death condition logic in isolation.
    - `tests/modules/household/test_financial_manager.py`: Must be created to test asset/income modifications.

2.  **No Change in Simulation Output**: A full simulation run with the same seed before and after the refactoring should produce identical results, verifying that the logic was moved correctly without behavior changes.

3.  **Code Metrics**:
    - The line count of `simulation/core_agents.py` must be significantly reduced.
    - The Cyclomatic Complexity of the `Household` class methods must decrease.

4.  **`ruff` Check**: All modified and new files must pass `ruff` checks without any new errors.
