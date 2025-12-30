# AI Learning Mechanism Design: Imitation & Evolution

## 1. Overview
This document outlines the design for the "Imitation and Evolutionary Learning Mechanism" in the economic simulation. The goal is to accelerate the learning process of agents (Households) by allowing less successful agents to imitate the strategies of successful ones, and to introduce innovation through mutation.

## 2. Core Components

### 2.1. `AITrainingManager`
- **Role**: Manages the imitation learning cycles and evolutionary processes.
- **Location**: `simulation/ai/ai_training_manager.py`
- **Key Responsibilities**:
    - Identify top-performing agents (Role Models).
    - Identify under-performing agents (Learners).
    - Execute Q-table cloning and mutation.
    - Provide "fittest" Q-tables for new agent initialization.

### 2.2. `BaseAIEngine` & `QTableManager`
- **Role**: Stores and manages the Q-tables for Strategy (Intention) and Tactic (Action).
- **Location**: `simulation/ai/api.py`, `simulation/ai/q_table_manager.py`
- **Key Responsibilities**:
    - Provide access to Q-tables for cloning (`get_q_table`, `set_q_table`).
    - (Implicitly) Support deep copying of Q-tables.

### 2.3. `Simulation` Engine
- **Role**: Triggers the learning cycles.
- **Location**: `simulation/engine.py`
- **Key Responsibilities**:
    - Call `AITrainingManager.run_imitation_learning_cycle()` at configured intervals.
    - Call `AITrainingManager.clone_from_fittest_agent()` when creating new agents (if applicable).

## 3. Algorithms & Logic

### 3.1. Imitation Learning Cycle
**Trigger**: Every `IMITATION_LEARNING_INTERVAL` ticks (e.g., 1000 ticks).

**Steps**:
1.  **Selection**:
    -   Sort all active Households by `assets` (descending).
    -   **Role Models**: Top 10% of agents.
    -   **Learners**: Bottom 50% of agents.
2.  **Cloning**:
    -   For each Learner:
        -   Randomly select one Role Model.
        -   **Strategy Cloning**: Deep copy `role_model.ai_engine.q_table_manager_strategy.q_table` to `learner`.
        -   **Tactic Cloning**: Deep copy `role_model.ai_engine.q_table_manager_tactic.q_table` to `learner`.
3.  **Mutation**:
    -   Apply mutation to the cloned Q-tables to introduce variation.

### 3.2. Mutation Logic
**Goal**: Prevent "mode collapse" where all agents do exactly the same thing, and allow for local optimization.

**Parameters**:
-   `IMITATION_MUTATION_RATE` (e.g., 0.1): Probability of mutating a specific Q-value.
-   `IMITATION_MUTATION_MAGNITUDE` (e.g., 0.05): Max change applied to a Q-value.

**Algorithm**:
```python
for state, actions in q_table.items():
    for action in actions:
        if random.random() < mutation_rate:
            noise = random.uniform(-mutation_magnitude, mutation_magnitude)
            q_table[state][action] += noise
```

### 3.3. New Agent Initialization (Evolutionary)
**Goal**: New agents shouldn't start from scratch (tabula rasa) but from a "good enough" baseline.

**Logic**:
-   When `create_new_household` is called:
    -   Retrieve the single "Fittest Agent" (highest assets).
    -   Clone its Strategy and Tactic Q-tables to the new agent.
    -   Apply mutation.

## 4. API Definitions

### `AITrainingManager`

```python
class AITrainingManager:
    def __init__(self, agents: List[Household], config_module: Any):
        ...

    def run_imitation_learning_cycle(self, current_tick: int) -> None:
        """Executes the full imitation cycle: Selection -> Cloning -> Mutation."""
        ...

    def clone_from_fittest_agent(self, target_agent: Household) -> None:
        """Clones Q-tables from the absolute best agent to the target agent."""
        ...

    def _get_top_performing_agents(self, percentile: float = 0.1) -> List[Household]:
        ...

    def _get_under_performing_agents(self, percentile: float = 0.5) -> List[Household]:
        ...

    def _clone_and_mutate_q_table(self, source: Household, target: Household) -> None:
        """Handles deep copy and mutation for BOTH Strategy and Tactic Q-tables."""
        ...
```

### `QTableManager` (Existing/Enhanced)

```python
class QTableManager:
    # Existing methods...
    
    def get_q_table(self) -> Dict:
        """Returns the raw Q-table dictionary."""
        return self.q_table

    def set_q_table(self, new_q_table: Dict) -> None:
        """Overwrites the Q-table."""
        self.q_table = new_q_table
```

## 5. Implementation Considerations

1.  **Performance**: Deep copying large dictionaries can be slow.
    -   *Mitigation*: The cycle runs infrequently (e.g., every 1000 ticks).
2.  **Reference Safety**: Ensure `copy.deepcopy` is used so Learners don't share memory references with Role Models (modifying Learner shouldn't affect Role Model).
3.  **State Compatibility**: Ensure Role Model and Learner use the same State/Action definitions (Enums). Since they share the same code class, this is guaranteed, but versioning could be an issue if code changes during a long run (not applicable for now).
4.  **Preserving Personality**:
    -   Currently, `Personality` influences `ActionSelector` but not the Q-table structure itself.
    -   *Decision*: We clone the Q-table (knowledge), but the Agent keeps its own `Personality` (preferences). This allows the same "winning strategy" to be executed slightly differently based on personality.

## 6. Integration Steps

1.  **Modify `AITrainingManager`**:
    -   Implement `_get_under_performing_agents`.
    -   Update `_clone_and_mutate_q_table` to handle **both** Strategy and Tactic tables.
    -   Implement `clone_from_fittest_agent`.
2.  **Update `Simulation`**:
    -   Ensure `run_imitation_learning_cycle` is called.
    -   (Future) Update agent spawning logic to use `clone_from_fittest_agent`.
3.  **Testing**:
    -   Unit test: Mock agents, verify Q-values are copied and mutated.
    -   Integration test: Run simulation, verify low-asset agents suddenly jump in performance (or at least change behavior) after a cycle.
