# Master Plan: (Test Cleanroom) & (AI Memory V2) Re-entry

**Objective:** Execute a coordinated, one-shot implementation of and to establish a robust, testable foundation for next-generation AI agents and eliminate systemic sources of technical debt related to testing and state management.

---

## 1. Test Purity Protocol ()

This protocol is mandatory for all new and refactored test code. Its purpose is to eradicate non-determinism and prevent `MagicMock` contamination, which leads to brittle, untyped, and unreliable tests.

### Core Mandates

1. **No Raw `MagicMock` for Core Objects**:
 * **Problem**: Direct use of `MagicMock` for complex objects like `Household`, `Firm`, or `Market` bypasses type checking and creates "tests that lie" about the correctness of the implementation's interface.
 * **Solution**: Core simulation objects MUST be instantiated via:
 * **Golden Fixtures**: Use pre-configured, realistic fixtures from `tests/conftest.py` (e.g., `golden_households`, `golden_firms`).
 * **Golden Loader**: For specific scenarios, use `scripts/fixture_harvester.py` and its `GoldenLoader` to load entities from data fixtures.

2. **DTOs via Helpers Only**:
 * **Problem**: Manual instantiation of Data Transfer Objects (DTOs) in tests is verbose and prone to errors when the DTO definition changes.
 * **Solution**: All DTO instances required for tests MUST be created using a centralized factory. A new file, `tests/helpers/dto_factory.py`, will be created for this purpose.
 * **Example**: `dto_factory.create_order_dto(agent_id=1, good="food", quantity=10)`

3. **Deterministic Time**:
 * **Problem**: Usage of `datetime` or floating-point numbers for timestamps introduces non-determinism.
 * **Solution**: All time-related fields (`Time`, `timestamp`, `created_at`, etc.) in DTOs and simulation state **MUST be represented as integers**. This ensures perfect reproducibility. The simulation tick is the source of truth for time.

4. **Fixture-Based Dependency Injection**:
 * **Problem**: Manually instantiating dependency chains (e.g., a `Household` needing a `Market`) within a test makes it fragile.
 * **Solution**: All external dependencies for a unit under test MUST be provided via Pytest fixtures.

---

## 2. Standard MockConfig Specification for AI Engines

To facilitate reliable, isolated testing of AI-driven components, we will standardize a `MockSimulationConfig`. This object will provide all necessary configuration parameters without requiring the full simulation environment.

It shall be defined in `tests/mocks/mock_config.py`.

```python
# tests/mocks/mock_config.py
from dataclasses import dataclass, field

@dataclass
class MockAIConfig:
 decision_cycle: int = 10
 max_memory_entries: int = 100
 pruning_threshold: float = 0.5

@dataclass
class MockEconomyConfig:
 starting_population: int = 50
 goods: list[str] = field(default_factory=lambda: ["food", "wood", "tools"])

@dataclass
class MockMarketConfig:
 initial_prices: dict[str, float] = field(default_factory=lambda: {"food": 1.0, "wood": 2.0})
 enable_dynamic_pricing: bool = False

@dataclass
class MockSimulationConfig:
 """
 A standardized, mockable configuration object for testing
 AI engines and other simulation components in isolation.
 """
 ai: MockAIConfig = field(default_factory=MockAIConfig)
 economy: MockEconomyConfig = field(default_factory=MockEconomyConfig)
 market: MockMarketConfig = field(default_factory=MockMarketConfig)
 simulation_id: str = "mock_sim_001"
 total_ticks: int = 1000

```

---

## 3. AI Memory V2 Architecture ()

The V2 memory system will be a structured, persistent, and queryable store for agent experiences, replacing the ephemeral and untyped V1 implementation.

### 3.1. Folder Structure

The new memory module will be located at `modules/memory/` and organized as follows:

```
modules/memory/
├── api.py # Public interface (MemoryV2Interface)
├── V2/
│ ├── __init__.py
│ ├── memory_manager.py # Core logic, implements MemoryV2Interface
│ ├── dtos.py # DTOs for memory records (e.g., MemoryRecordDTO)
│ └── storage/
│ ├── __init__.py
│ ├── base_storage.py # Abstract StorageInterface (ABC)
│ ├── file_storage.py # Filesystem-based JSON storage
│ └── sqlite_storage.py # (Future) SQLite-based storage
└── V1/
 └── ... # Legacy implementation (to be deprecated)
```

### 3.2. Interface and Compatibility

* **API Definition (`api.py`)**: A new `MemoryV2Interface` will be defined as an abstract base class, specifying the contract for all agent interactions with memory.

 ```python
 # modules/memory/api.py
 from abc import ABC, abstractmethod
 from typing import List
 from .V2.dtos import MemoryRecordDTO, QueryDTO

 class MemoryV2Interface(ABC):
 @abstractmethod
 def add_record(self, record: MemoryRecordDTO) -> None:
 ...

 @abstractmethod
 def query_records(self, query: QueryDTO) -> List[MemoryRecordDTO]:
 ...
 ```

* **Compatibility Strategy**:
 1. The `MemoryManager` will implement the `MemoryV2Interface`.
 2. Existing Agent classes will be updated to require a `MemoryV2Interface` object on initialization.
 3. During transition, the main simulation engine will inject the `MemoryManager` into agents. This ensures that agents are decoupled from the specific memory implementation.
 4. The V1 memory system will be marked as deprecated and removed after all agents are migrated.

---

## 4. Implementation Checklist for Jules

This checklist provides a clear, step-by-step path to completion.

### Phase 1: Establish Test Purity ()

* [ ] **Task 1.1**: Create `tests/helpers/dto_factory.py`. Implement helper functions for at least `OrderDTO`, `TradeDTO`, and `MarketStateDTO`.
* [ ] **Task 1.2**: Create `tests/mocks/mock_config.py` with the `MockSimulationConfig` as specified in Section 2.
* [ ] **Task 1.3**: Refactor `tests/modules/market/test_market_logic.py` to exclusively use the `dto_factory` and `golden_` fixtures. Remove all instances of `MagicMock` for core objects and DTOs.
* [ ] **Task 1.4**: Audit the codebase for `datetime.now()` or other `datetime` usage in simulation logic and replace it with integer-based `Time` ticks.

### Phase 2: Scaffold AI Memory V2 ()

* [ ] **Task 2.1**: Create the directory structure for `modules/memory/V2/` as defined in Section 3.1.
* [ ] **Task 2.2**: Define the `MemoryRecordDTO` and `QueryDTO` in `modules/memory/V2/dtos.py`. The `MemoryRecordDTO` must include `tick` (int), `agent_id` (int), `event_type` (str), and `data` (dict) fields.
* [ ] **Task 2.3**: Define the `MemoryV2Interface` in `modules/memory/api.py` as specified in Section 3.2.
* [ ] **Task 2.4**: Implement the basic `MemoryManager` class in `modules/memory/V2/memory_manager.py`. It should implement the `MemoryV2Interface` and have placeholder methods.
* [ ] **Task 2.5**: Implement the `StorageInterface` ABC and a basic `FileStorage` implementation that saves records to a JSON file.

### Phase 3: Integration and Verification

* [ ] **Task 3.1**: Create the test suite `tests/modules/memory/test_memory_v2.py`.
* [ ] **Task 3.2**: Write unit tests for `MemoryManager` using `MockSimulationConfig` and `dto_factory`. Ensure persistence (add/query) works correctly with the `FileStorage` backend.
* [ ] **Task 3.3**: Select one agent (e.g., `BasicHouseholdAgent`) and refactor it to accept and use the `MemoryV2Interface`.
* [ ] **Task 3.4**: Create a verification script `scripts/verify_memory_v2.py`. This script should run a 100-tick mini-simulation with one agent, confirming that memory records are created and can be queried post-simulation.

### Phase 4: Full Rollout and Cleanup

* [ ] **Task 4.1**: Migrate all remaining AI agents to use the `MemoryV2Interface`.
* [ ] **Task 4.2**: Once all agents are migrated, delete the `modules/memory/V1/` directory and any related legacy code.
* [ ] **Task 4.3**: Submit the final Pull Request for review.
