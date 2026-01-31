# Technical Specification: Structural Debt Refactoring

**ID:** `spec-debt-refactor-162-181-Housing`
**Author:** Gemini Scribe
**Date:** 2026-02-01
**Related Debts:** TD-162, TD-181, HousingRefactor, TD-180

---

## 1. Overview

This specification details the technical plan to address three critical architectural debts:
1.  **TD-162:** Decompose the `Household` "God Class" to improve maintainability and adhere to the Single Responsibility Principle (SRP).
2.  **TD-181:** Eliminate an abstraction leak in the household decision logic, decoupling it from the market's implementation details.
3.  **HousingRefactor:** Re-integrate orphaned housing and mortgage logic into a robust, decoupled transaction handling system.

This refactoring is a prerequisite for future development in the economic and agent behavior domains, aiming to stabilize the core simulation engine.

---

## 2. (TD-162) God Class Decomposition: `Household`

### 2.1. Problem Statement

The `Household` class (`simulation/core_agents.py`) has grown to 977 lines, mixing state management, decision orchestration, and data adaptation. This violates SRP, making it fragile and difficult to test. The audit report correctly notes that its properties are heavily used across the codebase, making a naive interface change (e.g., `household.assets` -> `household.econ.assets`) prohibitively expensive.

### 2.2. Design: The Adapter Pattern

We will extract non-core responsibilities into a dedicated `HouseholdAdapter` class, leaving the `Household` class primarily as a state container and component orchestrator. The public property interface of `Household` will be preserved to avoid widespread breaking changes.

#### 2.2.1. Pseudo-Code: `HouseholdAdapter`

```python
# In: modules/household/adapter.py

class HouseholdAdapter:
    """
    Translates Household's internal state into various DTOs for external systems
    (AI/ML Engine, Analytics, etc.), decoupling them from the core agent's structure.
    """
    def __init__(self, bio_state: BioStateDTO, econ_state: EconStateDTO, social_state: SocialStateDTO):
        self._bio = bio_state
        self._econ = econ_state
        self._social = social_state
        # Store other necessary top-level fields from Household if needed
        # self.id = bio_state.id
        # self.risk_aversion = ...

    def create_household_state_dto(self) -> HouseholdStateDTO:
        """Creates the comprehensive DTO for decision-making."""
        # ... logic from the original Household.create_state_dto() ...
        # Example:
        return HouseholdStateDTO(
            id=self._bio.id,
            assets=self._econ.assets,
            inventory=self._econ.inventory.copy(),
            needs=self._bio.needs.copy(),
            # ... and so on
        )

    def get_ai_learning_data(self) -> Dict[str, Any]:
        """Creates the flattened dictionary for the AI learning updates."""
        # ... logic from the original Household.get_agent_data() ...
        # Example:
        return {
            "assets": self._econ.assets,
            "needs": self._bio.needs.copy(),
            "is_employed": self._econ.is_employed,
            # ... and so on
        }

```

#### 2.2.2. Refactoring `Household`

The `Household` class will be modified as follows:

1.  **Remove Methods:** The `create_state_dto` and `get_agent_data` methods will be removed.
2.  **Instantiate Adapter:** In methods that require these DTOs (like `make_decision` and `update_learning`), an adapter will be instantiated on-the-fly.

```python
# In: simulation/core_agents.py (modified Household class)

class Household(BaseAgent, ILearningAgent):
    # ... existing __init__ and properties ...

    def _get_adapter(self) -> "HouseholdAdapter":
        """Factory method to create an adapter for the current state."""
        # Lazily import to avoid circular dependencies if adapter needs Household
        from modules.household.adapter import HouseholdAdapter
        return HouseholdAdapter(self._bio_state, self._econ_state, self._social_state)

    @override
    def make_decision(self, ...):
        # ...
        # 1. Prepare DTOs via Adapter
        adapter = self._get_adapter()
        state_dto = adapter.create_household_state_dto()
        # ... rest of the method uses state_dto
```

### 2.3. Verification Plan

-   **Unit Tests:** All unit tests that previously called `household.create_state_dto()` or `household.get_agent_data()` will be refactored to use `HouseholdAdapter(household._bio_state, ...).create_household_state_dto()`.
-   **Assertion Logic:** Assertions against the `Household` object's state should remain valid as the property interface is unchanged.
-   **`test_firm_decision_engine_new.py` (TD-180):** This large test file will require careful refactoring. A dedicated test fixture could be created to provide a pre-configured `HouseholdAdapter` instance to simplify test setups.

### 2.4. Risk & Impact Audit (TD-162)

-   **Risk - Cascading Interface Breakage**: **Mitigated.** By preserving the public property interface (`.assets`, `.is_employed`) and using the Adapter pattern for data transformation logic, we avoid a codebase-wide refactoring effort. The change is contained within the `Household` class and its direct callers that need the complex DTOs.
-   **Risk - Test Suite Failure**: **High but Manageable.** Test breakage is expected but will be localized to tests that specifically used the now-extracted adapter methods. The fix is straightforward: instantiate the adapter in the test.
-   **Constraint - Interface Contract Adherence**: **Met.** The `@override` properties for `BaseAgent` and `ILearningAgent` are preserved in their current form, delegating to internal state DTOs.

---

## 3. (TD-181) Abstraction Leak: `DecisionUnit`

### 3.1. Problem Statement

The `DecisionUnit` directly accesses the `sell_orders` attribute of a raw `OrderBookMarket` object, creating a tight coupling between decision logic and market implementation. This violates abstraction principles and makes the system brittle.

### 3.2. Design: Enriching `MarketSnapshotDTO`

The fix is to provide the necessary information through the existing DTO layer.

#### 3.2.1. API Change: `MarketSnapshotDTO`

We will add a dedicated structure to the `MarketSnapshotDTO` (definition assumed to be in `simulation/dtos.py` or similar).

```python
# In: simulation/dtos.py (or equivalent DTO file)

class HousingMarketInfo(TypedDict):
    best_ask_price: Optional[float]
    best_bid_price: Optional[float]
    available_units: int
    total_sell_orders: int

class MarketSnapshotDTO(TypedDict):
    # ... existing fields
    housing_market_info: Optional[HousingMarketInfo]
```

#### 3.2.2. Pseudo-Code: Orchestration Layer (`phases.py`)

The orchestration layer must be updated to populate this new DTO.

```python
# In: simulation/orchestration/phases.py (conceptual change)

def prepare_market_snapshot(...) -> MarketSnapshotDTO:
    # ... existing logic to build the snapshot ...

    housing_market = markets.get("housing")
    housing_info = None
    if housing_market and hasattr(housing_market, "get_market_snapshot_info"): # Use a dedicated method
        # The market itself should be responsible for providing its summary
        housing_info = housing_market.get_market_snapshot_info()
    
    snapshot["housing_market_info"] = housing_info
    return snapshot
```

#### 3.2.3. Refactoring `DecisionUnit`

The decision logic will now safely access the DTO.

```python
# In: modules/household/decision_unit.py (modified)

# ... inside make_decision method
housing_info = context.market_snapshot.get("housing_market_info")
if housing_info and housing_info["available_units"] > 0:
    target_price = housing_info["best_ask_price"]
    # ... logic now uses target_price instead of iterating raw orders
```

### 3.3. Verification Plan

-   **Unit Test:** Create a new unit test for `DecisionUnit` that passes a mock `DecisionContext` containing a `MarketSnapshotDTO` with `housing_market_info`.
-   **Test Cases:**
    1.  Verify that if `housing_market_info` is `None`, no housing purchase is attempted.
    2.  Verify that if `available_units` is 0, no purchase is attempted.
    3.  Verify that the agent uses `best_ask_price` from the DTO to make its purchasing decision.

### 3.4. Risk & Impact Audit (TD-181)

-   **Risk - External Orchestration Dependency**: **Addressed.** The specification explicitly includes the necessary change in the orchestration layer (`phases.py`) to populate the DTO.
-   **Constraint - DTO Population**: **Met.** The design provides a clear plan for how and where the `MarketSnapshotDTO` is enriched.

---

## 4. (HousingRefactor) System Decoupling: `HousingTransactionHandler`

### 4.1. Problem Statement

The existing `HousingSystem` (`simulation/systems/housing_system.py`) is tightly coupled to the main `simulation` object, directly accessing its agent/market lists and invoking the `settlement_system`. This monolithic approach prevents modularity and proper transaction management.

### 4.2. Design: Command & Handler Pattern

We will introduce a `TransactionManager` that routes transactional **Commands** (DTOs) to registered **Handlers**. This decouples the "intent" (e.g., pay rent) from the "execution" (creating ledger entries).

#### 4.2.1. API Definitions (`modules/finance/api.py`)

This new API file will define the core interfaces for the new transaction system. (See `api.py` section below for full code).

-   `TransactionCommand` (Base TypedDict)
-   `RentPaymentCommand`, `MortgagePaymentCommand`, `ForeclosureCommand` (Specific Command DTOs)
-   `ITransactionHandler` (Interface with an `execute` method)
-   `ITransactionManager` (Interface with `register_handler` and `submit` methods)

#### 4.2.2. `HousingTransactionHandler` Implementation

This handler will be responsible for processing housing-related commands.

```python
# In: modules/finance/handlers/housing_handler.py

class HousingTransactionHandler(ITransactionHandler):
    def execute(self, command: TransactionCommand, sim_state: "SimulationState") -> List[TransactionRecord]:
        if isinstance(command, RentPaymentCommand):
            # Logic to create a TransactionRecord for rent payment
            # 1. Get tenant and owner from sim_state.agents
            # 2. Check if tenant has enough assets
            # 3. Return a TransactionRecord DTO
            # NO direct asset modification here.
            ...
        elif isinstance(command, ForeclosureCommand):
            # Logic to handle foreclosure
            # 1. Create TransactionRecord for asset transfer (property)
            # 2. Return a list of records/events (e.g., EvictionEvent) for other systems to process
            ...
        return []
```

#### 4.2.3. Refactoring `HousingSystem`

`HousingSystem` will no longer perform transfers. It will only generate and submit commands.

```python
# In: simulation/systems/housing_system.py (modified)

class HousingSystem:
    # ...
    def process_housing(self, simulation: "Simulation"):
        tx_manager = simulation.transaction_manager # Get manager instance

        # ... logic to iterate units ...
        # B. Rent Collection
        if tenant and owner and tenant.assets >= rent:
            command = RentPaymentCommand(
                tenant_id=tenant.id,
                owner_id=owner.id,
                amount=rent,
                unit_id=unit.id,
                tick=simulation.time
            )
            tx_manager.submit(command)
        else:
            # Eviction logic remains here for now, as it's a direct state change,
            # but could be moved to an 'AgentLifecycleSystem'.
            ...
```

### 4.3. Verification Plan

-   **Handler Unit Tests:** Test `HousingTransactionHandler` by passing it each command type and a mock simulation state. Verify that it returns the correct `TransactionRecord` DTOs without mutating the input state.
-   **Manager Integration Test:** Test the `TransactionManager` by registering the `HousingTransactionHandler` and submitting a `RentPaymentCommand`. Verify the command is correctly routed to the handler.
-   **End-to-End Test:** A full simulation run should show that rent is correctly deducted and transferred, which will be observable in agent asset logs.

### 4.4. Risk & Impact Audit (HousingRefactor)

-   **Risk - Undefined Core API**: **Mitigated.** This specification defines the necessary APIs (`ITransactionManager`, `ITransactionHandler`, Command DTOs) to build upon.
-   **Constraint - Decoupling State from Transactions**: **Met.** The design strictly enforces that handlers do not mutate state. They produce `TransactionRecord` DTOs, which are then applied atomically by a separate settlement system. This respects SRP and improves system integrity.

---

## 5. Mandatory Reporting: Jules' Insights

A new file will be created by the implementing agent (`Jules`) to record observations during this task.

-   **Path:** `communications/insights/refactor-structural-debt-162.md`
-   **Content:** The file will document any unforeseen complexities, newly discovered technical debt, or suggestions for future improvements related to agent composition, transaction handling, or the testing framework. This includes noting any other areas of the code that were tightly coupled to the old `Household` implementation.

---
---

# API Definitions

## `modules/household/api.py`

```python
from typing import Protocol, Dict, Any
from .dtos import HouseholdStateDTO, BioStateDTO, EconStateDTO, SocialStateDTO

class IHouseholdAdapter(Protocol):
    """
    Defines the contract for an adapter that translates a Household's internal
    state into various DTOs for external system consumption.
    """

    def __init__(self, bio_state: BioStateDTO, econ_state: EconStateDTO, social_state: SocialStateDTO):
        ...

    def create_household_state_dto(self) -> HouseholdStateDTO:
        """Creates the comprehensive DTO for decision-making."""
        ...

    def get_ai_learning_data(self) -> Dict[str, Any]:
        """Creates the flattened dictionary for the AI learning updates."""
        ...

```

## `modules/finance/api.py`

```python
from typing import Protocol, List, Literal, TypedDict, Any, Type

# Forward reference for simulation state object to avoid circular imports
# In a real scenario, a more generic 'WorldState' DTO would be better.
if "TYPE_CHECKING":
    from simulation.engine import Simulation

# --- Command DTOs ---

class TransactionCommand(TypedDict):
    """Base for all transactional commands."""
    command_type: str
    tick: int

class RentPaymentCommand(TransactionCommand):
    command_type: Literal["RENT_PAYMENT"]
    tenant_id: int
    owner_id: int
    amount: float
    unit_id: int

class MortgagePaymentCommand(TransactionCommand):
    command_type: Literal["MORTGAGE_PAYMENT"]
    borrower_id: int
    loan_id: int
    amount: float

class ForeclosureCommand(TransactionCommand):
    command_type: Literal["FORECLOSURE"]
    loan_id: int
    unit_id: int
    owner_id: int


# --- Handler and Manager Interfaces ---

class ITransactionHandler(Protocol):
    """
    A handler processes a specific type of transaction command.
    It is stateless and produces a list of transaction records.
    """
    def execute(self, command: TransactionCommand, sim_state: "Simulation") -> List[Any]:
        """
        Processes the command against the simulation state and returns
        a list of resulting TransactionRecord DTOs or other events.
        DOES NOT mutate state directly.
        """
        ...

class ITransactionManager(Protocol):
    """
    Manages the registration of handlers and submission of commands.
    """
    def register_handler(self, command_type: str, handler: ITransactionHandler) -> None:
        """Registers a handler for a given command type."""
        ...

    def submit(self, command: TransactionCommand) -> None:
        """Submits a command to be processed by its registered handler."""
        ...

```
