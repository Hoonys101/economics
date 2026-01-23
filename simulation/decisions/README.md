# Decisions Module

This directory contains the decision-making engines for Agents (Households and Firms).

## DTO Purity Gate & Internal Order Pattern

As of **WO-114**, the simulation enforces a strict "Purity Gate" architecture to decouple decision logic (Pure Function) from state mutation (Side Effect).

### 1. Purity Gate (DTOs)
Decision Engines must **NEVER** access Agent instances (`Firm`, `Household`) directly. Instead, they receive read-only Data Transfer Objects (DTOs) via the `DecisionContext`:
- `FirmStateDTO`
- `HouseholdStateDTO`

This ensures that the decision process is deterministic, testable, and free from unintended side effects during the decision phase.

### 2. Internal Order Pattern
Decision Engines express their intent by returning a list of `Order` objects. To modify an agent's internal state (e.g., setting production targets, firing employees, investing in R&D), engines use **Internal Orders**.

**Mechanism:**
1. **Intent:** The Engine returns an `Order` with `market_id="internal"`.
2. **Type:** The `order_type` specifies the action (e.g., `SET_TARGET`, `INVEST_RD`, `FIRE`).
3. **Execution:** The Agent class (e.g., `Firm.make_decision`) intercepts these orders before returning external market orders to the system. It executes the logic locally.

**Examples of Internal Orders:**
- `Order(type="SET_TARGET", quantity=150, market_id="internal")`: Sets production target.
- `Order(type="INVEST_AUTOMATION", quantity=5000, market_id="internal")`: Deducts cash and increases automation level.
- `Order(type="FIRE", target_agent_id=101, price=2000, market_id="internal")`: Fires employee 101 and pays 2000 severance.

This pattern standardizes all agent outputs as "Orders," whether they target the external market or the agent's own configuration.
