```markdown
# Audit Report #4: Household Logic Pipeline

## Executive Summary
The core logic pipeline that translates a Household's `survival` need into consumption and market buy orders is functionally implemented. However, a critical architectural disconnect was identified: the `RuleBasedHouseholdDecisionEngine` completely bypasses the agent's 'Price Perception' model, fetching prices directly from the market. This renders the agent's economic psychology inert for survival-driven decisions.

## Detailed Analysis

### 1. Survival Need to Consumption/Bid Pipeline
- **Status**: ✅ Implemented
- **Evidence**:
    - **Need Growth**: The `survival` need is increased in `PsychologyComponent.update_needs` (`psychology_component.py:L68`).
    - **Inventory Consumption**: `ConsumptionBehavior.decide_and_consume` checks if `survival` exceeds `SURVIVAL_NEED_CONSUMPTION_THRESHOLD` to trigger consumption from inventory (`consumption_behavior.py:L35`).
    - **Market Bid Generation**: `RuleBasedHouseholdDecisionEngine.make_decisions` uses the same threshold (`SURVIVAL_NEED_CONSUMPTION_THRESHOLD`) to check the `survival` need and generate a "BUY" `Order` for "basic_food" if inventory is low (`rule_based_household_engine.py:L61-L64`).
- **Notes**: The pathway from a physiological need to an economic action (both consuming and buying) is clear and directly linked.

### 2. Price Perception Integration
- **Status**: ❌ Missing
- **Evidence**:
    - The `RuleBasedHouseholdDecisionEngine` fetches prices directly from the market via `market.get_best_ask(item_id=food_item_id)` (`rule_based_household_engine.py:L94`).
    - It makes no reference to the agent's own psychological price models, such as `household.perceived_avg_prices` or `household.expected_inflation`, which are managed by the `EconComponent` (`core_agents.py:L632-L642`).
- **Notes**: The agent has a mechanism to form opinions about prices, but its most basic decision-making engine does not consult this opinion. The agent acts on pure market reality, not its perception of it.

## Risk Assessment & Architectural Constraints

- **Critical Risk (Behavioral Inconsistency)**: Agents will not adapt their survival purchasing based on perceived inflation or historical prices. For example, an agent expecting prices to rise will not buy more, and one expecting them to fall will not delay purchases. This invalidates experiments related to inflation psychology and rational expectations for rule-based agents.
- **Architectural Constraint**: Any modification to this behavior must occur within `RuleBasedHouseholdDecisionEngine`. To fix the disconnect, this engine must be updated to query the `household`'s `EconComponent` for a "perceived" or "expected" price to use as its bid price, instead of the raw market `best_ask`.
- **SRP Violation (God Facade)**: The `Household` class in `core_agents.py` acts as a massive Facade, exposing over 80 properties and methods delegated from `BioComponent`, `EconComponent`, and `SocialComponent`. While this enforces a single point of entry, it creates a complex and bloated interface that obscures the true source of state and logic, violating the Single Responsibility Principle at the facade level.
- **Hidden Coupling**: The `Household.decide_and_consume` method (`core_agents.py:L849`) calls `self.update_needs` immediately after `self.econ_component.consumption.decide_and_consume`. This tightly couples the act of consumption with the separate lifecycle event of need decay/growth, which should be managed as distinct, sequential phases by the main simulation loop to ensure predictable state transitions.

## Conclusion
The `survival` need correctly triggers economic actions, but the system fails to integrate the agent's psychological price model into its rule-based decision-making. This is a critical flaw that limits the behavioral realism of the simulation. Future work must decide if this is intentional (for a "simple" agent) or an oversight that needs to be corrected by making the `RuleBasedHouseholdDecisionEngine` aware of the `agent`'s `EconComponent` state.
```
