I will generate the implementation specification for WO-066 High-Fidelity Sensory Architecture and the corresponding API definition.

### 1. `modules/sensory/api.py`
This file defines the strict data contracts for the Sensory Architecture, ensuring the Government Agent receives structured, typed data.

```python
"""
modules/sensory/api.py
Sensory Architecture Interface Definitions.
Defines the data structures for economic sensing and government perception.
"""
from typing import TypedDict, Optional, List, Dict
from dataclasses import dataclass

# Uses existing DTOs from core where applicable, but defines specific Sensory structures here
# for strict contract enforcement before merging into global DTOs.

@dataclass
class SensorySignalDTO:
    """
    Individual sensory signal wrapping both trend (SMA) and immediate shock (Instant).
    """
    metric_name: str
    sma_value: float          # Simple Moving Average (Trend)
    instant_value: float      # Real-time value this tick (Shock)
    volatility: float         # Standard deviation or variance (Uncertainty)
    is_reliable: bool         # Data quality flag (e.g., false if missing data)

@dataclass
class GovernmentSensoryInputDTO:
    """
    WO-066: Enhanced Government Sensory Data.
    Replaces/Extends the previous GovernmentStateDTO for sensory inputs.
    """
    tick: int
    
    # Macro Indicators (Dual-Channel: Trend + Instant)
    inflation: SensorySignalDTO
    gdp_growth: SensorySignalDTO
    unemployment: SensorySignalDTO
    wage_growth: SensorySignalDTO
    
    # Political/Social
    approval_rating_sma: float
    public_sentiment_index: float  # Real-time sentiment
    
    # Fiscal Context
    debt_to_gdp_ratio: float
    budget_deficit_ratio: float

class ISensorySystem:
    """
    Interface for the Sensory System.
    Responsible for collecting, smoothing, and validating economic data.
    """
    def capture_snapshot(self, tick: int) -> None:
        """Captures the current economic state immediately after transactions."""
        ...

    def get_sensory_data(self, tick: int) -> GovernmentSensoryInputDTO:
        """Returns the processed sensory data for the Government Agent."""
        ...

    def get_last_known_price(self, item_id: str) -> float:
        """
        Returns the last valid transaction price for an item.
        Fallback mechanism for zero-volume markets.
        """
        ...
```

### 2. `design/specs/wo066_sensory_architecture_spec.md`
This is the detailed "Zero-Question" specification for the implementation.

```markdown
# Spec: WO-066 High-Fidelity Sensory Architecture

## 1. Overview
- **Goal**: Resolve the "Lag & Blindness" issue in the Government Agent's decision-making process.
- **Problem**: 
  1. Reliance on SMA (Simple Moving Average) masks immediate economic shocks (e.g., hyperinflation spikes).
  2. Zero-volume markets return `0.0` or unstable prices, causing policy hallucinations.
  3. Data synchronization timing in `Engine` allows the Government to act on stale data.
- **Solution**: 
  1. Introduce `Instant` vs `SMA` dual-channel signals.
  2. Implement `Last Known Price (LKP)` persistence logic in `EconomicIndicatorTracker`.
  3. Enforce "Capture -> Decide" strict ordering in `Simulation.run_tick`.

## 2. Architecture & Data Flow

### 2.1 Data Structure (DTO Update)
Update `GovernmentStateDTO` (or `GovernmentSensoryInputDTO`) to include instantaneous metrics.

| Field | Type | Description |
| :--- | :--- | :--- |
| `inflation_instant` | `float` | $(Price_{t} - Price_{t-1}) / Price_{t-1}$ |
| `inflation_sma` | `float` | 10-tick Simple Moving Average |
| `gdp_growth_instant` | `float` | $(GDP_{t} - GDP_{t-1}) / GDP_{t-1}$ |
| `gdp_growth_sma` | `float` | 10-tick SMA |
| `last_known_prices` | `Dict[str, float]` | Map of item_id to last valid price |

### 2.2 Component Roles
1.  **EconomicIndicatorTracker (The Retina)**:
    *   Maintains a `price_memory: Dict[str, float]` to store LKP.
    *   If `volume > 0`: Update `price_memory`.
    *   If `volume == 0`: Return `price_memory` value (instead of 0 or OrderBook noise).
2.  **Engine (The Nervous System)**:
    *   Calculates `Instant` metrics using `Tracker`'s latest snapshot.
    *   Calculates `SMA` using internal `deque` buffers.
    *   Packages both into DTO and feeds `Government`.
3.  **Government (The Brain)**:
    *   Uses a "Sensor Fusion" logic to weigh Trend vs Shock.

## 3. Logic Specification (Pseudo-code)

### 3.1 EconomicIndicatorTracker: Last Known Price Logic

```python
class EconomicIndicatorTracker:
    def __init__(self, ...):
        self.price_memory: Dict[str, float] = {} # Persistent memory
        # Initialize with config prices
        for good, details in config.GOODS.items():
            self.price_memory[good] = details['initial_price']

    def track(self, ...):
        # ... existing logic ...
        
        for market_name in markets:
            avg_price = market.get_daily_avg_price()
            volume = market.get_daily_volume()
            
            if volume > 0:
                # Update memory
                self.price_memory[market_name] = avg_price
            else:
                # Fallback 1: Best Ask (OrderBook)
                best_ask = market.get_best_ask()
                if best_ask > 0:
                     avg_price = best_ask
                else:
                    # Fallback 2: LKP (Memory)
                    avg_price = self.price_memory.get(market_name, 10.0)
            
            # Record avg_price to metrics...
```

### 3.2 Engine: Synchronization & Signal Calculation

```python
def run_tick(self):
    # 1. Process Transactions (Markets Clear)
    # ... match_orders() ...
    
    # 2. IMMEDIATE TRACKING (Sync)
    # Ensure tracker sees the result of the transactions just happened
    current_money = self._calculate_total_money()
    self.tracker.track(self.time, ..., money_supply=current_money)
    
    # 3. Calculate Sensory Signals (Dual Channel)
    latest = self.tracker.get_latest_indicators()
    
    # [Inflation]
    curr_price = latest['avg_goods_price']
    prev_price = self.last_avg_price_for_sma # State from t-1
    instant_inflation = (curr_price - prev_price) / prev_price if prev_price > 0 else 0.0
    
    self.inflation_buffer.append(instant_inflation)
    sma_inflation = sum(self.inflation_buffer) / len(self.inflation_buffer)
    
    # [GDP]
    curr_gdp = latest['total_production'] # Or Nominal GDP
    prev_gdp = self.last_gdp_for_sma
    instant_gdp = (curr_gdp - prev_gdp) / prev_gdp if prev_gdp > 0 else 0.0
    
    self.gdp_growth_buffer.append(instant_gdp)
    sma_gdp = sum(self.gdp_growth_buffer) / len(self.gdp_growth_buffer)
    
    # 4. Construct DTO
    sensory_dto = GovernmentStateDTO(
        tick=self.time,
        inflation_sma=sma_inflation,
        inflation_instant=instant_inflation, # NEW
        gdp_growth_sma=sma_gdp,
        gdp_growth_instant=instant_gdp,      # NEW
        current_gdp=curr_gdp,
        # ... other fields
    )
    
    # 5. Government Decide
    self.government.update_sensory_data(sensory_dto)
    self.government.make_policy_decision(...)
    
    # 6. Update State for Next Tick
    self.last_avg_price_for_sma = curr_price
    self.last_gdp_for_sma = curr_gdp
```

### 3.3 Government: Hybrid Decision Logic (SmartLeviathanPolicy)

```python
# In make_policy_decision or PolicyEngine
def perceive_crisis(self, sensory: GovernmentStateDTO) -> float:
    """
    Returns a 'Panic Score' (0.0 to 1.0)
    """
    # Weight: 70% Trend, 30% Shock
    # BUT, if Shock is extreme (> 50% change), ignore Trend
    
    weighted_inflation = (sensory.inflation_sma * 0.7) + (sensory.inflation_instant * 0.3)
    
    if abs(sensory.inflation_instant) > 0.5: # Hyper-shock
        logger.warning("HYPER_SHOCK DETECTED | Ignoring SMA")
        weighted_inflation = sensory.inflation_instant
        
    return weighted_inflation
```

## 4. Test Strategy
- **Golden Sample**: `tests/goldens/sensory_shock_test.json`
- **Test Case**:
    1. Tick 1-10: Stable prices (Volume > 0). Verify SMA ~= Instant ~= 0.
    2. Tick 11: **Inject Price Shock** (force market price * 2.0).
    3. Verify `GovernmentStateDTO.inflation_instant` > 0.9 (approx).
    4. Verify `GovernmentStateDTO.inflation_sma` is rising slowly.
    5. Tick 12: Zero Volume Tick.
    6. Verify `avg_goods_price` remains at Tick 11 level (LKP), not 0.

## 5. Insight Reporting (Mandatory)
Jules is required to report:
- Does the "Instant" signal cause the Government to overreact (volatility)?
- Did the LKP logic successfully prevent "Flash Crashes" in low-liquidity markets?
```
