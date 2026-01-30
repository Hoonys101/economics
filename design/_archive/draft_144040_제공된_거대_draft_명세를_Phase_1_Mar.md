# SPECIFICATION: Phase 1 - Market Infrastructure & Signals
**ID**: `SPEC_ANIMAL_PHASE1_MARKET`
**Parent**: `SPEC_ANIMAL_SPIRITS`

**Objective**: This specification defines the foundational data infrastructure for creating organic, agent-driven market stability. It isolates the first critical step from the larger 'Animal Spirits' initiative: establishing clean, reliable market signals. This is achieved by introducing a dedicated system observer and the core `MarketSignalDTO` data contract, and by relaxing the circuit breaker to facilitate initial price discovery.

---

## 1. New Component: System-Level Market Signal Observer

To maintain architectural purity and prevent agent logic from making direct, state-altering calls to the market, we introduce a new system-level component.

- **Component**: `MarketSignalObserver`
- **Location**: `modules/system/observers.py` (new file)
- **Purpose**: This component's sole responsibility is to read the state of all `OrderBookMarket` instances *after* the matching phase and produce a clean `MarketSnapshotDTO` containing calculated signals for the *next* tick's decision-making phase.

### 1.1. Execution Phase in Simulation Loop

The observer runs in a new, dedicated phase to ensure data integrity and prevent circular dependencies.

1.  **Phase 1**: Agent Decisions (Uses snapshot from T-1)
2.  **Phase 2**: Market Matching (Trades from T are executed)
3.  **`NEW` Phase 2.5: Market Observation**
    - The `MarketSignalObserver` runs.
    - It iterates through each market.
    - It calculates all fields for the `MarketSignalDTO`.
    - It assembles the `MarketSnapshotDTO` for tick T.
4.  **Phase 3**: State Updates (Consumption, production, etc.)
5.  *(Next Tick)* -> **Phase 1**: Agent Decisions (Uses snapshot from T)

### 1.2. Logic (Pseudo-code)

```python
# In MarketSignalObserver.run(markets: List[OrderBookMarket], current_tick: int) -> MarketSnapshotDTO:

all_market_signals: Dict[str, MarketSignalDTO] = {}
for market in markets:
    price_history = market.get_price_history(days=7)
    
    signal = MarketSignalDTO(
        market_id=market.market_id,
        item_id=market.item_id,
        best_bid=market.get_best_bid(),
        best_ask=market.get_best_ask(),
        last_traded_price=market.get_last_price(),
        price_history_7d=price_history,
        volatility_7d=calculate_std_dev(price_history) if len(price_history) > 1 else 0.0,
        order_book_depth_buy=market.get_buy_order_count(),
        order_book_depth_sell=market.get_sell_order_count(),
        is_frozen=market.is_frozen()
    )
    all_market_signals[market.item_id] = signal

# The new snapshot is stored and made available for the next tick's decision phase
return MarketSnapshotDTO(
    tick=current_tick,
    market_signals=all_market_signals
)
```

## 2. Core Data Contracts (`api.py`)

The following DTOs formalize the data exchange.

### 2.1. `MarketSignalDTO`

This DTO provides agents with essential, pre-calculated signals about a specific market's state. It is the primary output of the `MarketSignalObserver`.

- **`market_id` (str)**: Unique identifier for the market.
- **`item_id` (str)**: The item traded in this market.
- **`best_bid` (Optional[float])**: The highest price a buyer is willing to pay.
- **`best_ask` (Optional[float])**: The lowest price a seller is willing to accept.
- **`last_traded_price` (Optional[float])**: The price of the last successful transaction.
- **`price_history_7d` (List[float])**: A list of the last 7 closing prices.
- **`volatility_7d` (float)**: The standard deviation of `price_history_7d`, a measure of price stability.
- **`order_book_depth_buy` (int)**: The total number of outstanding buy orders.
- **`order_book_depth_sell` (int)**: The total number of outstanding sell orders.
- **`is_frozen` (bool)**: True if the circuit breaker is active or no trades are occurring.

### 2.2. `MarketSnapshotDTO` (Modified)

This is a core data contract and its modification is a **breaking change**. It now embeds the market signals.

- **`tick` (int)**: The simulation tick when the snapshot was generated.
- **`market_signals` (Dict[str, MarketSignalDTO])**: A dictionary mapping `item_id` to its corresponding signal DTO.
- **`market_data` (Dict[str, Any])**: **[DEPRECATED]** Legacy field, to be phased out. Maintained for temporary compatibility.

## 3. Market: Circuit Breaker Relaxation (History-Free Discovery)

To prevent market seizure at the start of the simulation when no price history exists, the circuit breaker's bounds will be widened.

- **Location**: `simulation.markets.order_book_market.OrderBookMarket.get_dynamic_price_bounds`
- **Logic**: Modify the existing method to check the length of the price history.

### 3.1. Logic (Pseudo-code)

```python
# In OrderBookMarket.get_dynamic_price_bounds

min_history_len = self.config_module.CIRCUIT_BREAKER_MIN_HISTORY
price_history = self.price_history.get(self.item_id, [])

# If history is too sparse, allow any price to establish a baseline.
if len(price_history) < min_history_len:
    # --- WIDENED BOUNDS FOR PRICE DISCOVERY ---
    self.logger.debug(f"History-Free Discovery: Widening bounds for {self.item_id}.")
    return (0.0, float('inf'))

# ... existing logic for calculating bounds based on volatility ...
# If sufficient history exists, calculate bounds normally.
mean_price = sum(price_history) / len(price_history)
std_dev = calculate_std_dev(price_history)
# ... etc. ...
```

## 4. Verification Plan

1.  **Unit Tests**:
    - `TestMarketSignalObserver`:
        - Given a mock market with orders and a price history, verify the observer correctly calculates `volatility_7d`, captures `best_bid`/`best_ask`, and sets `is_frozen`.
    - `TestCircuitBreakerRelaxation`:
        - In `TestOrderBookMarket`, call `get_dynamic_price_bounds`.
        - Verify it returns `(0.0, inf)` when the market's price history is shorter than `CIRCUIT_BREAKER_MIN_HISTORY`.
        - Verify it returns correctly calculated, finite bounds when the history is sufficient.

2.  **🚨 Golden Fixture Invalidation Mandate**:
    - This change **guarantees invalidation** of nearly all existing economic outcome tests and golden fixtures. The economic assumptions underpinning those tests are fundamentally altered by this new price discovery mechanism.
    - **Required Work Item**: After the full `SPEC_ANIMAL_SPIRITS` feature set is implemented and merged, a dedicated task MUST be created to perform a full review and regeneration of all golden fixtures using `scripts/fixture_harvester.py`. This cost is understood and accepted.

## 5. Risk & Impact Audit (Addressing Pre-flight Check)

This specification explicitly addresses all architectural risks identified in the pre-flight audit.

-   **1. System-Level Observer**: This spec formally defines the `MarketSignalObserver` (Section 1) as the sole, explicit owner of signal calculation. Its position in the simulation loop (Phase 2.5) is defined to prevent data hazards and circular dependencies.
-   **2. Core Data Contract Modification**: We acknowledge that modifying `MarketSnapshotDTO` is a critical, breaking change (Section 2.2). This is a planned and necessary step to enforce architectural purity. All agent decision engines will require updates to parse the new structure, which will be handled in subsequent implementation phases.
-   **3. Guaranteed Test Invalidation**: The Verification Plan (Section 4) explicitly acknowledges the invalidation of existing tests and mandates the regeneration of Golden Fixtures as a non-negotiable follow-up task.

---
```python
# modules/system/api.py
from __future__ import annotations
from typing import TypedDict, List, Dict, Optional, Any

# --- DTOs for Market Stability Signals ---

class MarketSignalDTO(TypedDict):
    """
    Provides agents with essential, pre-calculated signals about a specific market's state.
    This is generated by the MarketSignalObserver after each trading round to ensure data purity
    for the next decision-making phase.
    """
    market_id: str
    item_id: str
    best_bid: Optional[float]
    best_ask: Optional[float]
    last_traded_price: Optional[float]
    price_history_7d: List[float]  # Rolling 7-tick price history
    volatility_7d: float  # Standard deviation of price_history_7d
    order_book_depth_buy: int  # Number of outstanding buy orders
    order_book_depth_sell: int  # Number of outstanding sell orders
    is_frozen: bool  # True if circuit breaker is active or no trades have occurred recently

# --- Modifications to Existing Core DTOs ---

class MarketSnapshotDTO(TypedDict):
    """
    [MODIFIED] A snapshot of all relevant market data for a given tick.
    This is a breaking change. The snapshot now contains a structured dictionary
    of market signals instead of raw, unstructured data.
    """
    tick: int
    market_signals: Dict[str, MarketSignalDTO]  # item_id -> signal_dto
    market_data: Dict[str, Any]  # [DEPRECATED] For legacy compatibility during transition.

class DecisionContext(TypedDict):
    """
    [MODIFIED] The complete context provided to a decision engine.
    The market_snapshot field is updated to the new structure, which will
    require all decision engines to be updated to parse it correctly.
    """
    state: "HouseholdStateDTO"  # or FirmStateDTO
    config: "HouseholdConfigDTO"  # or FirmConfigDTO
    goods_data: List[Dict[str, Any]]
    market_snapshot: MarketSnapshotDTO
    current_time: int
    # ... other existing fields
```
