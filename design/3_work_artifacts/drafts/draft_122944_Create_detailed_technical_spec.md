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

---
# Specification: TD-160 & TD-187 - Atomic Estate and Severance Settlement

## 1. Problem Definition

- **ID**: TD-160, TD-187
- **Description**: The inheritance (`InheritanceManager`) and severance pay processes are not atomic. They generate a sequence of discrete `Transaction` objects, which can lead to partial execution if one step fails.
- **Root Cause**: The system lacks a mechanism to group related financial operations into a single, all-or-nothing transaction. The `InheritanceManager`'s direct, sequential creation of `Transaction` objects for liquidation, taxation, and distribution is an implicit, fragile attempt at a multi-step process.
- **Impact**:
    - **TD-160 (Money Leaks)**: If an estate is partially liquidated but the tax or distribution transaction fails, the assets of the deceased agent are left in a corrupted, intermediate state, effectively destroying wealth from the simulation (a "money leak").
    - **TD-187 (Race Condition)**: During firm liquidation, a timing issue between calculating available funds and paying severance can lead to over-withdrawal if assets are otherwise claimed, breaking the simulation's zero-sum integrity.

## 2. Detailed Implementation Plan

This refactoring will replace the sequential transaction generation with a Saga pattern, orchestrated by a new `SettlementSystem` that guarantees atomicity.

### Step 1: Define the Settlement Saga DTOs

In a new file, `simulation/dtos/settlement_dtos.py`, define the data contracts for our sagas.

```python
# simulation/dtos/settlement_dtos.py
from typing import List, Dict, Any, Literal
from dataclasses import dataclass, field

@dataclass
class EstateValuationDTO:
    """A read-only snapshot of the deceased's wealth."""
    cash: float
    real_estate_value: float
    stock_value: float
    total_wealth: float
    tax_due: float
    stock_holdings: Dict[int, float] # {firm_id: quantity}
    property_holdings: List[int] # [property_id]

@dataclass
class EstateSettlementSaga:
    """The complete, atomic unit of work for settling an estate."""
    saga_type: Literal["ESTATE_SETTLEMENT"] = "ESTATE_SETTLEMENT"
    deceased_id: int
    heir_ids: List[int]
    government_id: int
    valuation: EstateValuationDTO
    current_tick: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

### Step 2: Refactor `InheritanceManager`

The `InheritanceManager` will be simplified into a read-only valuation and saga creation service. It will no longer create `Transaction` objects.

- **Modify `simulation/systems/inheritance_manager.py`**:
    - The `process_death` method signature will change to `def process_death(...) -> EstateSettlementSaga:`.
    - The method will perform all the valuation steps as before (calculating cash, stock value, RE value, tax).
    - Instead of creating a list of `Transaction`s, it will populate and return a single `EstateSettlementSaga` object.
    - It will no longer need write-access to any part of the simulation state.

### Step 3: Create the `SettlementSystem` and Saga Handler

A new system will be responsible for executing these sagas atomically.

- **Create `simulation/systems/settlement_system.py`**:
    - The `SettlementSystem` will have a method `submit_saga(saga: EstateSettlementSaga)`.
    - Internally, it will have a registry of handlers: `self.handlers = {"ESTATE_SETTLEMENT": self.handle_estate_settlement}`.
    - The `execute` method of the system will process its queue of submitted sagas.

- **Implement the Saga Handler (`handle_estate_settlement`)**:
    - This method receives the `EstateSettlementSaga` DTO.
    - It will perform the settlement as a **single, ACID-compliant operation**.
    - **Execution Steps & Compensation (Rollback) Logic**:
        1.  **BEGIN TRANSACTION** (Conceptually).
        2.  **Freeze Deceased's Accounts**: No further direct debits/credits allowed.
        3.  **Liquidate Assets (if cash < tax)**:
            - **Action**: Debit stocks/property from deceased portfolio, credit to government portfolio.
            - **Action**: Credit deceased's cash account with sale value.
            - **Compensation**: Reverse the transfers.
        4.  **Pay Inheritance Tax**:
            - **Action**: Debit `tax_due` from deceased's cash, credit government cash.
            - **Compensation**: Reverse the transfer. If this step fails, **the entire saga rolls back**.
        5.  **Distribute Inheritance / Escheat**:
            - **Action (Heirs)**: Debit remaining cash from deceased, credit to heirs' accounts (split evenly).
            - **Action (Escheat)**: Debit all remaining assets (cash, stocks, property if not liquidated) from deceased, credit to government.
            - **Compensation**: Reverse the transfers.
        6.  **COMMIT TRANSACTION** (Conceptually). Mark saga as complete.

### Step 4: Integrate `SettlementSystem` into the Simulation Loop

- In `WorldState`, initialize `self.settlement_system = SettlementSystem(...)`.
- The phase responsible for lifecycle/death (e.g., `Phase_Bankruptcy`) will now:
    1.  Call `InheritanceManager.process_death()` for each deceased agent.
    2.  Receive the `EstateSettlementSaga` object.
    3.  Submit it to `world_state.settlement_system`.
- A new phase, `Phase_Settlement`, will be added to `TickOrchestrator`'s phase list, running after decisions but before transaction processing, to execute the sagas.

## 3. Verification Criteria

1.  **New Unit Tests for `SettlementSystem`**:
    - `tests/systems/test_settlement_system.py`:
        - Test successful inheritance with and without liquidation.
        - Test successful escheatment.
        - **Crucially, test the rollback mechanism**: Create a scenario where the deceased has valuable assets but not enough cash is raised during liquidation to pay the full tax. Verify that the saga fails and the assets (stocks, properties) are returned to the deceased's (frozen) portfolio, and no cash has been transferred to the government.

2.  **Zero-Sum Conservation Test**:
    - An integration test will be written that tracks total money supply and total assets (stocks, properties) in the simulation.
    - It will trigger an inheritance event and assert that the total value of all assets and money in the simulation remains constant before and after the `SettlementSystem` runs (i.e., assets are only transferred, not created or destroyed).

3.  **Refactoring Verification**:
    - The `InheritanceManager.process_death` method should no longer return a `List[Transaction]`.
    - No `Transaction` objects with `transaction_type` of `inheritance_distribution`, `escheatment`, or `asset_liquidation` should be generated anywhere outside the `SettlementSystem`.

---
# Specification: TD-192 - Transient State Synchronization Protocol

## 1. Problem Definition

- **ID**: TD-192
- **Description**: State modifications made within a tick via the transient `SimulationState` DTO may be lost and not persist back to the primary `WorldState`.
- **Root Cause**: The architecture lacks a formal, enforced protocol for synchronizing state from the transient DTO back to the persistent state object at the end of a processing phase. Synchronization relies on developers remembering to modify collection objects *in-place* or manually adding sync logic to `TickOrchestrator`, which is error-prone. The `TD-192` comment in `action_processor.py` highlights this regression risk for transient queues (`effects_queue`, `inter_tick_queue`).
- **Impact**:
    - **State Desynchronization & Lost Data**: Critical events, agent creations, or transactions queued in one phase may never be processed if the queue object is re-assigned instead of modified in-place, leading to subtle and severe simulation bugs.
    - **High Regression Risk**: Any refactoring within a phase could accidentally break the implicit sync-back contract, leading to silent failures that are difficult to trace.
    - **Architectural Brittleness**: The system's correctness depends on an unwritten convention rather than an explicit mechanism.

## 2. Detailed Implementation Plan

This plan establishes a formal, two-part protocol to guarantee state synchronization: **1. The In-Place Modification Rule** for collections, and **2. A Hub-and-Spoke Draining Mechanism** for transient queues managed by the `TickOrchestrator`.

### Step 1: Formalize the "In-Place Modification" Rule

This rule will be documented in the project's development guide (`PROTOCOL_ENGINEERING.md`).

- **Rule**: Any phase or system operating on the `SimulationState` DTO **MUST NOT** re-assign collection attributes (lists, dicts). It must only modify them in-place.
    - **Allowed**: `sim_state.households.append(...)`, `sim_state.agents.update(...)`, `sim_state.firms[:] = ...`
    - **Forbidden**: `sim_state.households = new_list_of_households`
- **Enforcement**: This is primarily a code review and developer discipline issue. A custom `ruff` lint rule could be written in the future to detect direct assignment to state DTO collections.

### Step 2: Implement a "State Drain" in `TickOrchestrator`

The `TickOrchestrator` will be the sole authority for managing the lifecycle of transient data. Instead of phases passing state to each other, they will all report back to the orchestrator's central state.

- **Modify `simulation/orchestration/tick_orchestrator.py`**:
    - The main loop in `run_tick` will be modified. After each phase executes, a new private method `_drain_and_sync_state` will be called.

```python
# In TickOrchestrator.run_tick
# ...
sim_state = self._create_simulation_state_dto(...)

for phase in self.phases:
    # 1. Execute the phase
    sim_state = phase.execute(sim_state)

    # 2. Immediately drain and sync state back to WorldState
    self._drain_and_sync_state(sim_state)

# ...
```

### Step 3: Implement the `_drain_and_sync_state` Method

This method centralizes all synchronization logic, making it explicit and reliable.

- **Create `_drain_and_sync_state(self, sim_state: SimulationState)` in `TickOrchestrator`**:

```python
# In TickOrchestrator
def _drain_and_sync_state(self, sim_state: SimulationState):
    """
    Drains transient queues from SimulationState into WorldState and syncs scalars.
    This ensures changes from a phase are immediately persisted before the next phase runs.
    """
    ws = self.world_state

    # --- Sync Scalars ---
    ws.next_agent_id = sim_state.next_agent_id

    # --- Drain Transient Queues ---
    # The core of the solution: move items from the DTO's queue to the WorldState's
    # master queue for the tick, then clear the DTO's queue so it's fresh for the next phase.

    if sim_state.effects_queue:
        ws.effects_queue.extend(sim_state.effects_queue)
        sim_state.effects_queue.clear() # Prevent double-processing

    if sim_state.inter_tick_queue:
        ws.inter_tick_queue.extend(sim_state.inter_tick_queue)
        sim_state.inter_tick_queue.clear() # Prevent double-processing

    if sim_state.transactions:
        ws.transactions.extend(sim_state.transactions)
        sim_state.transactions.clear() # Prevent double-processing

    # --- Sync mutable collections by reference (ensure no re-assignment) ---
    # This acts as a safety check. If a phase violates the rule, this will raise an error.
    if ws.agents is not sim_state.agents:
        raise RuntimeError("CRITICAL: 'agents' collection was re-assigned in a phase. Use in-place modification.")
    
    # Update the inactive agents dictionary
    ws.inactive_agents.update(sim_state.inactive_agents)
```

### Step 4: Refactor `ActionProcessor` and other systems

- The manual synchronization logic in `action_processor.py` (marked with `TD-192`) will be **removed**. The `TickOrchestrator`'s new draining mechanism makes it redundant. The `TransactionProcessor` will append to the `SimulationState`'s queues, and the orchestrator will handle the sync-back immediately after `Phase3_Transaction` completes.

## 3. Verification Criteria

1.  **New Integration Test for State Synchronization**:
    - Create a test `tests/orchestration/test_state_synchronization.py`.
    - **Test Case**:
        1.  Create a dummy `IPhaseStrategy` ("Phase A") that adds an item to `sim_state.effects_queue`.
        2.  Create another dummy `IPhaseStrategy` ("Phase B") that also adds an item to `sim_state.effects_queue`.
        3.  Run a `TickOrchestrator` with `[Phase A, Phase B]`.
        4.  **Assert**: After the tick runs, `world_state.effects_queue` must contain **both** items, demonstrating that the drain logic correctly accumulated items from both phases without loss.

2.  **New Failure Test for Re-assignment**:
    - **Test Case**:
        1.  Create a dummy phase that violates the "In-Place" rule (e.g., `sim_state.agents = []`).
        2.  Run the `TickOrchestrator` with this phase.
        3.  **Assert**: The `RuntimeError` defined in `_drain_and_sync_state` must be raised, proving the guardrail works.

3.  **Refactoring Verification**:
    - The explicit sync logic in `action_processor.py` must be removed.
    - A full simulation run with the same seed must produce identical results before and after the change, confirming that the new explicit sync mechanism correctly replicates the behavior of the old implicit one.
