# Implementation Specification: Remediation TD-116, TD-117, TD-118

This document provides the detailed implementation plan to resolve critical technical debt items related to economic integrity, structural purity, and execution sequence violations.

---

## 1. [TD-116] Economic Integrity: Inheritance Distribution

### 1.1. Objective
Eliminate floating-point precision errors ("Ghost Money") during inheritance by ensuring the sum of distributed assets exactly equals the total assets of the deceased agent. This will be achieved by using integer-based calculations for asset division and assigning the remainder to the last heir.

### 1.2. Target File
- `simulation/systems/transaction_processor.py`

### 1.3. Implementation Steps

The logic for the `inheritance_distribution` transaction type within `TransactionProcessor.execute` must be modified. The current implementation uses simple division, which is prone to floating-point inaccuracies.

**Location:** `TransactionProcessor.execute` method, `elif tx.transaction_type == "inheritance_distribution":` block.

**Pseudocode:**
1.  Get the list of heir IDs and the total cash from the deceased agent (`buyer`).
2.  If there are heirs and cash to distribute:
3.  Import the `math` module.
4.  Calculate the `base_amount` for each heir by flooring the result of `(total_cash / number_of_heirs)` to two decimal places.
5.  Initialize a `total_distributed` counter to zero.
6.  Loop through all heirs **except the last one**:
7.  Transfer the `base_amount` to the current heir.
8.  Add the `base_amount` to `total_distributed`.
9.  For the **last heir**:
10. Calculate the `remaining_amount` as `total_cash - total_distributed`.
11. Transfer the `remaining_amount` to the last heir.

**Code Modification:**
```python
# simulation/systems/transaction_processor.py

# ... inside execute method ...
            elif tx.transaction_type == "inheritance_distribution":
                heir_ids = tx.metadata.get("heir_ids", []) if tx.metadata else []
                total_cash = buyer.assets
                if total_cash > 0 and heir_ids:
                    # --- START TD-116 MODIFICATION ---
                    import math
                    count = len(heir_ids)
                    # Calculate amount per heir, avoiding float precision issues
                    base_amount = math.floor((total_cash / count) * 100) / 100.0
                    
                    distributed_sum = 0.0
                    
                    # Distribute to all but the last heir
                    for i in range(count - 1):
                        heir = agents.get(heir_ids[i])
                        if heir and settlement:
                            if settlement.transfer(buyer, heir, base_amount, "inheritance_part"):
                                distributed_sum += base_amount
                    
                    # Last heir gets the remainder to ensure zero-sum
                    last_heir = agents.get(heir_ids[-1])
                    if last_heir and settlement:
                        remaining_amount = total_cash - distributed_sum
                        settlement.transfer(buyer, last_heir, remaining_amount, "inheritance_final")

                    success = True # Assume success for this block
                    # --- END TD-116 MODIFICATION ---
```

### 1.4. Verification Plan
1.  **Zero-Sum Test**: Execute the `tests/physics/test_money_supply.py` test suite. The test must pass with no delta greater than `1e-9` after running a simulation scenario that includes agent deaths and inheritance.
2.  **Manual Verification**: Add logging within the modified block to print `total_cash`, `base_amount`, `distributed_sum`, and `remaining_amount` to confirm the logic is executing correctly.

---

## 2. [TD-117] Structural Purity: DTO-Only Decisions

### 2.1. Objective
Enforce architectural purity by preventing agent decision engines from accessing live `Market` and `Government` objects. All environmental information must be passed via pure-data Data Transfer Objects (DTOs).

### 2.2. Target Files
- `simulation/dtos/api.py` (DTO definitions)
- `simulation/tick_scheduler.py` (DTO creation)
- `simulation/core_agents.py` (Signature and `DecisionContext` update)
- `simulation/firms.py` (Signature and `DecisionContext` update)
- All `BaseDecisionEngine` implementations (to use new DTOs).

### 2.3. Implementation Steps

#### Step 1: Define New DTOs in `simulation/dtos/api.py`
The following DTOs will be added to `simulation/dtos/api.py`.

```python
# In simulation/dtos/api.py

from simulation.models import Order # Add this import

# ... other imports

# ==============================================================================
# TD-117: Structural Purity DTOs
# ==============================================================================

@dataclass
class MarketSnapshotDTO:
    """A pure-data snapshot of the state of all markets at a point in time."""
    prices: Dict[str, float]
    volumes: Dict[str, float]
    asks: Dict[str, List[Order]] # For seller selection logic
    # Add other aggregated market data as needed by decision engines
    # Example:
    # best_bids: Dict[str, float]
    # avg_wage: float

@dataclass
class GovernmentPolicyDTO:
    """A pure-data snapshot of current government policies affecting agent decisions."""
    income_tax_rate: float
    sales_tax_rate: float
    corporate_tax_rate: float
    base_interest_rate: float
    # Add other policy data as needed, e.g., welfare amounts, subsidies
```

#### Step 2: Modify `DecisionContext` in `simulation/dtos/api.py`
The `DecisionContext` DTO will be updated to use the new DTOs, removing the direct link to live objects.

```python
# In simulation/dtos/api.py, update DecisionContext

@dataclass
class DecisionContext:
    """
    A pure data container for decision-making.
    Direct agent instance access is strictly forbidden (Enforced by Purity Gate).
    TD-117 CHANGE: Replaced live objects with DTOs.
    """
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int

    # State DTO representing the agent's current condition
    state: Union[HouseholdStateDTO, FirmStateDTO]

    # Static configuration values relevant to the agent type
    config: Union[HouseholdConfigDTO, FirmConfigDTO]

    # DTO-based context
    market_snapshot: MarketSnapshotDTO
    government_policy: GovernmentPolicyDTO

    # Legacy systems passed through - to be phased out
    reflux_system: Optional[Any] = None
    stress_scenario_config: Optional[StressScenarioConfig] = None
```

#### Step 3: Update `TickScheduler` to Create DTOs
In `_phase_decisions`, before calling `agent.make_decision`, the scheduler must now create the `MarketSnapshotDTO` and `GovernmentPolicyDTO`.

**Location:** `simulation/tick_scheduler.py` -> `_phase_decisions`

**Pseudocode:**
1.  Initialize empty dictionaries for prices, volumes, and asks.
2.  Iterate through each `market` in `state.markets`:
3.  Get average price, volume, and all ask orders for each good.
4.  Populate the dictionaries.
5.  Create `MarketSnapshotDTO` instance with the aggregated data.
6.  Create `GovernmentPolicyDTO` instance by accessing properties from `state.government` and `state.central_bank`.
7.  Pass these new DTOs to the `agent.make_decision` calls.

#### Step 4: Update Agent `make_decision` Signatures
The signatures in `Household` and `Firm` must be changed. They will no longer accept `markets` and `government` directly.

**Location:** `simulation/core_agents.py` and `simulation/firms.py`

**Before:**
```python
def make_decision(self, markets: Dict[str, "Market"], ..., government: Optional[Any] = None, ...)
```

**After:**
```python
# The method will now receive the DTOs created by the TickScheduler
def make_decision(self, market_snapshot: MarketSnapshotDTO, government_policy: GovernmentPolicyDTO, goods_data: List[Dict[str, Any]], ...)
```
Inside the `make_decision` method, the instantiation of `DecisionContext` must be updated to use these new DTOs.

### 2.4. Verification Plan
1.  **Purity Audit (Static)**: After changes, run a `grep` or project-wide search to ensure no decision engine (`/decisions` or `/ai`) imports or accesses `simulation.core_markets.Market` or `simulation.agents.government.Government`. All access must be through the `DecisionContext` DTOs.
2.  **Functional Test**: Run the full test suite. Key tests in `tests/integration/` must pass, as this change affects the entire decision-making pipeline.
3.  **Data Validation**: Add logging in a decision engine to print the contents of the received `MarketSnapshotDTO` and `GovernmentPolicyDTO` to ensure they contain the correct, expected data.

### 2.5. 🚨 Architectural Risk
- **High (Breaking Change)**: This is a fundamental change to the `DecisionContext` API. **All** existing agent decision engine implementations will break and must be refactored to read from `context.market_snapshot` and `context.government_policy` instead of `context.markets` and `context.government`. A thorough audit of every property accessed on the old objects is required to ensure the new DTOs provide complete information.

---

## 3. [TD-118] Sacred Sequence: `CommerceSystem` Integration

### 3.1. Objective
Refactor the monolithic `CommerceSystem` to align with the 4-phase Sacred Sequence, eliminating duplicate lifecycle processing and improving logical consistency.

### 3.2. Target Files
- `simulation/systems/commerce_system.py` (Refactor methods)
- `simulation/tick_scheduler.py` (Integrate new methods into the 4 phases)
- `simulation/dtos/api.py` (Add field to `SimulationState` to pass data between phases)

### 3.3. Implementation Steps

#### Step 1: Refactor `CommerceSystem`
The existing `execute_consumption_and_leisure` method will be split.

**Location:** `simulation/systems/commerce_system.py`

**New Methods:**
```python
# simulation/systems/commerce_system.py

class CommerceSystem(ICommerceSystem):
    # ...

    def plan_consumption_and_leisure(self, context: CommerceContext) -> Dict[int, Dict[str, Any]]:
        """
        Phase 1 (Decisions): Determines desired consumption and leisure type.
        Returns a dictionary of "consumption plans" per household.
        """
        # 1. Contains the vectorized decision making logic from the old method.
        #    - breeding_planner.decide_consumption_batch(...)
        # 2. Contains the "Fast Purchase" logic, but converts it into an Order
        #    or a planned transaction instead of executing it directly.
        # 3. CRITICAL: The call to household.update_needs() MUST be removed.
        # 4. Returns a structured plan, e.g.:
        #    { household_id: {"consume_amt": X, "buy_amt": Y, "leisure_hours": Z} }
        ...
        return planned_consumptions

    def finalize_consumption_and_leisure(self, context: CommerceContext, actual_consumption: Dict[int, Dict[str, float]]):
        """
        Phase 4 (Lifecycle): Applies leisure effects based on actual consumption.
        """
        # 1. Iterates through households.
        # 2. Retrieves actual consumed items for the household from the `actual_consumption` map.
        # 3. Retrieves planned leisure hours from the context.
        # 4. Calls household.apply_leisure_effect(...) with the actual consumption data.
        # 5. Transfers parenting XP based on leisure results.
        # 6. CRITICAL: Does NOT call household.update_needs().
        ...
```

#### Step 2: Modify `SimulationState` DTO
Add a field to carry the consumption plans from Phase 1 to Phase 4.

**Location:** `simulation/dtos/api.py` -> `SimulationState`

```python
# In SimulationState DTO
@dataclass
class SimulationState:
    # ... other fields
    # TD-118 Addition: To carry planned consumption from Phase 1 to Phase 4
    planned_consumption: Optional[Dict[int, Dict[str, Any]]] = None

    def __post_init__(self):
        # ...
        if self.planned_consumption is None:
            self.planned_consumption = {}
```

#### Step 3: Integrate into `TickScheduler`
Modify `run_tick` to call the new `CommerceSystem` methods in the correct phases.

**Location:** `simulation/tick_scheduler.py`

**Pseudocode:**
1.  **During `_phase_decisions`**:
    *   After agent `make_decision` calls.
    *   Create the `CommerceContext`.
    *   Call `state.commerce_system.plan_consumption_and_leisure(context)`.
    *   Store the returned consumption plans in `sim_state.planned_consumption`.

2.  **During `_phase_transactions`**:
    *   The "Fast Purchase" logic, now converted to transactions, will be processed here naturally with all other transactions.

3.  **During `_phase_lifecycle`**:
    *   After agent lifecycle events (aging, death).
    *   Create the `CommerceContext`.
    *   Gather the *actual* consumption results for each household (e.g., from `household.current_consumption` which was updated during transaction processing).
    *   Call `state.commerce_system.finalize_consumption_and_leisure(context, actual_consumption_results)`.

4.  **Remove Old Call**: The old monolithic call `state.commerce_system.execute_consumption_and_leisure(...)` after the 4-phase sequence must be completely removed.

### 3.4. Verification Plan
1.  **Execution Trace**: Add distinct logging statements (e.g., `COMMERCE_PLAN`, `COMMERCE_FINALIZE`) to the new methods and verify from the logs that they are executed in Phase 1 and Phase 4, respectively.
2.  **No Double Processing**: Add a temporary counter or log to `BioComponent.run_lifecycle` (or the method it calls for aging). Run a simulation for 10 ticks and verify that it is called exactly 10 times per agent, not 20.
3.  **Functional Test**: Ensure that households still gain leisure utility and children still gain XP from parenting. The end-of-tick state for households should be comparable to the state before the change (allowing for minor differences due to timing).

### 3.5. 🚨 Architectural Risk
- **High (Duplicate Processing)**: As identified in the audit, the primary risk is failing to remove the `household.update_needs()` call from the old `CommerceSystem` logic. This will cause agents to age and their needs to decay twice per tick, corrupting simulation results. The refactoring must ensure `CommerceSystem` is purely responsible for commerce/leisure planning and effects, with no lifecycle side effects.
