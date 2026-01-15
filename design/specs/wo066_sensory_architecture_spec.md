# Spec: WO-066 High-Fidelity Sensory Architecture

## 1. Overview
- **Goal**: Resolve the "Lag & Blindness" issue in the Government Agent's decision-making process.
- **Problem**: 
  1. Reliance on SMA (Simple Moving Average) masks immediate economic shocks.
  2. Zero-volume markets return `0.0` or unstable prices, causing policy hallucinations.
  3. Data synchronization timing in `Engine` allows the Government to act on stale data.
- **Solution**: 
  1. Introduce `Instant` vs `SMA` dual-channel signals.
  2. Implement `Last Known Price (LKP)` persistence logic in `EconomicIndicatorTracker`.
  3. Enforce "Capture -> Decide" strict ordering in `Engine.run_tick`.

## 2. Architecture & Data Flow

### 2.1 Data Structure (DTO Update: `GovernmentSensoryInputDTO`)
Updates `GovernmentStateDTO` to include instantaneous metrics.

| Field | Type | Description |
| :--- | :--- | :--- |
| `inflation_instant` | `float` | $(Price_{t} - Price_{t-1}) / Price_{t-1}$ |
| `inflation_sma` | `float` | 10-tick Simple Moving Average |
| `gdp_growth_instant` | `float` | $(GDP_{t} - GDP_{t-1}) / GDP_{t-1}$ |
| `gdp_growth_sma` | `float` | 10-tick SMA |
| `last_known_prices` | `Dict[str, float]` | Map of item_id to last valid price |

### 2.2 Component Roles
1.  **EconomicIndicatorTracker (The Retina)**:
    - Maintains a `price_memory: Dict[str, float]` to store LKP.
    - If `volume > 0`: Update `price_memory`.
    - If `volume == 0`: Return `price_memory` value (instead of 0 or OrderBook noise).
2.  **Engine (The Nervous System)**:
    - Calculates `Instant` metrics using `Tracker`'s latest snapshot.
    - Calculates `SMA` using internal `deque` buffers.
    - Packages both into DTO and feeds `Government`.
3.  **Government (The Brain)**:
    - Uses "Sensor Fusion" logic to weigh Trend vs Shock.

## 3. Logic Specification (Pseudo-code)

### 3.1 EconomicIndicatorTracker: Last Known Price Logic

```python
class EconomicIndicatorTracker:
    def __init__(self, ...):
        self.price_memory: Dict[str, float] = {} # Persistent memory
        # Initialize with config prices or 10.0

    def track(self, ...):
        for market_name in markets:
            if volume > 0:
                self.price_memory[market_name] = avg_price
            else:
                # Fallback Sequence: Best Ask -> Best Bid -> Last Known Price
                avg_price = self.price_memory.get(market_name, 10.0)
```

### 3.2 Engine: Synchronization & Signal Calculation

```python
def run_tick(self):
    # 1. Transactions Clear
    # 2. IMMEDIATE SYNC
    self.tracker.track(self.time, ..., money_supply=current_money)
    
    # 3. Calculate DTO (Dual Channel)
    instant_inflation = (curr_price - prev_price) / prev_price
    sma_inflation = buffer.average()
    
    # 4. Inject to Government
    self.government.update_sensory_data(sensory_dto)
    self.government.make_policy_decision(...)
```

## 4. Test Strategy
- **Golden Sample**: `tests/goldens/sensory_shock_test.json`
- **Test Case**:
    1. Tick 1-10: Stable prices. Verify SMA ~= Instant ~= 0.
    2. Tick 11: **Inject Price Shock** (x2.0). Verify `instant` > 0.9.
    3. Tick 12: **Zero Volume**. Verify `avg_price` maintains Tick 11 level (LKP).

---
**[Reporting Instruction]**:
Jules must report:
- Does the "Instant" signal cause volatility? (Overreaction check)
- Did LKP logic prevent "Flash Crashes" in illiquid markets?
