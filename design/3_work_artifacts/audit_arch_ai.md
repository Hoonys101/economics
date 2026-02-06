# Report: AI Engine Architecture vs. Implementation

## Executive Summary
The `simulation/ai/ai_training_manager.py` file successfully implements the core evolutionary and learning concepts outlined in `ARCH_AI_ENGINE.md`. However, there is a divergence where the implementation separates concerns more cleanly than the architecture document, and has introduced new, undocumented features, indicating minor heuristic drift.

## Detailed Analysis

### 1. AITrainingManager for Strategy Propagation
- **Status**: ✅ Implemented
- **Evidence**: The `AITrainingManager` class (`ai_training_manager.py:L14`) is the central component for evolutionary mechanisms. It implements `run_imitation_learning_cycle` (`ai_training_manager.py:L20`) to propagate strategies from top-performing agents to under-performing ones, and `inherit_brain` (`ai_training_manager.py:L67`) to pass strategies from parent to child agents. This directly aligns with the document's description of "전략의 복제와 변이" (Strategy cloning and mutation).

### 2. Multi-Channel Q-Tables
- **Status**: ✅ Implemented
- **Evidence**: `_clone_and_mutate_q_table` (`ai_training_manager.py:L182`) explicitly handles Q-tables for consumption, work, and investment (`ai_training_manager.py:L194-L203`). This matches the "Multi-Channel Aggressiveness Vector" concept, although the implementation uses separate Q-Table objects rather than a literal vector.

### 3. Evolutionary "Strategy Gene Pool"
- **Status**: ✅ Implemented
- **Evidence**: The `inherit_brain` method (`ai_training_manager.py:L67`) serves as the mechanism for passing the "Strategy Gene Pool" to the next generation by cloning Q-tables. The survival/failure dynamic is driven by selecting agents based on asset performance (`ai_training_manager.py:L135`, `L147`), as described in the architecture.

### 4. Data-Driven Purity (DecisionContext)
- **Status**: ❌ Not Found
- **Evidence**: `ai_training_manager.py` does not contain any logic related to a `DecisionContext` or ensuring pure, stateless decision-making.
- **Notes**: This indicates a separation of concerns in the implementation. `AITrainingManager` is responsible for the *evolution* of strategies (training), not the real-time *execution* of a decision. The purity principle likely applies to a different module (e.g., `HouseholdAI`) which was not provided for review.

### 5. Vectorized Planner (NumPy)
- **Status**: ❌ Not Found
- **Evidence**: No NumPy-based vectorized operations for parallel decision-making are present in `ai_training_manager.py`.
- **Notes**: As with Data-Driven Purity, this optimization belongs to the real-time decision execution layer, not the training manager. The architecture document appears to conflate the training/evolution system with the real-time decision engine.

## Risk Assessment & Heuristic Drift

- **Separation of Concerns**: The implementation has a clearer separation between the offline/evolutionary training (`AITrainingManager`) and the (presumed) real-time decision engine. This is a positive architectural pattern but represents a deviation from the unified "AI Engine" described in the document.
- **Undocumented Features**: The implementation has evolved beyond the spec, adding sophisticated new mechanics not mentioned in `ARCH_AI_ENGINE.md`:
    - **Personality Inheritance**: `inherit_brain` includes logic for passing on and mutating an agent's `Personality` (`ai_training_manager.py:L70-L105`).
    - **Education Inheritance**: A parent's "education xp" grants a learning rate bonus to the child (`ai_training_manager.py:L108-L125`).
- **Legacy Code**: The presence of logic to handle legacy strategy/tactic Q-tables (`ai_training_manager.py:L206-L216`) suggests past architectural iterations that are not reflected in the current design document.

## Conclusion
The `AITrainingManager` is well-aligned with the evolutionary principles of the design document, successfully creating a "gene pool" of strategies that are propagated through imitation and inheritance. However, the architecture document should be updated to reflect the implementation's clearer separation of concerns and to incorporate the new, more sophisticated evolutionary features like Personality and Education inheritance. The state-machine and decision purity aspects could not be verified as they lie outside the provided file.
