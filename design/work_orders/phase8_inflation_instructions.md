# W-2 Work Order: Phase 8 - The Psychology of Inflation (Adaptive Expectations)

> **Assignee**: Jules
> **Priority**: P1 (Macro Logic)
> **Branch**: `feature/inflation-psychology`
> **Base**: `main`

---

## 📋 Overview
> **Goal**: Agents must "remember" past prices and "predict" future inflation.
> **Current State**: Agents are memory-less (Markovian).
> **Target State**: Agents use Adaptive Expectations ($\pi^e_{t+1} = \pi^e_t + \lambda (\pi_t - \pi^e_t)$) to hoard (panic buy) or delay consumption.

## 📄 References
- **Master Spec**: `design/specs/phase8_adaptive_expectations_spec.md`

---

## ✅ Implementation Steps

### 1. Config Update (`config.py`)
Add the following constants (adjust values if needed during tuning):
```python
# Phase 8: Inflation Psychology
INFLATION_MEMORY_WINDOW = 10     # Ticks to remember price history
ADAPTATION_RATE_IMPULSIVE = 0.8  # Lambda for impulsive agents
ADAPTATION_RATE_NORMAL = 0.3     # Lambda for normal agents
ADAPTATION_RATE_CONSERVATIVE = 0.1 # Lambda for conservative agents

PANIC_BUYING_THRESHOLD = 0.05    # Expected Inflation > 5% -> Hoard
HOARDING_FACTOR = 0.5            # Buy 50% more than needed

DEFLATION_WAIT_THRESHOLD = -0.05 # Expected Inflation < -5% -> Delay
DELAY_FACTOR = 0.5               # Buy 50% less than needed
```

### 2. Household Attributes (`simulation/core_agents.py`)
In `Household.__init__`:
- `self.price_history`: Dict[str, Deque[float]] (Max len: `INFLATION_MEMORY_WINDOW`)
- `self.expected_inflation`: Dict[str, float] (Default 0.0)
- `self.adaptation_rate`: float
    - **Logic**:
        - `IMPULSIVE` / `STATUS_SEEKER`: `ADAPTATION_RATE_IMPULSIVE`
        - `CONSERVATIVE` / `MISER`: `ADAPTATION_RATE_CONSERVATIVE`
        - Others: `ADAPTATION_RATE_NORMAL`

### 3. Perception Logic Update
In `Household.update_perceived_prices(market_data)`:
1.  **Record History**: Append current market price to `price_history[item_id]`.
2.  **Calc Current Inflation ($\pi_t$)**:
    - `pi_t = (current_price - last_price) / last_price`
    - (Handle zero/missing history gracefully)
3.  **Update Expectation ($\pi^e$)**:
    - `new_pi_e = old_pi_e + self.adaptation_rate * (pi_t - old_pi_e)`
    - Update `self.expected_inflation[item_id]`.

### 4. Consumption Logic Update
In `Household.decide_and_consume` (or `consume`):
- Before consuming/buying, check `self.expected_inflation[item_id]`.
- **Panic Buying**:
    - If `pi_e > PANIC_BUYING_THRESHOLD`:
    - `quantity *= (1 + HOARDING_FACTOR)`
    - Log: "PANIC BUYING! Expecting inflation..."
- **Deflationary Wait**:
    - If `pi_e < DEFLATION_WAIT_THRESHOLD`:
    - `quantity *= (1 - DELAY_FACTOR)`
    - Log: "DELAYING CONSUMPTION! Expecting deflation..."

---

## 🧪 Verification Plan
Create `scripts/verify_inflation_psychology.py`:
1.  **Supply Shock**: Force Firm to reduce production (or destroy inventory) for 10 ticks.
2.  **Price Monitor**: Confirm Market Price rises.
3.  **Behavior Monitor**:
    - Check `Household.expected_inflation`. Does it go positive?
    - Check Consumption Qty. Does it **increase** (Hoarding) even as price rises? (Paradoxical behavior)
