# Report: Analysis of Hardcoded Heuristics and Technical Debt

## Executive Summary
The codebase contains a significant amount of technical debt in the form of hardcoded "magic numbers," fixed thresholds, and rule-based heuristics. This makes the simulation rigid and predictable. Migrating to a truly adaptive AI system will require refactoring these components into dynamic, learnable mechanisms.

## Detailed Analysis

### 1. Configuration File (`config.py`)
The `config.py` file centralizes many constants, but many of these represent static rules rather than flexible parameters. An adaptive AI should be able to adjust these values based on the economic climate.

-   **TD-001: Fixed M&A Thresholds**
    -   **Location**: `config.py`
    -   **Snippet**: `HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD = 0.7`
    -   **Analysis**: This sets a fixed 70% discount threshold for identifying hostile takeover targets. In a real economy, this "discount" is variable, influenced by market sentiment, interest rates, and sector health. An adaptive AI should determine the takeover threshold dynamically.

-   **TD-002: Static Severance and Labor Rules**
    -   **Location**: `config.py`
    -   **Snippet**: `SEVERANCE_PAY_WEEKS = 4`, `WAGE_DECAY_RATE = 0.02`
    -   **Analysis**: The number of severance weeks and the rate at which an unemployed agent's wage expectation decays are fixed. These should be influenced by labor laws (which could be a government AI policy), unemployment rates, and the agent's financial desperation.

-   **TD-003: Arbitrary Population and Startup Costs**
    -   **Location**: `config.py`
    -   **Snippet**: `POPULATION_IMMIGRATION_THRESHOLD = 80`, `STARTUP_COST = 30000.0`
    -   **Analysis**: Immigration triggers and startup costs are static. These should be emergent properties of the economy, influenced by housing availability, cost of living, and access to capital.

-   **TD-004: Inflexible Tax Brackets**
    -   **Location**: `config.py`
    -   **Snippet**: `TAX_BRACKETS = [(0.5, 0.0), (1.0, 0.05), ...]`
    -   **Analysis**: The income tax brackets are defined as static multiples of survival cost. A government AI should have the flexibility to adjust not only the rates but also the bracket thresholds themselves as part of its fiscal policy.

### 2. Agent and Decision Logic (`simulation/`)
Agents' decision-making processes are frequently constrained by simplistic, hardcoded `if/else` logic and fixed formulas, preventing nuanced or learned behaviors.

-   **TD-005: Rigid Housing Decision Trigger**
    -   **Location**: `simulation/core_agents.py` (Household.decide_housing)
    -   **Snippet**: `if not (self.is_homeless or current_time % 30 == 0): return`
    -   **Analysis**: Housing decisions are only reviewed on a fixed 30-tick cycle or when homeless. This is an arbitrary schedule. An agent should be able to reconsider housing based on life events (new job, change in wealth) or market shocks, not just a timer.

-   **TD-006: Fixed Shadow Wage Formula**
    -   **Location**: `simulation/core_agents.py` (Household._calculate_shadow_reservation_wage)
    -   **Snippet**: `self.shadow_reservation_wage *= (1.0 - 0.02)`
    -   **Analysis**: The reservation wage decays at a fixed rate of 2% per tick when unemployed. This rate should be adaptive, potentially decreasing faster if the agent's survival need is high or slower if the agent has a large financial buffer.

-   **TD-007: Simplistic Firm Valuation**
    -   **Location**: `simulation/firms.py` (Firm.calculate_valuation)
    -   **Snippet**: `profit_premium = max(0.0, avg_profit) * getattr(self.config_module, "VALUATION_PER_MULTIPLIER", 10.0)`
    -   **Analysis**: The Price-to-Earnings (PER) multiplier for valuing a firm's profit potential is a hardcoded constant (10.0). In reality, the PER is highly dynamic and sector-dependent. This should be a market-derived value.

-   **TD-008: Hardcoded R&D Logic**
    -   **Location**: `simulation/decisions/corporate_manager.py` (_manage_r_and_d)
    -   **Snippet**: `denominator = max(firm.revenue_this_turn * 0.2, 100.0)`
    -   **Analysis**: The formula to determine the base chance of R&D success contains magic numbers (`0.2`, `100.0`). The relationship between budget and success should be more complex, perhaps a learnable function or S-curve, rather than a simple linear ratio.

### 3. System-Level Rules (`simulation/systems/`)
The systems that govern the simulation's "physics" rely on rigid formulas and probabilities, limiting emergent behavior.

-   **TD-009: Fixed Mortality Formula**
    -   **Location**: `simulation/systems/demographic_manager.py` (process_aging)
    -   **Snippet**: `if agent.age > 80: death_prob = 0.05 + (agent.age - 80) * 0.01`
    -   **Analysis**: The probability of natural death is a simple, hardcoded linear function of age past 80. This model does not account for wealth, access to services, or overall quality of life, which should influence lifespan.

-   **TD-010: Rigid Immigration Trigger**
    -   **Location**: `simulation/systems/immigration_manager.py` (process_immigration)
    -   **Snippet**: `condition_labor_shortage = unemployment_rate < 0.05`
    -   **Analysis**: Immigration is triggered by a fixed unemployment rate threshold of 5%. This should be a policy lever for the government AI, allowing it to open or close borders based on a wider range of economic indicators (e.g., wage pressure, GDP growth, housing capacity).

-   **TD-011: Fixed Hostile Takeover Probability**
    -   **Location**: `simulation/systems/ma_manager.py` (_attempt_hostile_takeover)
    -   **Snippet**: `success_prob = 0.6`
    -   **Analysis**: The success probability of a hostile takeover is a static 60%. This should be a dynamic calculation based on the predator's offer premium, the target's financial health, and potentially the loyalty of its existing shareholders (a currently unmodeled concept).

-   **TD-012: Static AI State Discretization**
    -   **Location**: `simulation/ai/government_ai.py` (_get_state)
    -   **Snippet**: `if inf_gap_val < -0.01: s_inf = 0`
    -   **Analysis**: The AI's entire state representation is based on hardcoded thresholds (e.g., inflation gap < -1%). These boundaries are arbitrary. A more advanced AI could work with continuous data or learn the optimal thresholds itself.

## Risk Assessment
The pervasive use of hardcoded heuristics presents several risks:
-   **Brittleness**: The simulation is not resilient to edge cases or scenarios that fall outside the predefined rules.
-   **Unrealistic Behavior**: The fixed logic prevents agents from developing novel or nuanced strategies, leading to predictable and less realistic emergent outcomes.
-   **Difficult Evolution**: Migrating to an adaptive AI will require significant refactoring. Each hardcoded rule is a point of friction that must be individually replaced with a more flexible system.

## Conclusion
The current codebase serves as a solid foundation, but its reliance on static rules and magic numbers is a significant technical debt. A dedicated "Adaptive AI Migration" phase is required. The priority should be to replace fixed decision thresholds, static formulas, and arbitrary constants with systems that allow for dynamic, AI-driven parameterization and learned behavioral models.
