# Market Design Issues and Plan for Next Session

This document outlines critical market design problems identified in the economic simulation and proposes solutions to be addressed in the next development session.

## 1. Problem: Inelastic Food Demand & Lack of Luxury Goods

### Problem Recognition
The current "food" item in the simulation appears to behave as a perfectly inelastic good. This means its demand does not significantly change with price fluctuations, which masks the expected supply-demand dynamics. Consequently, the previous verification of the law of supply and demand (P1 in MASTER_PLAN.md) did not fully support the economic principle. The original intention was to introduce luxury food items to observe more elastic demand behavior.

### Impact
This limitation reduces the economic realism of the market dynamics and prevents the observation of nuanced consumer responses to price changes, particularly for goods with varying elasticities.

### Proposed Solution for Next Session
1.  **Verify Current "Food" Elasticity:** Examine `data/goods.json` and `simulation/core_agents.py` to understand how "food" is currently defined, its utility, and how its consumption is modeled. Confirm if its behavior is indeed perfectly inelastic.
2.  **Define Luxury Food Item:** Ensure a luxury food item is properly defined in `data/goods.json`. This definition should include appropriate utility characteristics and a clear `is_luxury` flag.
3.  **Adjust Household Consumption Logic for Luxury Goods:** Modify `simulation/core_agents.py` and `simulation/decisions/household_decision_engine.py` to enable households to make consumption decisions that consider luxury goods. This logic should incorporate factors such as household wealth, social status needs, and the price elasticity of luxury items.
4.  **Re-run Supply-Demand Experiment:** After implementing the above changes, re-run the supply-demand experiment, specifically focusing on the newly introduced luxury food item, to verify if the law of supply and demand is observable.

## 2. Problem: Single Purchase Item & Indifference Curve Limitation

### Problem Recognition
Households in the current simulation model primarily decide on a single purchase item at a time. This fundamental constraint prevents the derivation of indifference curves, which are essential for understanding comprehensive consumer preferences and trade-offs between different goods.

### Impact
This limitation significantly reduces the economic realism of consumer behavior. The simulation cannot accurately model:
*   **Substitution Effects:** How consumers might switch between different goods when their relative prices change.
*   **Income Effects:** How changes in a household's purchasing power affect their demand for various goods.
*   **Diverse Consumption Patterns:** All households tend to exhibit very similar, simplified consumption behaviors, lacking the diversity seen in real economies.

### Proposed Solution for Next Session
1.  **Enable Multi-Item Consumption:** The immediate priority is to expand the household decision-making process to allow for the consideration and potential purchase of multiple types of goods within a single simulation tick or decision cycle.
2.  **Modify Decision Logic:** Update `simulation/core_agents.py` (specifically the `decide_and_consume` method) and `simulation/decisions/household_decision_engine.py` to support a more complex consumption decision process. This will involve:
    *   Evaluating multiple needs simultaneously.
    *   Considering the utility derived from various goods.
    *   Allocating budget across different goods.
3.  **Integration with Luxury Goods:** This solution will naturally integrate with the introduction of luxury goods, allowing households to choose between necessities and luxuries based on their current state and preferences.

These two problems are interconnected, and addressing the multi-item consumption will be key to observing more realistic market dynamics, including the law of supply and demand for various goods.