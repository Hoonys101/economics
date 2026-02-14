# Specification: Household Agent Decomposition

## 1. Introduction
- **Objective**: Finalize the architectural refactoring of the `Household` agent from a "Partial Orchestrator" to a "Pure Coordinator".
- **Scope**: Extract remaining business logic (Beliefs, Crisis/Panic Selling) into stateless engines and enforce strict DTO-based communication patterns.
- **Context**: Current implementation (`simulation/core_agents.py`) contains residual logic that violates the Coordinator pattern.

## 2. Refactoring Strategy: Belief System
- **Current**: `update_perceived_prices` implements adaptive expectation logic directly.
- **Target**: `BeliefEngine.update_beliefs(input: BeliefInputDTO) -> BeliefResultDTO`.
- **Agent Responsibility**: Replace `_econ_state.perceived_avg_prices` with the result from the engine.

## 3. Refactoring Strategy: Crisis & Panic Selling
- **Current**: `trigger_emergency_liquidation` logic is in the agent.
- **Target**: `CrisisEngine.evaluate_distress(input: PanicSellingInputDTO) -> PanicSellingResultDTO`.
- **Agent Responsibility**: Execute the `orders` returned by the engine.

## 4. Pseudocode
```python
def update_beliefs(self, observed_prices):
    input_dto = BeliefInputDTO(
        current_tick=self.current_tick,
        observed_prices=observed_prices,
        current_perceived_prices=self._econ_state.perceived_prices,
        adaptation_rate=self.config.adaptation_rate
    )
    result = self.belief_engine.update_beliefs(input_dto)
    self._econ_state.perceived_prices = result.new_perceived_prices
```

## 5. Definition of Done
- `Household` contains zero business logic methods.
- All engine interactions use `InputDTO` -> `Engine` -> `ResultDTO`.
- Existing test suite passes.
