# Report: Analysis of SoC and Cohesion

## Executive Summary
The `Simulation` class in `engine.py` exhibits significant violations of the Separation of Concerns (SoC) principle, acting as a "God Object" that contains logic for numerous, distinct economic and social subsystems. The `Household` class in `core_agents.py` also shows low cohesion, with methods like `update_needs` performing broad orchestration rather than a single, well-defined task. This high coupling and low cohesion make the system difficult to test, maintain, and extend.

## Detailed Analysis

### 1. `simulation/engine.py` (`Simulation` class)

- **Status**: ❌ Missing (Significant SoC Violations)
- **Evidence**:
    - **`engine.py:L161-L188` (`_update_social_ranks`):** The engine directly iterates through all households, reads their internal state (`current_consumption`, `is_active`), calculates a "social score," sorts them, and writes back the calculated `social_rank`. This is business logic that should belong to a dedicated `SocialMobilitySystem` or `DemographicSystem`.
    - **`engine.py:L233-L248` (Chaos Injection Events):** The main simulation loop contains hardcoded, time-based "chaos events" that directly manipulate market prices and household assets. This logic is not part of the core economic simulation and should be managed by a separate `EventSystem` or `ScenarioManager`.
    - **`engine.py:L316-L368` (Sensory Module Pipeline):** The engine is responsible for calculating SMAs for inflation, unemployment, GDP, etc., and packaging them into a `GovernmentStateDTO`. This data aggregation and transformation logic should be encapsulated within a `SensorySystem` or `GovernmentIntelligenceAgency` that the `Government` agent would own.
    - **`engine.py:L565-L678` (Consumption & Leisure Logic):** The engine orchestrates and executes household consumption. It calls a `breeding_planner`, iterates through households, directly applies consumption, handles "fast purchases," modifies agent assets, and applies leisure effects. This entire block of logic is a core responsibility of either the `Household` agent itself or a `ConsumptionSystem`, not the main engine loop.
    - **`engine.py:L700-L722` (Taxation and Infrastructure Effects):** The engine directly calls the government to calculate tax on firms and then iterates through all firms to apply a global TFP boost if infrastructure investment occurred. The TFP boost logic should be in a `TechnologyManager` or `ProductionSystem`, invoked by an event from the government's investment.
- **Notes**: The `run_tick` method is a clear example of low cohesion. It's a procedural script over 600 lines long that handles dozens of unrelated concerns, from AI training cycles to M&A processing to population dynamics. Each of these should be delegated to a specialized system manager (e.g., `AIManager.run_training()`, `CorporateSystem.process_ma()`, `PopulationSystem.update_demographics()`).

### 2. `simulation/core_agents.py` (`Household` class)

- **Status**: ⚠️ Partial (Low Cohesion and High Coupling)
- **Evidence**:
    - **`core_agents.py:L949-L1053` (`make_decision`):** This method does more than just make a decision. It also contains the execution logic for *acting* on that decision, specifically for housing. It finds the best-priced housing unit on the market and creates a buy order. Decision-making should be separate from action-execution. The `housing_planner` should return a concrete `Plan` or `Action`, which is then executed, rather than setting an internal state flag (`housing_target_mode`) that `make_decision` later interprets.
    - **`core_agents.py:L884-L902` (`update_needs`):** The method name is misleading. It doesn't just update psychological needs; it orchestrates the agent's entire tick lifecycle: working, consuming, paying taxes, and *then* updating psychological states. This indicates low cohesion. The method should be renamed `run_tick_lifecycle` or similar, and its constituent parts could be further decoupled.
    - **`core_agents.py:L1055-L1101` (`choose_best_seller`):** The `Household` agent has intimate knowledge of market mechanics, including how to calculate utility based on brand awareness, quality preference, and price. This logic is highly coupled to the market's implementation and should be delegated to a `ShoppingAssistant` component or a market-provided service that returns the best option based on agent preferences.
    - **`core_agents.py:L806-L832` (`_calculate_shadow_reservation_wage`):** The household agent is responsible for tracking market-wide wage history and calculating a "startup cost index". This is macroeconomic analysis and should not be the responsibility of an individual agent. This logic belongs in a `LaborMarketAnalyzer` or a similar system that provides this data to agents.
- **Notes**: The class has been refactored to use components like `PsychologyComponent`, `ConsumptionBehavior`, and `LeisureManager` (`core_agents.py:L218-L222`), which is a positive step toward better SoC. However, many high-level orchestration methods remain within the main `Household` class, making it a "coordinator" component rather than a simple data object.

### 3. `simulation/firms.py` (`Firm` class)

- **Status**: ⚠️ Partial (Analysis based on usage in `engine.py`)
- **Evidence**:
    - **`engine.py:L724-L781` (Firm AI Learning Update):** The `Simulation` engine directly accesses the firm's `decision_engine` and its nested `ai_engine` to call `calculate_reward` and `update_learning_v2`. This creates high coupling, as the engine needs to know the internal composition of a `Firm`'s decision-making apparatus. A better approach would be an `update_learning()` method on the `Firm` class itself, which would internally delegate to the appropriate components.
- **Notes**: The `Firm` class was not provided for direct analysis. This finding is based on how the `Simulation` class interacts with `Firm` objects, revealing a pattern where the engine reaches deep into the agent's internals.

## Risk Assessment
- **High Maintenance Cost**: With logic for specific systems spread across the `engine.py` file, fixing a bug or changing a feature (e.g., how social rank is calculated) requires modifying the central, most complex part of the simulation, increasing the risk of unintended side effects.
- **Poor Testability**: It is nearly impossible to unit test individual mechanisms like "inflation shock" or "consumption logic" without running the entire `run_tick` method, making testing slow and brittle.
- **Reduced Extensibility**: Adding a new system (e.g., an environmental impact system) would require adding yet more logic to the already bloated `run_tick` method, rather than creating a clean, self-contained, and pluggable module.

## Conclusion
The simulation's architecture suffers from significant SoC violations, primarily centered in the `Simulation.run_tick` method. While agents like `Household` have begun transitioning to a more component-based design, they retain orchestration logic that increases their complexity. The immediate action item should be to refactor the `Simulation` class, extracting distinct responsibilities (e.g., social ranking, consumption execution, sensory data processing, event management) into dedicated, independent system-level manager classes that are called sequentially by the main `run_tick` loop.
