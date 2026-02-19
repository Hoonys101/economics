# Coding Standards: Simulation & Economic Integrity

This document outlines the engineering patterns and constraints required to maintain the structural and economic integrity of the simulation.

## 1. Economic & System Integrity Patterns

### 1.1 Lifecycle Atomicity (The "Birth Certificate" Rule)
*   **Principle**: An agent must possess a valid ID in the `AgentRegistry` **before** it can receive capital, goods, or messages.
*   **Implementation**:
    ```python
    # Correct Sequence
    agent = AgentFactory.create()
    registry.register(agent)  # 1. Existence
    settlement.transfer(source, agent.id, amount)  # 2. Capitalization
    ```

### 1.2 Solvency Guardrails (Soft Gates)
*   **Principle**: Fiscal Agents must never use "All-or-Nothing" spending logic. Use **Partial Execution** to maintain flow.
*   **Pattern**:
    ```python
    available = settlement.get_balance(self.id)
    to_spend = min(required, available)
    if to_spend > 0:
        execute_partial(to_spend)
    ```

### 1.3 The Float Quarantine
*   **Principle**: Floating-point math is permitted **only** in Valuation/Pricing logic. It must be explicitly cast to `int` (pennies) before touching the `SettlementSystem`.
*   **Mandate**: `MAManager` and `StockMarket` must wrap all transfers in `round_to_pennies()`.
