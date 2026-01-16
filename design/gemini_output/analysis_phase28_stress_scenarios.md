```markdown
# Phase 28 Stress Test Analysis & Implementation Plan

This document outlines the analysis and proposed implementation strategy for Phase 28: Macro-Stability Stress Testing. It identifies key economic variables, defines three core stress scenarios, and proposes an architecturally-sound approach for implementation that respects the findings of the pre-flight audit.

## 1. Key Configurable Economic Variables

Based on an analysis of the codebase, the following variables are central to the simulation's economic behavior. They are categorized by their primary domain of influence.

### Agent Behavior (Households & Firms)
- **Psychology & Preferences:**
  - `ADAPTATION_RATE_*`: Controls how quickly households adapt to new inflation expectations.
  - `PERCEIVED_PRICE_UPDATE_FACTOR`: Smoothing factor for how households perceive price changes.
  - `INFLATION_MEMORY_WINDOW`: The time horizon for remembering past prices.
  - `QUALITY_PREFERENCE`, `BRAND_SENSITIVITY_BETA`: Governs household preference for quality and brand over price.
  - `VALUE_ORIENTATION_MAPPING`: Defines core preferences for asset, social, and growth goals.
  - `CONFORMITY_RANGES`: Controls the tendency of households to follow social trends.
  - `RISK_AVERSION`: General modifier for financial risk-taking.
- **Labor & Consumption:**
  - `MAX_WORK_HOURS`, `SHOPPING_HOURS`: Defines the household time budget.
  - `HOUSEHOLD_MIN_WAGE_DEMAND`, `HOUSEHOLD_DEFAULT_WAGE`: Base parameters for household wage expectations.
  - `FOOD_CONSUMPTION_QUANTITY`: Minimum survival consumption amount.
  - `HOUSEHOLD_LOW_ASSET_THRESHOLD`: Asset level below which households accept lower wages.
- **Education & Skills:**
  - `EDUCATION_WEALTH_THRESHOLDS`: Asset gates for achieving higher education levels.
  - `EDUCATION_COST_MULTIPLIERS`: Determines the wage premium for education.
- **Firm Logic:**
  - `STARTUP_GRACE_PERIOD_TICKS`: How long startups are exempt from strict solvency checks.
  - `ALTMAN_Z_SCORE_THRESHOLD`: The threshold for firm bankruptcy.

### Market & System Dynamics
- `INITIAL_RENT_PRICE`, `INITIAL_WAGE`: Core price anchors at simulation start.
- `INFRASTRUCTURE_TFP_BOOST`: Productivity increase from government investment.
- `IMITATION_LEARNING_INTERVAL`: Frequency of the AI's imitation learning cycle.
- `BOND_MATURITY_TICKS`: The term length for government bonds.
- `TICKS_PER_YEAR`: Defines the conversion rate between ticks and years for financial calculations.

### Government & Central Bank Policy
- `DEBT_RISK_PREMIUM_TIERS`: Defines the risk premium on government debt based on Debt-to-GDP ratio.
- `QE_INTERVENTION_YIELD_THRESHOLD`: The bond yield that triggers Central Bank intervention (Quantitative Easing).
- `BAILOUT_PENALTY_PREMIUM`, `BAILOUT_REPAYMENT_RATIO`: Terms for corporate bailout loans.
- **Tax Policy**: (Implicitly configured in `Government` class) Corporate and income tax rates.

## 2. Proposed Stress Scenarios & Behavioral Parameterization

To avoid polluting the global `config_module` and to heed the audit's warnings, all new scenario-specific parameters should be encapsulated in a dedicated DTO, `StressScenarioConfig`, and passed explicitly to agents.

```python
# Proposed DTO structure (to be defined in a new file, e.g., simulation/dtos/scenario.py)
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class StressScenarioConfig:
    # General Scenario Flags
    is_active: bool = False
    scenario_name: Optional[str] = None

    # Hyperinflation Parameters
    inflation_expectation_multiplier: float = 1.0  # Multiplies household adaptation_rate
    hoarding_propensity_factor: float = 0.0      # Extra goods to buy when inflation is high (0.0 = none)

    # Deflationary Spiral Parameters
    panic_selling_enabled: bool = False               # Enable asset fire-sales
    debt_aversion_multiplier: float = 1.0             # Multiplies desire to repay debt vs consume
    consumption_pessimism_factor: float = 0.0         # % reduction in consumption if unemployed/pessimistic (0.0 = none)

    # Supply Shock Parameters
    exogenous_productivity_shock: Dict[str, float] = field(default_factory=dict) # e.g., {"firm_type_A": 0.5}
```

---

### Scenario 1: Hyperinflation (Demand-Pull / Cost-Push)

- **Goal:** Test the stability of the currency and market pricing mechanisms under rapidly rising prices and inflation expectations.
- **Triggers:**
  1.  **Demand-Pull:** At `tick == SCENARIO_START_TICK`, inject a large amount of cash directly into all household assets ("Helicopter Money").
  2.  **Cost-Push:** At `tick == SCENARIO_START_TICK`, dramatically increase a core input cost for all firms (e.g., by doubling the `labor` price in `market_data` for one tick).
- **Key Behaviors & Parameters:**
  - **Accelerated Inflation Expectations:** Households must react faster to price changes.
    - **Parameter:** `StressScenarioConfig.inflation_expectation_multiplier`.
    - **Injection Point:** In `Household.update_perceived_prices`, the `adaptation_rate` would be multiplied by this factor, making `expected_inflation` more sensitive.
  - **Pre-emptive Hoarding:** Households buy more non-durable goods than immediately necessary, expecting future price rises.
    - **Parameter:** `StressScenarioConfig.hoarding_propensity_factor`.
    - **Injection Point:** In `Household.make_decision` (or its `ConsumptionBehavior` component), the quantity for `BUY` orders for goods like `basic_food` would be increased if `expected_inflation` is high.
  - **Rapid Price Adjustments (Firms):** Firms update their sell prices more frequently and aggressively.
    - **Injection Point:** In `Firm.make_decision`, when setting sell order prices, firms would react more strongly to their own rising costs or observed market price changes, instead of using smoothed averages.

---

### Scenario 2: Deflationary Spiral (Debt-Deflation)

- **Goal:** Test the system's resilience against a collapse in asset values, falling demand, and rising real debt burdens.
- **Triggers:**
  1.  **Asset Shock:** At `tick == SCENARIO_START_TICK`, execute a large, one-time reduction in all household and firm assets (e.g., `assets *= 0.5`), simulating a market crash.
  2.  **Credit Crunch:** The `Bank` dramatically increases its `base_rate`.
- **Key Behaviors & Parameters:**
  - **Panic Selling / Fire Sales:** Households and firms liquidate assets (stocks, property) to raise cash, further depressing prices.
    - **Parameter:** `StressScenarioConfig.panic_selling_enabled`.
    - **Injection Point:** In `Household.make_decision`, if this flag is true and `assets` are below a threshold, the agent will generate `SELL` orders for items in its `portfolio`, ignoring long-term value.
  - **Consumption Collapse:** Unemployed or pessimistic households drastically cut spending.
    - **Parameter:** `StressScenarioConfig.consumption_pessimism_factor`.
    - **Injection Point:** In `Household.make_decision`, the budget allocated for consumption would be reduced by this factor if `is_employed == False`.
  - **Debt Aversion:** Agents prioritize debt repayment over all other spending.
    - **Parameter:** `StressScenarioConfig.debt_aversion_multiplier`.
    - **Injection Point:** In `Household.make_decision`, the logic for creating `REPAYMENT` orders would be given higher priority and a larger budget allocation, multiplied by this factor.
  - **Investment Freeze (Firms):** Firms cancel all expansionary investment (hiring, R&D) and focus solely on survival.
    - **Injection Point:** In `Firm.make_decision`, logic for creating `BUY` orders for labor or CAPEX-related goods would be suppressed if demand is falling.

---

### Scenario 3: Supply Shock (Productivity Collapse)

- **Goal:** Test the system's ability to adapt to a sudden, structural inability to produce essential goods.
- **Triggers:**
  1.  **Productivity Shock:** At `tick == SCENARIO_START_TICK`, permanently reduce the `productivity_factor` of firms in a critical sector (e.g., `Farm` firms producing `basic_food`). This is done via the `exogenous_productivity_shock` parameter.
- **Key Behaviors & Parameters:**
  - **Labor Shedding vs. Hoarding (Firms):** Firms must decide whether to fire workers they can no longer use productively or keep them on the payroll, expecting a recovery.
    - **Injection Point:** In `Firm.make_decision`, the logic that determines the quantity for `labor` `BUY` orders would need to be adjusted. A new firm-level "patience" or "optimism" trait could be parameterized here.
  - **Input Substitution (Firms/Households):** When an input/good becomes scarce and expensive, agents must try to use an alternative.
    - **Injection Point:** This reveals a weakness noted in the audit. The current logic in `Household.decide_and_consume` is likely hardcoded to specific goods. A refactoring would be needed to create a `good_utility_map` that could be dynamically adjusted based on price and availability, representing substitution.
  - **Price Gouging vs. Price Smoothing (Firms):** Do firms with remaining supply exploit the shortage by raising prices astronomically, or do they smooth prices to maintain brand loyalty?
    - **Injection Point:** In `Firm.make_decision`, the pricing logic for `SELL` orders could be modified to be more or less reactive to the supply/demand imbalance, potentially controlled by a firm's `Personality`.

## 3. Implementation Strategy (Architectural Recommendations)

This strategy is designed to introduce stress testing capabilities without exacerbating the existing architectural debt identified in the pre-flight audit.

1.  **Introduce a `StressScenarioConfig` DTO:**
    - Create a new, dedicated dataclass in `simulation/dtos/`. This object will hold all scenario-specific parameters.
    - An instance of this DTO will be created by the `Simulation` initializer.
    - **This avoids adding more unstructured `getattr` calls to the fragile `config_module`.**

2.  **Explicit Parameter Passing (No God Object Modification):**
    - The `StressScenarioConfig` object must be passed **explicitly** down the call stack.
    - `Simulation.run_tick()` will pass it to `Household.make_decision()` and `Firm.make_decision()`.
    - **DO NOT** make it a global or an attribute of the `Simulation` object that agents can access directly. This maintains clear data flow.

3.  **Isolate Scenario Triggers:**
    - The *triggers* for each scenario (e.g., the initial asset shock or productivity drop) should be implemented as a simple, self-contained `if self.time == SCENARIO_START_TICK:` block at the **top** of the `Simulation.run_tick()` method.
    - This block reads from the `StressScenarioConfig` to activate the correct shock.
    - **This contains the only modification to the `run_tick` monolith, keeping it minimal and predictable.**

4.  **Agent-Level Behavioral Modification:**
    - The actual *behavioral changes* during a scenario are implemented entirely within the agents' decision-making methods (`make_decision`).
    - These methods will read the `StressScenarioConfig` DTO they receive as an argument and modify their logic accordingly (e.g., `if scenario_config.panic_selling_enabled:`).
    - This respects the principle of agent autonomy and keeps complex conditional logic out of the `Simulation` engine.

By following this strategy, we can introduce powerful stress-testing capabilities while promoting better architectural hygiene, ensuring that the new features are modular, testable, and do not add to the project's existing technical debt.
```
