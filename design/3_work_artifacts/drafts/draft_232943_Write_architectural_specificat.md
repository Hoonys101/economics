Okay, I will now create the architectural specifications for TD-271 and TD-272.

# Spec: TD-271 OrderBookMarket Interface Compliance

```markdown
# Design Spec: TD-271 OrderBookMarket Interface Compliance

## 1. Introduction

- **Purpose**: This document outlines the architectural changes required to fix the interface violation in `OrderBookMarket`, ensuring it complies with the `IMarket` protocol.
- **Scope**: The changes are limited to the `OrderBookMarket` class and the definition of its public interface in a new `modules/market/api.py` file.
- **Goal**: To enforce a clean separation between the market's internal implementation and its public contract, preventing leaky abstractions and improving maintainability.

## 2. Problem Definition (TD-271)

`OrderBookMarket` currently stores its buy and sell orders as a list of `MarketOrder`, an internal, mutable class (`List[MarketOrder]`). However, its public properties (`buy_orders`, `sell_orders`) expose this internal list directly.

This violates the `IMarket` protocol, which mandates that these properties return a `Dict[str, List[Order]]`, where `Order` is the immutable public DTO. This leaky abstraction exposes internal implementation details and creates a rigid, non-compliant contract.

## 3. Detailed Design

### 3.1. Solution: Encapsulation and On-the-Fly Conversion

The internal logic of `OrderBookMarket` will continue to use the mutable `MarketOrder` class for efficient matching. However, the public-facing properties will be refactored to hide this detail.

1.  **Rename Internal State**: The internal attributes `self.buy_orders` and `self.sell_orders` will be renamed to `self._buy_orders` and `self._sell_orders` to signify they are private.
2.  **Implement Public Properties**: New read-only properties named `buy_orders` and `sell_orders` will be created. These properties will iterate over the internal `_buy_orders` and `_sell_orders` dictionaries and convert each `MarketOrder` into its corresponding `Order` DTO before returning the result.

This ensures the class internals can be modified without breaking the public contract, and consumers of the market receive data in the expected, immutable format.

### 3.2. Pseudo-code: `OrderBookMarket` Refactoring

```python
# simulation/markets/order_book_market.py

from simulation.models import Order
from .dtos import MarketOrder # Internal DTO

class OrderBookMarket(Market):
    def __init__(self, ...):
        super().__init__(...)
        # Rename internal attributes to denote privacy
        self._buy_orders: Dict[str, List[MarketOrder]] = {}
        self._sell_orders: Dict[str, List[MarketOrder]] = {}
        # ... other attributes

    # ... existing methods using self._buy_orders and self._sell_orders ...

    @property
    def buy_orders(self) -> Dict[str, List[Order]]:
        """
        Public property that returns buy orders as a dictionary of public Order DTOs,
        complying with the IMarket interface.
        """
        public_orders: Dict[str, List[Order]] = {}
        for item_id, internal_orders in self._buy_orders.items():
            public_orders[item_id] = [
                self._convert_market_order_to_dto(order) for order in internal_orders
            ]
        return public_orders

    @property
    def sell_orders(self) -> Dict[str, List[Order]]:
        """
        Public property that returns sell orders as a dictionary of public Order DTOs,
        complying with the IMarket interface.
        """
        public_orders: Dict[str, List[Order]] = {}
        for item_id, internal_orders in self._sell_orders.items():
            public_orders[item_id] = [
                self._convert_market_order_to_dto(order) for order in internal_orders
            ]
        return public_orders

    def _convert_market_order_to_dto(self, market_order: MarketOrder) -> Order:
        """
        Converts an internal MarketOrder to the public Order DTO.
        """
        return Order(
            id=market_order.original_id,
            agent_id=market_order.agent_id,
            side=market_order.side,
            item_id=market_order.item_id,
            quantity=market_order.quantity,
            price_limit=market_order.price,
            target_agent_id=market_order.target_agent_id,
            brand_info=market_order.brand_info,
            # Add other fields as necessary to match the Order DTO
        )

```

### 3.3. API/Interface: `modules/market/api.py`

A new API file will be created to formally define the market interface.

```python
# modules/market/api.py

from typing import Protocol, Dict, List, runtime_checkable
from simulation.models import Order, Transaction

@runtime_checkable
class IMarket(Protocol):
    """
    Interface for Market objects, exposing only read-only attributes
    safe for agent consumption (Snapshot Pattern).
    """
    id: str

    @property
    def buy_orders(self) -> Dict[str, List[Order]]: ...

    @property
    def sell_orders(self) -> Dict[str, List[Order]]: ...

    @property
    def matched_transactions(self) -> List[Transaction]: ...

    def get_daily_avg_price(self) -> float: ...
    def get_daily_volume(self) -> float: ...

```

## 4. 🚨 Risk & Impact Audit

- **Test Impact (High)**: Unit tests that directly inspect the contents of `market.buy_orders` or `market.sell_orders` will fail. They are currently asserting against the `MarketOrder` class structure. These tests **must** be updated to assert against the public `Order` DTO structure.
- **Refactoring Risk (Low)**: The change is well-encapsulated within `OrderBookMarket`. As long as other system components were correctly type-hinted against `IMarket` or `Order`, they should not be affected. The risk lies entirely within tests that violated the abstraction.
- **Performance Impact (Negligible)**: The on-the-fly conversion of orders to DTOs will introduce a small overhead when the properties are accessed. This is a necessary trade-off for architectural purity and is unlikely to be a bottleneck.

## 5. Verification & Mocking Strategy

- **Golden Data**: No changes to golden data are required. This is a structural refactoring of an in-memory object.
- **Mocking Strategy**:
  - Existing tests that mock `OrderBookMarket` and its methods do not need to change.
  - New tests should mock the `IMarket` interface where possible.
  - When testing components that consume market data, the mocked `buy_orders` and `sell_orders` should return data structured as `Dict[str, List[Order]]` to align with the correct interface.

## 6. 🚨 Mandatory Reporting Verification

- **Insight Captured**: This refactoring enforces the **"Interface Segregation Principle"** and **"Encapsulation"**. The key insight is that internal mutable representations are acceptable for performance, but they must never leak through a public contract. The contract must be stable and abstract.
- **Report Location**: `communications/insights/TD-271-Interface-Purity.md` will be created to document this principle for future architectural reviews.

```

# Spec: TD-272 PersistenceManager Domain Purity

```markdown
# Design Spec: TD-272 PersistenceManager Domain Purity

## 1. Introduction

- **Purpose**: This document specifies the refactoring of `PersistenceManager` to resolve critical SRP violations and high coupling, transforming it into a pure, DTO-driven service.
- **Scope**: The refactoring involves `PersistenceManager`, the simulation `Engine`, and the creation of a new `AnalyticsSystem` responsible for data aggregation.
- **Goal**: To decouple the persistence layer from the domain layer, making the system more modular, testable, and easier to maintain. `PersistenceManager` should know nothing about `Household` or `Firm` agents.

## 2. Problem Definition (TD-272)

`PersistenceManager` is currently a "God Class" that:
1.  **Violates SRP**: It has two responsibilities: data aggregation (business logic) and data buffering/flushing (persistence logic).
2.  **Is Highly Coupled**: It directly iterates through live `Household` and `Firm` objects, accessing their internal attributes (e.g., `agent.hr.employees`, `agent.needs`). Any change to these domain objects risks breaking the persistence layer.
3.  **Is Untestable in Isolation**: Testing `PersistenceManager` requires mocking complex, live agent objects, making unit tests brittle and difficult to write.

## 3. Detailed Design

### 3.1. Solution: Decouple via a Dedicated Analytics System

The core solution is to introduce a new system, `AnalyticsSystem`, which will take over the responsibility of data aggregation. The workflow will be as follows:

1.  **`AnalyticsSystem` (New)**: This stateless system will be called by the main simulation loop. It will receive the list of active agents and transactions. Its sole job is to iterate through them, perform all necessary calculations (e.g., total income, unemployment), and produce a set of immutable DTOs (`AgentStateData`, `EconomicIndicatorData`).
2.  **`PersistenceManager` (Refactored)**: It will be stripped of all aggregation logic. Its `buffer_tick_state` method will be replaced with specific, DTO-based buffering methods (e.g., `buffer_agent_states`, `buffer_economic_indicators`). It will become a simple, dumb receiver of DTOs.
3.  **`Simulation` Engine (Orchestrator)**: The main engine will orchestrate this flow. After the tick's primary logic is complete, it will:
    a. Call `AnalyticsSystem` to generate the tick's data DTOs.
    b. Pass these DTOs to the `PersistenceManager` for buffering.

### 3.2. Pseudo-code: New Architecture

```python
# modules/analytics/analytics_system.py (New File)

class AnalyticsSystem:
    """
    Stateless system responsible for calculating and assembling
    all data DTOs for persistence.
    """
    def generate_tick_data(
        self, simulation: "Simulation", transactions: List["Transaction"]
    ) -> Tuple[List[AgentStateData], List[TransactionData], EconomicIndicatorData]:

        agent_states = []
        # 1. Create AgentStateData DTOs from agents
        for agent in simulation.agents.values():
            if isinstance(agent, Household):
                dto = self._create_household_dto(agent, simulation.time, ...)
                agent_states.append(dto)
            elif isinstance(agent, Firm):
                dto = self._create_firm_dto(agent, simulation.time, ...)
                agent_states.append(dto)

        # 2. Create TransactionData DTOs
        transaction_dtos = [
            self._create_transaction_dto(tx, simulation.time, ...) for tx in transactions
        ]

        # 3. Aggregate and create EconomicIndicatorData DTO
        # ... calculation logic for unemployment, avg_wage, etc. ...
        indicator_dto = EconomicIndicatorData(...)

        return agent_states, transaction_dtos, indicator_dto

    # Helper methods like _create_household_dto, _create_firm_dto...

# simulation/systems/persistence_manager.py (Refactored)

class PersistenceManager:
    def __init__(self, ...):
        # ... buffers remain the same ...

    # REMOVED: buffer_tick_state(self, simulation, transactions)

    def buffer_data(
        self,
        agent_states: List[AgentStateData],
        transactions: List[TransactionData],
        indicators: List[EconomicIndicatorData] # Now a list
    ):
        """Buffers pre-aggregated DTOs."""
        if agent_states:
            self.agent_state_buffer.extend(agent_states)
        if transactions:
            self.transaction_buffer.extend(transactions)
        if indicators:
            self.economic_indicator_buffer.extend(indicators)

    def flush_buffers(self, current_tick: int):
        # ... flush logic remains the same ...

# simulation/engine.py (Orchestration Example)

class Simulation:
    def _run_tick(self):
        # ... main simulation logic produces 'transactions' ...

        # After tick logic, before next tick starts:
        # 1. Analytics system generates all DTOs
        agent_dtos, tx_dtos, indicator_dto = self.analytics_system.generate_tick_data(
            self, transactions
        )

        # 2. Persistence manager buffers the DTOs
        self.persistence_manager.buffer_data(
            agent_states=agent_dtos,
            transactions=tx_dtos,
            indicators=[indicator_dto] # Pass as list
        )

        # 3. Flush periodically
        if self.time % self.config.DB_FLUSH_INTERVAL == 0:
            self.persistence_manager.flush_buffers(self.time)

```

### 3.3. API/Interface: `modules/system/api.py` (Updated)

```python
# modules/system/api.py

from typing import Protocol, List
from simulation.dtos import (
    AgentStateData,
    TransactionData,
    EconomicIndicatorData,
)

class IPersistenceManager(Protocol):
    """
    A pure DTO-driven interface for buffering and persisting simulation state.
    """
    def buffer_data(
        self,
        agent_states: List[AgentStateData],
        transactions: List[TransactionData],
        indicators: List[EconomicIndicatorData]
    ) -> None: ...

    def flush_buffers(self, current_tick: int) -> None: ...

# (Optional but recommended)
# modules/analytics/api.py
class IAnalyticsSystem(Protocol):
    def generate_tick_data(
        self, simulation: "Simulation", transactions: List["Transaction"]
    ) -> Tuple[List[AgentStateData], List[TransactionData], EconomicIndicatorData]:
        ...
```

## 4. 🚨 Risk & Impact Audit

- **Test Impact (Critical)**: All existing tests for `PersistenceManager` are now invalid. They **must be rewritten** from scratch. Instead of mocking live agents, tests will now instantiate and pass lists of `AgentStateData`, `TransactionData`, and `EconomicIndicatorData` DTOs directly to the `buffer_data` method. This is a significant but necessary effort.
- **Refactoring Risk (Medium)**: The logic for creating DTOs and aggregating data is being moved from `PersistenceManager` to the new `AnalyticsSystem`. There is a risk of introducing subtle bugs during this migration. A parallel run and comparison of the database output before and after the change is highly recommended.
- **Architectural Improvement (High)**: This change dramatically improves the architecture by adhering to SRP and decoupling layers. The `PersistenceManager` becomes a simple, robust, and easily testable utility. The domain logic is now correctly located in a dedicated analytics layer.

## 5. Verification & Mocking Strategy

- **Golden Data**: A "golden" database file, generated from a simulation run *before* the refactoring, should be created. After the refactoring is complete, a new run should be performed, and its database output must be compared against the golden file to ensure no data has been lost or corrupted.
- **Mocking Strategy**:
  - **`PersistenceManager` Tests**: No mocks needed. Simply create DTO instances and pass them to `buffer_data`. Assert that the internal buffers contain the correct data.
  - **`AnalyticsSystem` Tests**: These tests will be similar to the old `PersistenceManager` tests. They will require mocked `Household` and `Firm` objects to be passed in. The assertions will be on the structure and content of the returned DTOs.

## 6. 🚨 Mandatory Reporting Verification

- **Insight Captured**: This refactoring is a direct application of the **Single Responsibility Principle (SRP)** and **Dependency Inversion**. The key insight is that infrastructure layers (like persistence) should not depend on business/domain layers (like agents). Instead, both should depend on stable abstractions (DTOs).
- **Report Location**: `communications/insights/TD-272-SRP-and-Purity.md` will be created to formalize this architectural pattern and prevent future "God Class" implementations.
```
