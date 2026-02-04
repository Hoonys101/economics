# Technical Specification: WO-4.0 & WO-4.1 - Decoupled Household & Market Protocols

## 1. Overview & Goals

This specification addresses critical architectural risks identified in the pre-flight audit for `WO-4.0` and `WO-4.1`. The current `Household` agent acts as a "God Class" facade, creating tight coupling through circular dependencies and the use of `Any` types for system interactions.

The primary goals are:
1.  **Decouple Agent Creation**: Eliminate the circular dependency in the agent `clone` method by introducing a dedicated factory (`TD-214`).
2.  **Enforce Protocol-Driven Interactions**: Replace implicit dependencies (`Any`, `getattr`) with formal protocols (interfaces) to enable true duck typing between agents and market systems (`TD-215`).
3.  **Simplify Agent & Handler Logic**: Reduce the orchestration burden on the `Household` facade and the implementation complexity of the `HousingTransactionHandler` by relying on these new, clear contracts.
4.  **Maintain State Atomicity**: Ensure that the existing DTO-based, side-effect-free state update pattern is preserved and reinforced.

---

## 2. WO-4.0: Refactoring Household Agent (Decoupling)

### 2.1. Problem: God Class & Circular Dependencies

-   **SRP Violation**: The `Household` class and its mixins currently manage state initialization, decision orchestration, lifecycle management, and agent creation, violating the Single Responsibility Principle.
-   **Circular Dependency**: As identified in the audit, `modules/household/mixins/_reproduction.py` directly imports and instantiates `simulation.core_agents.Household`, creating a critical `core_agents` -> `mixins` -> `core_agents` import loop. This prevents subclassing and tightly couples reproduction logic to a concrete implementation.

### 2.2. Solution: Agent Factory Protocol (TD-214)

To break the circular dependency, we will introduce a new `IAgentFactory` protocol.

1.  **Protocol Definition**: An `IAgentFactory` interface will be defined in `modules/simulation/api.py`. It will have a single method, `create_household`.
2.  **Factory Implementation**: A concrete `AgentFactory` class will be implemented in the simulation's main orchestration layer (e.g., `simulation_runner.py` or a new `factories.py` module). This factory will be responsible for the complex instantiation logic currently in `Household.__init__`.
3.  **Dependency Injection**: The `AgentFactory` instance will be injected into the `Household` agent upon its creation.
4.  **Refactored `clone` Method**: The `HouseholdReproductionMixin.clone` method will no longer import `Household`. Instead, it will call the injected factory (`self.agent_factory.create_household(...)`), passing the necessary parameters for the new agent.

### 2.3. Refactored `Household` Constructor

The `Household.__init__` will be simplified. Complex, personality-based state initialization logic will be moved into the `AgentFactory`, which will prepare the state DTOs (`BioStateDTO`, `EconStateDTO`, `SocialStateDTO`) and pass them to the `Household` constructor. The constructor's role will be reduced to assigning these pre-configured states and components.

---

## 3. WO-4.1: Market Interaction Protocols (Duck Typing / TD-215)

### 3.1. Problem: Implicit, Brittle Dependencies

-   **`Any` Type**: `OrchestrationContextDTO` passes a `housing_system: Optional[Any]` object, creating a hidden, untyped dependency that is later called directly (`housing_system.initiate_purchase(...)`).
-   **`getattr` & `isinstance`**: Code is littered with `getattr(self, 'decision_engine', None)` and `isinstance(buyer, IPropertyOwner)` checks. This is "stringly-typed" and fragile, indicating a failure to code to a consistent interface. The `HousingTransactionHandler` is a prime example of this anti-pattern.

### 3.2. Solution: Formal Protocol Definitions

We will define explicit `abc.ABC` protocols for all key cross-boundary interactions. This makes dependencies explicit and testable.

1.  **`IHousingSagaInitiator`**: To be defined in `modules/market/api.py`. This protocol will be implemented by the `HousingSystem` (or equivalent orchestrator) and will expose the `initiate_purchase` method. The `DecisionUnit` will receive this protocol instead of an `Any`-typed object.
2.  **`IMortgageApplicant`**: To be defined in `modules/common/interfaces.py`. This protocol will be implemented by `Household`. It will expose read-only properties like `id`, `assets`, `current_wage`, and a method `get_borrower_profile()`. The `HousingTransactionHandler` will interact with this protocol instead of checking attributes.
3.  **`IPropertyOwner`**: To be formalized in `modules/common/interfaces.py`. This protocol will define the contract for any agent that can own real estate, with methods `add_property` and `remove_property`.

### 3.3. Refactoring `HousingTransactionHandler`

The `HousingTransactionHandler.handle` method will be refactored to consume these protocols.
-   It will accept `buyer: IMortgageApplicant` and `seller: IPropertyOwner` in its signature (or perform a safe cast at the beginning).
-   It will call `buyer.get_borrower_profile()` instead of assembling the DTO itself.
-   It will call `buyer.assets` and `seller.remove_property()` via the defined protocols, eliminating `hasattr` checks.

---

## 4. API Definitions (`api.py`)

The following code will be added to the respective API definition files.

#### `modules/simulation/api.py`
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.core_agents import Household

class IAgentFactory(ABC):
    """Protocol for creating new agents to break circular dependencies."""
    @abstractmethod
    def create_household(self, new_id: int, **kwargs: Any) -> Household:
        """Creates a new household agent instance using orchestrated logic."""
        pass
```

#### `modules/common/interfaces.py` (New & Updated)
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, TYPE_CHECKING

from modules.system.api import CurrencyCode
from modules.finance.api import BorrowerProfileDTO

if TYPE_CHECKING:
    from simulation.systems.api import TransactionContext

class IPropertyOwner(ABC):
    """Defines an entity that can own real estate properties."""
    @property
    @abstractmethod
    def owned_properties(self) -> List[int]: ...

    @abstractmethod
    def add_property(self, property_id: int) -> None: ...

    @abstractmethod
    def remove_property(self, property_id: int) -> None: ...

class IMortgageApplicant(ABC):
    """Defines an entity that can apply for a mortgage."""
    @property
    @abstractmethod
    def id(self) -> int: ...

    @property
    @abstractmethod
    def assets(self) -> Dict[CurrencyCode, float]: ...

    @property
    @abstractmethod
    def current_wage(self) -> float: ...

    @abstractmethod
    def get_borrower_profile(self, trade_value: float, context: "TransactionContext") -> BorrowerProfileDTO:
        """Assembles a borrower profile for a loan application."""
        pass

class IResident(ABC):
    """Defines an entity that can reside in a property."""
    @property
    @abstractmethod
    def residing_property_id(self) -> Optional[int]: ...
    @residing_property_id.setter
    def residing_property_id(self, value: Optional[int]) -> None: ...

    @property
    @abstractmethod
    def is_homeless(self) -> bool: ...
    @is_homeless.setter
    def is_homeless(self, value: bool) -> None: ...
```

#### `modules/market/api.py` (New)
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.housing.dtos import HousingPurchaseDecisionDTO

class IHousingSagaInitiator(ABC):
    """Protocol for a system that can orchestrate a house purchase saga."""
    @abstractmethod
    def initiate_purchase(self, decision: "HousingPurchaseDecisionDTO", buyer_id: int) -> None:
        """Initiates the saga for purchasing a house."""
        pass
```

---

## 5. Implementation Plan (Pseudo-code)

#### `modules/household/mixins/_reproduction.py`
```python
# class HouseholdReproductionMixin:
    # Add property to be injected
    # self.agent_factory: IAgentFactory

    @override
    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "Household":
        # No longer imports Household
        
        # 1. Prepare inheritance kwargs
        offspring_demo = self.bio_component.create_offspring_demographics(...)
        econ_inheritance = self.econ_component.prepare_clone_state(...)
        
        # 2. Assemble all kwargs for the factory
        factory_kwargs = {
            "initial_assets": initial_assets_from_parent,
            "personality": self._social_state.personality,
            **offspring_demo,
            **econ_inheritance,
            # ... other necessary base params
        }

        # 3. Delegate creation to the factory
        cloned_household = self.agent_factory.create_household(
            new_id=new_id,
            **factory_kwargs
        )

        return cloned_household
```

#### `modules/household/decision_unit.py`
```python
# class OrchestrationContextDTO(TypedDict):
    # ...
    # housing_system: Optional[IHousingSagaInitiator] # CHANGED from Any

# class DecisionUnit(IDecisionUnit):
    def orchestrate_economic_decisions(...):
        # ...
        housing_system = context.get("housing_system")

        # ... (Planner logic) ...
        decision = self.housing_planner.evaluate_housing_options(request)

        if decision['decision_type'] == "INITIATE_PURCHASE":
             # Protocol is checked statically, no need for hasattr
             if housing_system:
                 # Call via the protocol
                 housing_system.initiate_purchase(decision, buyer_id=household_state.id)
             else:
                 logger.warning("Housing Saga Initiator not available.")
```

#### `modules/market/handlers/housing_transaction_handler.py`
```python
# class HousingTransactionHandler:
    def handle(self, tx: Transaction, buyer: IMortgageApplicant, seller: IPropertyOwner, context: TransactionContext) -> bool:
        # 1. Validation: Types are now enforced by protocol
        if not buyer or not seller:
            return False

        # ...

        # 2. Get Borrower Profile via Protocol
        # No need to calculate income/debt here
        borrower_profile = buyer.get_borrower_profile(sale_price, context)
        
        # 3. Check Buyer Funds via Protocol
        if buyer.assets.get(DEFAULT_CURRENCY, 0.0) < down_payment:
            return False

        # ... (Saga logic continues) ...

    def _apply_housing_effects(...):
        # ...
        # Update Seller via Protocol
        seller.remove_property(unit_id)
        
        # Update Buyer via Protocol
        buyer.add_property(unit_id)

        # Auto-move-in if homeless (safe cast or check if buyer also implements IResident)
        if isinstance(buyer, IResident):
            if buyer.is_homeless:
                buyer.residing_property_id = unit_id
                buyer.is_homeless = False
```

---

## 6. Verification Plan & Mocking Strategy

-   **Unit Tests**: New unit tests will be created for `AgentFactory` to ensure it correctly initializes `Household` agents with diverse personalities and states.
-   **Protocol Conformance Tests**: For each new protocol (`IAgentFactory`, `IMortgageApplicant`, etc.), a set of tests will verify that `Household` and other concrete classes correctly implement all required methods and properties.
-   **Mocking**:
    -   In tests for `DecisionUnit`, a mock implementation of `IHousingSagaInitiator` will be injected to verify that `initiate_purchase` is called with the correct parameters, without needing a full `HousingSystem`.
    -   In tests for `HousingTransactionHandler`, mock objects implementing `IMortgageApplicant` and `IPropertyOwner` will be used to simulate different buyer/seller scenarios (e.g., low funds, existing properties).
-   **[Test] Golden Data & Fixture Update**:
    -   The existing `golden_households` fixtures remain valid.
    -   `conftest.py` will be updated to use the new `AgentFactory` to generate these fixtures, ensuring consistency with the main application's creation logic. This centralizes the instantiation process.

---

## 7. Risk & Impact Audit (Post-Refactor)

This section addresses the initial audit findings and outlines the impact of the proposed changes.

-   **[Mitigated] Critical Risk: Circular Dependency**: The introduction of the `IAgentFactory` protocol and dependency injection completely resolves the `_reproduction.py` -> `core_agents.py` import loop.
-   **[Mitigated] Critical Risk: Implicit Dependencies**: The replacement of `Any` and `getattr` with formal protocols (`IHousingSagaInitiator`, `IMortgageApplicant`) makes all system interactions explicit, typed, and statically verifiable. This is a major step towards a robust, protocol-driven architecture.
-   **[Contained] Critical Risk: `Household` God Class**: While `Household` remains a facade, its internal complexity is reduced. The creation logic is moved to a factory, and orchestration logic in `make_decision` is simplified by delegating to protocol-based components. It is no longer a "God Class" but a "Well-Managed Facade".
-   **Architectural Constraint: State Atomicity**: The proposed changes respect and reinforce the DTO-copy-on-write pattern, ensuring state updates remain atomic and free of side effects.
-   **⚠️ **New Risk**: Widespread Test Refactoring**: As noted in the audit, these changes are fundamental. A significant number of tests, particularly those that manually instantiate `Household` or mock its methods, will need to be updated to use the new factory pattern and protocols. This represents the highest cost of implementation.
-   **[Routine] Mandatory Reporting**: No changes are made to the insight logging mechanism. Components should continue to log insights, which will be aggregated by the designated process.
