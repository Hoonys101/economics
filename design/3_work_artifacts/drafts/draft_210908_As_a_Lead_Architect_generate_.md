# Spec: `BaseAgent` Initialization Refactor (TD-268)

## 1. Overview

**Problem**: The current `BaseAgent` constructor and its `BaseAgentInitDTO` have become a monolithic, inflexible mechanism for agent creation. It conflates immutable configuration, mutable state, and complex dependencies (`decision_engine`) into a single, overloaded object. This creates tight coupling and makes a clean separation of concerns, as required by the new Orchestrator-Engine pattern, impossible.

**Goal**: Refactor the `BaseAgent` initialization chain to establish a clean, multi-stage protocol that explicitly separates an agent's **Core Identity (Config)**, its **Dynamic State**, and its **Decision Logic (Engine)**. This will resolve TD-268 and align agent architecture with the project's core design principles.

## 2. Proposed Architecture: The Orchestrator-Engine Pattern

We will formalize the "Orchestrator-Engine" pattern by introducing explicit interfaces and dedicated Data Transfer Objects.

### 2.1. Data Transfer Objects (DTOs)

Two new DTOs will replace the monolithic `BaseAgentInitDTO`:

1.  **`AgentCoreConfigDTO`**: Defines an agent's immutable, foundational properties. This data is set once at creation and does not change.
    - `id: int`
    - `name: str`
    - `value_orientation: str`
    - `initial_needs: Dict[str, float]`
    - `logger: logging.Logger`
    - `memory_interface: "MemoryV2Interface"`

2.  **`AgentStateDTO`**: A snapshot of an agent's mutable state at a specific point in time. This is used for loading state and as input for the decision engine.
    - `assets: Dict[CurrencyCode, float]`
    - `inventory: Dict[str, float]`
    - `is_active: bool`

### 2.2. Interfaces

Two new interfaces will define the contract between the agent's body (Orchestrator) and its brain (Engine).

1.  **`IDecisionEngine`**: An explicit interface for the "brain" of the agent. Its sole responsibility is to make decisions based on a state snapshot.
    - `make_decision(state: AgentStateDTO, market_snapshot: Any) -> DecisionDTO`

2.  **`IAgent`**: The public interface for all agents, representing the "Orchestrator." It manages state and executes decisions.
    - `get_core_config() -> AgentCoreConfigDTO`
    - `get_current_state() -> AgentStateDTO`
    - `load_state(state: AgentStateDTO) -> None`
    - `execute_decision(decision: DecisionDTO) -> None`

### 2.3. New Initialization Flow

Agent creation is now a two-step process: **Instantiation** followed by **Hydration**.

1.  **Instantiation**: The `BaseAgent` constructor is simplified to accept only the core configuration and the decision engine.
    ```python
    # 1. Instantiate the Engine
    engine = QLearningDecisionEngine(...)

    # 2. Define Core Config
    core_config = AgentCoreConfigDTO(id=1, name="Firm_1", ...)

    # 3. Instantiate the Agent (Orchestrator)
    # The constructor is now clean and explicit.
    agent = Firm(core_config, engine)
    ```

2.  **Hydration**: The agent's dynamic state is loaded via a separate method using the `AgentStateDTO`.
    ```python
    # 4. Define Initial State
    initial_state = AgentStateDTO(assets={"USD": 10000.0}, inventory={})

    # 5. Load the state into the agent
    agent.load_state(initial_state)
    ```

## 3. Pseudo-code Implementation

### 3.1. `modules/simulation/api.py`

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, TYPE_CHECKING
import logging

from modules.system.api import CurrencyCode

if TYPE_CHECKING:
    from modules.memory.api import MemoryV2Interface

@dataclass
class AgentCoreConfigDTO:
    """Defines the immutable, core properties of an agent."""
    id: int
    value_orientation: str
    initial_needs: Dict[str, float]
    name: str
    logger: logging.Logger
    memory_interface: MemoryV2Interface | None

@dataclass
class AgentStateDTO:
    """A snapshot of an agent's mutable state."""
    assets: Dict[CurrencyCode, float]
    inventory: Dict[str, float]
    is_active: bool

@dataclass
class DecisionDTO:
    """(Placeholder) Represents a decision made by an engine."""
    actions: list[Any]

class IDecisionEngine(ABC):
    """Interface for the 'brain' of an agent."""
    @abstractmethod
    def make_decision(self, state: AgentStateDTO, world_context: Any) -> DecisionDTO:
        ...

class IAgent(ABC):
    """Public interface for an agent 'Orchestrator'."""
    @property
    @abstractmethod
    def id(self) -> int: ...

    @abstractmethod
    def get_core_config(self) -> AgentCoreConfigDTO: ...

    @abstractmethod
    def get_current_state(self) -> AgentStateDTO: ...

    @abstractmethod
    def load_state(self, state: AgentStateDTO) -> None: ...

    @abstractmethod
    def update_needs(self, current_tick: int) -> None: ...

    @abstractmethod
    def make_decision(self, input_dto: Any) -> tuple[list[Any], Any]: ...
```

### 3.2. `simulation/base_agent.py` (Refactored)

```python
# from modules.simulation.api import IAgent, IDecisionEngine, AgentCoreConfigDTO, AgentStateDTO
# ... other imports

class BaseAgent(IAgent, ICurrencyHolder, IInventoryHandler, IFinancialEntity, ABC):
    def __init__(self, core_config: AgentCoreConfigDTO, engine: IDecisionEngine):
        # 1. Store core, immutable properties
        self._core_config = core_config
        self.decision_engine = engine

        # 2. Initialize internal state containers
        self._wallet = Wallet(self.id, {})
        self._inventory: Dict[str, float] = {}
        self.is_active: bool = True
        self.pre_state_snapshot: Dict[str, Any] = {}

        # 3. Directly accessible properties from core config
        self.id = core_config.id
        self.name = core_config.name
        self.logger = core_config.logger
        self.memory_v2 = core_config.memory_interface
        self.value_orientation = core_config.value_orientation
        self.needs = core_config.initial_needs.copy()

    def load_state(self, state: AgentStateDTO) -> None:
        """Hydrates the agent with dynamic state."""
        self._wallet.load_balances(state.assets)
        self._inventory = state.inventory.copy()
        self.is_active = state.is_active

    def get_core_config(self) -> AgentCoreConfigDTO:
        return self._core_config

    def get_current_state(self) -> AgentStateDTO:
        return AgentStateDTO(
            assets=self._wallet.get_all_balances(),
            inventory=self._inventory.copy(),
            is_active=self.is_active
        )

    # ... other methods (deposit, withdraw, add_item) remain the same
```

## 4. 🚨 Risk & Impact Audit (Addressing Pre-flight Findings)

This refactor directly addresses the identified risks, while acknowledging architectural constraints.

1.  **God Class & Hidden Dependencies**: This refactor **contains, but does not solve**, the `Firm` God Class pattern. By introducing `AgentStateDTO`, we make the state passed between components more explicit, paving the way for a future refactor. The "parent pointer" (`HRDepartment(self)`) remains a necessary evil for now, but its state manipulation becomes more traceable.

2.  **Opaque `decision_engine` Dependency**: **Resolved**. The `IDecisionEngine` interface makes this critical dependency explicit, formalizing the contract between the agent and its AI model. The `Any` type is eliminated.

3.  **Inherent Circular Import Risk**: **Mitigated**. The risk remains, but this design does not exacerbate it. The `if TYPE_CHECKING:` blocks for parent type hints in `Firm` and its departments **must be preserved**.

4.  **Brittle and Coupled Tests**: **High Impact**. This is a **breaking change**. All existing test fixtures for agents are now obsolete. A new testing strategy is required. See Verification Plan below.

## 5. Verification Plan & Mocking Strategy

The existing test setup is incompatible and must be rebuilt.

-   **New Fixtures**: New Pytest fixtures will be created to build agents using the new two-stage `__init__` -> `load_state` flow.
-   **Golden Data**: Golden data will be split into two files:
    1.  `golden_firm_config.json` -> Deserializes into `AgentCoreConfigDTO`.
    2.  `golden_firm_state.json` -> Deserializes into `AgentStateDTO`.
-   **Test Example**:
    ```python
    @pytest.fixture
    def fully_loaded_firm(golden_firm_config, golden_firm_state) -> Firm:
        # Stage 1: Instantiate
        engine = MockDecisionEngine() # Use a mock or fake engine
        firm = Firm(golden_firm_config, engine)

        # Stage 2: Hydrate
        firm.load_state(golden_firm_state)
        return firm

    def test_firm_production(fully_loaded_firm: Firm):
        # The test now receives a correctly constructed agent
        assert fully_loaded_firm.get_quantity("product_A") > 0
    ```
This approach decouples test setup from the complex logic of agent creation, making tests more robust and maintainable.

## 6. 🚨 Mandatory Reporting Verification

Insights and technical debt discovered during the implementation of this refactor will be recorded in `communications/insights/TD-268_BaseAgent_Init_Refactor.md`. This includes tracking the effort required to migrate test fixtures to the new architecture. **This report is a required deliverable for mission completion.**
