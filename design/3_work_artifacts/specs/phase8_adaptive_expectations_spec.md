# W-1 Specification: Phase 8 - Adaptive Price Expectations (The Psychology of Inflation)

> **Goal**: Introduce "Time" and "Fear" into Consumer Logic.
> **Core Concept**: Adaptive Expectations Hypothesis ($\pi^e_{t+1} = \pi^e_t + \lambda (\pi_t - \pi^e_t)$)

## 1. Overview
Currently, Agents are "Goldfish" (Memory-less). They only see the Current Price.
We will turn them into "Speculators" who fear inflation and hope for deflation.
This enables Macro-Emergent Phenomena: **Bubbles** (Hoarding) and **Crashes** (Demand Collapse).

## 2. Cognitive Model: Price Memory & Expectation
Target: `Household` Agent (`simulation/core_agents.py`)

### 2.1 Attributes
*   `self.price_history`: Dict[ItemID, Deque[float]] (Max Len: 10)
    *   Stores recent average transaction prices.
*   `self.expected_inflation`: Dict[ItemID, float]
    *   Agent's belief about next tick's price change rate (e.g., 0.05 = +5%).
*   `self.adaptation_rate` ($\lambda$): float (0.0 ~ 1.0)
    *   How fast they update beliefs.
    *   **Logic**:
        *   `IMPULSIVE`: 0.8 (Fast reaction, panic prone)
        *   `CONSERVATIVE`: 0.1 (Slow reaction)
        *   Others: 0.3

### 2.2 Update Logic (Every Tick)
1.  **Observe**: Use `perceived_avg_prices` (already implemented) or fetch pure market avg.
2.  **Calculate Current Inflation ($\pi_t$)**:
    $$ \pi_t = \frac{P_t - P_{t-1}}{P_{t-1}} $$
3.  **Update Expectation ($\pi^e$)**:
    $$ \pi^e_{t+1} = \pi^e_t + \lambda (\pi_t - \pi^e_t) $$

---

## 3. Behavioral Modification: Hoarding & Delay
Target: `decide_and_consume` logic

### 3.1 The Panic Buying (Hoarding)
*   **Trigger**: If $\pi^e >$ `PANIC_THRESHOLD` (e.g., 0.05)
*   **Action**: Increase Target Quantity.
    *   `New_Qty = Base_Need * (1 + HOARDING_FACTOR)`
*   **Effect**: Creates "Phantom Demand" -> Price Rises further -> Spiral.

### 3.2 The Deflationary Wait (Delay)
*   **Trigger**: If $\pi^e <$ `-DELAY_THRESHOLD` (e.g., -0.05)
*   **Action**: Decrease Target Quantity (Only buy minimum survival amt).
    *   `New_Qty = Base_Need * (1 - DELAY_FACTOR)`
*   **Effect**: Demand vanishes -> Price Crashes -> Spiral.

---

## 4. Configuration (`config.py`)
Add these constants:

```python
# Phase 8: Inflation Psychology
INFLATION_MEMORY_WINDOW = 10     # Ticks to remember
ADAPTATION_RATE_IMPULSIVE = 0.8
ADAPTATION_RATE_NORMAL = 0.3
ADAPTATION_RATE_CONSERVATIVE = 0.1

PANIC_BUYING_THRESHOLD = 0.05   # Expecting >5% price hike
HOARDING_FACTOR = 0.5           # Buy 50% more

DEFLATION_WAIT_THRESHOLD = -0.05 # Expecting >5% price drop
DELAY_FACTOR = 0.5              # Buy 50% less
```

## 5. Verification
*   **Scenario**: Artificial Supply Shock. 
    *   Cut Food Supply by 50%.
    *   Price rises.
    *   **Check**: Does Demand **Increase** (Panic Buy) despite higher price? (Counter-intuitive but correct for Bubble).
