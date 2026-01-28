# WO-123: AI Memory System V2 Spec

## 1. Introduction

This document outlines the design for the AI Memory System V2. Its purpose is to provide agents with a mechanism to store, recall, and learn from past experiences. The system is divided into a Short-Term Memory (STM) for immediate recall and a Long-Term Memory (LTM) for significant, consolidated events, inspired by the Priority Experience Replay (PER) concept.

## 2. System Architecture

The memory system consists of three main components: the Short-Term Memory (STM), the Long-Term Memory (LTM), and a Consolidation process that moves memories from STM to LTM.

```
+------------------+      +----------------------+      +---------------------+
| New Experience   | ---> | Short-Term Memory    | ---> |    Consolidation    |
| (ExperienceDTO)  |      | (In-Memory Deque)    |      | (Priority Check)    |
+------------------+      +----------------------+      +----------+----------+
                                                                   |
                                                                   | (If Priority > Threshold)
                                                                   v
                                                         +---------+---------+
                                                         | Long-Term Memory  |
                                                         | (Via IMemoryDAO)  |
                                                         +-------------------+
```

-   **Short-Term Memory (STM):** A fast, in-memory, fixed-size queue (`collections.deque`) that stores the most recent experiences. This provides data for immediate, high-frequency learning cycles.
-   **Long-Term Memory (LTM):** A persistent storage for experiences deemed "significant" based on a priority score. This is accessed via a Data Access Object (DAO) interface (`IMemoryDAO`), allowing for different storage backends (e.g., JSON file, SQLite, vector database).
-   **Consolidation:** A process that runs periodically to evaluate experiences in the STM. High-priority experiences are transferred to the LTM, ensuring that valuable lessons are not forgotten.

## 3. Detailed Design

### 3.1. Logic (Pseudo-code)

#### `add_experience(experience: ExperienceDTO)`

```python
# Run within the Memory System service
def add_experience(self, experience: ExperienceDTO):
    # 1. Calculate the priority of the incoming experience
    experience.priority = self._calculate_priority(experience)

    # 2. Add the experience to the short-term memory queue
    self.stm_deque.append(experience)

    # 3. If STM exceeds capacity, the oldest memory is automatically dropped by deque
    # (Assuming deque is initialized with maxlen=STM_CAPACITY)
```

#### `_calculate_priority(experience: ExperienceDTO) -> float`

```python
# Helper function to determine memory significance
def _calculate_priority(self, experience: ExperienceDTO) -> float:
    # Priority is a function of the absolute reward and a novelty factor.
    # Higher reward/penalty implies a more important lesson.
    reward_component = abs(experience.reward)

    # Novelty can be complex. For V2, we start simple:
    # A terminal state (e.g., bankruptcy) is highly novel.
    novelty_component = 1.0 if experience.is_terminal else 0.0

    # Retrieve a similar memory from LTM to gauge novelty (Future V3)
    # novelty_score = self.ltm.get_novelty(experience.state)

    priority = reward_component + novelty_component
    return priority
```

#### `consolidate(agent_id: int)`

```python
# Moves significant memories from STM to LTM
def consolidate(self, agent_id: int):
    significant_experiences = []
    
    # Use a temporary list to avoid modifying deque while iterating
    experiences_to_process = list(self.stm_deque)
    
    for experience in experiences_to_process:
        if experience.agent_id == agent_id and experience.priority >= config.LTM_CONSOLIDATION_THRESHOLD:
            significant_experiences.append(experience)

    if significant_experiences:
        # 2. Persist them using the DAO
        self.memory_dao.save_experiences(significant_experiences)

    # 3. For simplicity in V2, we clear the STM after consolidation.
    # A more advanced implementation might only remove the consolidated items.
    self.stm_deque.clear()
```

### 3.2. Interface Specification (DTO)

The `ExperienceDTO` is the core data structure for a memory.

-   `agent_id (int)`: The ID of the agent who had the experience.
-   `timestamp (int)`: The simulation tick of the event.
-   `state (Dict[str, Any])`: A snapshot of the agent/environment state *before* the action. To be effective, this should be convertible to a numerical vector (embedding).
-   `action (Dict[str, Any])`: The action taken by the agent.
-   `reward (float)`: The numerical reward (or penalty) received.
-   `next_state (Dict[str, Any])`: The state *after* the action was taken.
-   `is_terminal (bool)`: True if the experience led to a terminal state (e.g., agent bankruptcy).
-   `priority (float)`: The calculated significance of the memory.

## 4. Verification Plan

-   **Test Case 1 (STM Operation):** Create a `MemorySystem` instance. Call `add_experience` `N` times. Verify that the STM deque contains `N` experiences. Add one more experience and verify the oldest one is dropped if `N` is the `STM_CAPACITY`.
-   **Test Case 2 (Priority Calculation):** Create two `ExperienceDTO` objects, one with a high `reward` and one with a low `reward`. Verify that `_calculate_priority` returns a higher score for the high-reward experience.
-   **Test Case 3 (Consolidation Logic):**
    1.  Populate the STM with a mix of high and low-priority experiences.
    2.  Inject a mock `IMemoryDAO`.
    3.  Call `consolidate()`.
    4.  Assert that the mock DAO's `save_experiences` method was called exactly once with a list containing only the high-priority experiences.
    5.  Assert that the STM is empty after consolidation.

## 5. Mocking Guide

-   **DAO Mocking**: For all unit tests of the `MemorySystem`, the `IMemoryDAO` should be mocked using `unittest.mock.MagicMock` or a custom mock implementation. This isolates the memory logic from file I/O and allows for easy verification of what is being saved.

    ```python
    # Example in a pytest test
    def test_consolidation_saves_to_dao():
        mock_dao = MagicMock(spec=IMemoryDAO)
        memory_system = MemorySystem(dao=mock_dao, stm_capacity=10)
        
        # ... add high-priority experiences to memory_system ...

        memory_system.consolidate(agent_id=1)

        mock_dao.save_experiences.assert_called_once()
        # Further assertions on the content of the call
    ```

-   **Golden Data**: A `tests/fixtures/golden_experiences.json` file should be created with a list of realistic `ExperienceDTO` scenarios. A pytest fixture `golden_experiences(request)` can load these to be used in tests, ensuring consistency. Do not rely on `MagicMock` to create fake agent states; use structured data from fixtures like `golden_households`.

## 6. 🚨 Risk & Impact Audit

-   **Circular Dependency Risk**: `Agent -> MemorySystem -> Agent` is a potential loop.
    -   **Analysis**: An agent's decision logic will use the `MemorySystem` to retrieve memories. The outcome of that decision creates a new `ExperienceDTO` which is fed back into the `MemorySystem`.
    -   **Mitigation**: This is a valid functional loop, not a problematic import loop. The use of DTOs (`ExperienceDTO`) as the data contract prevents the `MemorySystem` from needing to `import` any specific agent or logic module, breaking the code-level dependency.
-   **Performance Impact**: LTM retrieval can become a bottleneck.
    -   **Analysis**: As the LTM grows, querying for relevant memories (`get_prioritized_memories`) based on a state `query` can be very slow if implemented as a linear scan.
    -   **Recommendation**: The first implementation of `IMemoryDAO` (e.g., `JsonMemoryDAO`) can be simple. However, the design must anticipate a future `VectorDBMemoryDAO` where `state` and `next_state` are converted to vector embeddings. Retrieval would then use fast vector similarity search (e.g., FAISS, Annoy).
-   **Configuration Dependency**: The system introduces new global parameters.
    -   **Analysis**: The system requires configuration values to function correctly.
    -   **Recommendation**: The following parameters must be added to `config/simulation.yaml`:
        -   `memory_system.stm_capacity` (e.g., 1000)
        -   `memory_system.ltm_consolidation_threshold` (e.g., 0.8)

---

### **[Routine] Mandatory Reporting**

*Implementation Note for Jules:* During your work on this module, any insights, potential improvements, or identified technical debt (e.g., "The priority calculation is too simple and should consider state novelty") must be documented and saved as a new file in the `communications/insights/` directory.

---
**END OF SPEC**

---
Now, here is the content for `modules/ai/memory/api.py`.

```python
# modules/ai/memory/api.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ExperienceDTO:
    """
    Data Transfer Object representing a single, atomic experience for an agent.
    This is the core data structure for the memory system.
    """
    agent_id: int
    timestamp: int
    state: Dict[str, Any]
    action: Dict[str, Any]
    reward: float
    next_state: Dict[str, Any]
    is_terminal: bool = False
    priority: float = 0.0

class IMemoryDAO(ABC):
    """
    Data Access Object Interface for long-term memory persistence.
    This abstracts the storage mechanism (e.g., file, database, etc.).
    """

    @abstractmethod
    def save_experiences(self, experiences: List[ExperienceDTO]) -> None:
        """
        Saves a batch of significant experiences to the persistent storage.
        """
        pass

    @abstractmethod
    def load_experiences(self, agent_id: int, query: Dict[str, Any]) -> List[ExperienceDTO]:
        """
        Loads experiences from persistent storage based on a query.
        The query mechanism can be simple (e.g., last N) or complex (e.g., semantic search).
        """
        pass

class IMemorySystem(ABC):
    """
    Interface for the AI Memory System.
    Defines the contract for how other parts of the simulation interact with an agent's memory.
    """

    @abstractmethod
    def add_experience(self, experience: ExperienceDTO) -> None:
        """
        Adds a new experience to the agent's memory, typically starting in short-term memory.
        """
        pass

    @abstractmethod
    def get_short_term_memories(self, agent_id: int, n: int) -> List[ExperienceDTO]:
        """
        Retrieves the last 'n' experiences from the short-term memory buffer.
        """
        pass

    @abstractmethod
    def get_prioritized_memories(self, agent_id: int, n: int) -> List[ExperienceDTO]:
        """
        Retrieves 'n' significant experiences from long-term memory,
        potentially using a query or sampling strategy like Priority Experience Replay.
        """
        pass

    @abstractmethod
    def consolidate(self, agent_id: int) -> None:
        """
        Triggers the process of evaluating short-term memories and moving
        high-priority ones to long-term, persistent storage.
        """
        pass

```
