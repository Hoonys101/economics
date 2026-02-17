File: modules\market\api.py
```python
from __future__ import annotations
from typing import List, Dict, Any, Optional, Protocol, TypedDict, Union, runtime_checkable
from dataclasses import dataclass, field
from modules.simulation.api import AgentID

# Define Currency Code
CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode = "USD"

@dataclass(frozen=True)
class CanonicalOrderDTO:
    """
    Immutable representation of an order in the matching engine.
    MIGRATION (TD-MKT-FLOAT-MATCH): 'price_limit' (float) is deprecated in favor of 'price_pennies' (int).
    For now, both are kept for transition, but 'price_pennies' is the Source of Truth for matching.
    """
    id: str = field(default_factory=lambda: "unknown") # Order ID
    agent_id: AgentID
    side: str # "BUY" or "SELL"
    item_id: str
    quantity: float # Remaining quantity
    price_pennies: int # Integer pennies (The SSoT)
    price_limit: float # Legacy float representation (for UI/Logging)
    market_id: str
    target_agent_id: Optional[AgentID] = None # For targeted orders (e.g. loyalty)
    brand_info: Optional[Dict[str, Any]] = None # Quality/Brand data

@dataclass
class OrderBookStateDTO:
    """
    Snapshot of the order book passed to the stateless MatchingEngine.
    """
    buy_orders: Dict[str, List[CanonicalOrderDTO]] # item_id -> List[Order]
    sell_orders: Dict[str, List[CanonicalOrderDTO]] # item_id -> List[Order]
    market_id: str

@dataclass
class MatchingResultDTO:
    """
    Result of a matching cycle.
    """
    transactions: List[Any] # List[Transaction] - keeping Any to avoid circular import with models
    unfilled_buy_orders: Dict[str, List[CanonicalOrderDTO]]
    unfilled_sell_orders: Dict[str, List[CanonicalOrderDTO]]
    market_stats: Dict[str, Any] # e.g. {"last_prices": {...}, "volume": {...}}

@runtime_checkable
class IMatchingEngine(Protocol):
    """
    Protocol for a Stateless Matching Engine.
    Enforces the separation of matching logic (Engine) from state management (Market).
    """
    def match(self, state: OrderBookStateDTO, current_tick: int) -> MatchingResultDTO:
        """
        Executes the matching algorithm on the provided state.
        Returns the set of generated transactions and the remaining unfilled orders.
        """
        ...

class MarketSignalDTO(TypedDict):
    """
    Lightweight DTO for broadcasting market data.
    """
    item_id: str
    best_bid_pennies: int
    best_ask_pennies: int
    last_price_pennies: int
    volume: float
    tick: int

```

File: design\3_work_artifacts\specs\market_precision_spec.md
```markdown
# Spec: Market Precision Refactor (Integer Math)

## 1. Introduction
This specification outlines the refactoring of the `MatchingEngine` and `OrderBookMarket` to utilize **Integer Math (Pennies)** for all price discovery and execution logic. This resolves **TD-MKT-FLOAT-MATCH** by eliminating floating-point drift in the critical financial path, ensuring strict Zero-Sum integrity.

### 1.1 Goals
- **Eliminate Floats**: All internal price calculations must use `int` (pennies).
- **Zero-Sum Integrity**: `Amount Paid (Buyer) == Amount Received (Seller)`. No fractional pennies created or destroyed.
- **Deterministic Rounding**: Standardize on a "Floor" strategy for exchange rates involving non-integer quantities.

## 2. Architecture & Data Structures

### 2.1 DTO Updates (`modules/market/api.py`)
- **`CanonicalOrderDTO`**:
  - Add `price_pennies: int`.
  - Deprecate `price_limit: float` (mark for removal in Phase 4).
  - **Migration**: During initialization, `OrderBookMarket` must convert incoming float inputs to pennies (`int(price * 100)`).

### 2.2 Matching Engine Logic (`simulation/markets/matching_engine.py`)

#### 2.2.1 Mid-Price Calculation
The legacy `(bid + ask) / 2` float formula is replaced with:
```python
mid_price_pennies = (buyer_order.price_pennies + seller_order.price_pennies) // 2
```
- **Implication**: Any fractional remainder (0.5 penny) is effectively floored. This implies a slight bias towards the "Taker" (if we consider the aggressor) or simply a market friction that benefits neither.
- **Note**: This preserves integer integrity.

#### 2.2.2 Execution Value Calculation
For goods/labor where quantity might be `float` (e.g., 8.5 hours):
```python
# Standard: Price per Unit * Quantity
gross_value = mid_price_pennies * trade_quantity
# Settlement Value (Integer)
total_pennies = int(gross_value) 
# Note: Python int() acts as floor().
```
- **Zero-Sum**: The `Transaction` object will store `price` as `total_pennies / quantity` (for display) or better, we modify `Transaction` to carry `total_amount_pennies`.
- **Constraint**: Since `Transaction` is a shared model, we will calculate the effective float price `total_pennies / quantity` for the `price` field to maintain compatibility, but the **SettlementSystem** must prefer `total_pennies` if available.

### 2.3 Residual Penny Analysis
- **Scenario**: Price 100 pennies, Qty 0.33. Gross = 33.33. Settle = 33.
- **Outcome**: 0.33 pennies of "theoretical value" is lost.
- **Decision**: This is acceptable. The system cannot transact fractional pennies. The "Loss" is a reduction in velocity, not a leak of actual money supply (M2), as M2 is defined by the integer balances in wallets.

## 3. Implementation Steps

### 3.1 Step 1: DTO & Protocol Migration
- Update `CanonicalOrderDTO` in `modules/market/api.py`.
- Update `OrderBookMarket.place_order` to populate `price_pennies`.

### 3.2 Step 2: Engine Refactor
- Rewrite `OrderBookMatchingEngine._match_item` and `_match_firm_stock`.
- **Constraint**: Do not use `float` comparisons for price. Use `price_pennies`.

### 3.3 Step 3: Transaction Generation
- Ensure `Transaction` objects created in the engine are based on the integer totals.
- **Formula**:
  ```python
  trade_price_pennies = (b.price_pennies + s.price_pennies) // 2
  trade_total_pennies = int(trade_price_pennies * trade_qty)
  # Back-calculate float price for legacy compatibility
  effective_price = trade_total_pennies / trade_qty if trade_qty > 0 else 0
  ```

## 4. Verification Plan

### 4.1 New Test Cases
- `test_market_zero_sum_integer()`: 
  - Place Buy @ 100 pennies, Sell @ 99 pennies. 
  - Verify Mid = 99 (floor of 99.5). 
  - Verify Buyer Balance -99, Seller Balance +99.
- `test_market_fractional_qty_rounding()`:
  - Price 10, Qty 0.3. Total = 3. 
  - Verify transfer is exactly 3 pennies.

### 4.2 Legacy Impact
- `matching_engine.py` is a drop-in replacement. Existing tests using floats might fail if they expect exact float mid-points.
- **Action**: Update `tests/markets/test_matching_engine.py` to assert integer-aligned results.

## 5. Risk Assessment (Audit)
- **[Critical]**: `Transaction.price` (float) is widely used by Agents for learning.
  - **Mitigation**: The back-calculated `effective_price` ensures agents still see a valid unit price, even if it varies slightly due to rounding.
- **[Medium]**: `OrderBookMarket` history (volatility) uses floats.
  - **Decision**: Keep history as floats for statistical analysis. The strict integer math is only for **Settlement**.

## 6. Technical Debt Ledger (Updates)
- **Resolved**: `TD-MKT-FLOAT-MATCH` (upon implementation).
- **New**: `TD-TRANS-INT-SCHEMA`: `Transaction` model still relies on float `price` as primary carrier. Needs schema migration to `amount_pennies`.
```

File: communications\insights\market-precision-spec.md
```markdown
# Insight Report: Market Precision Spec

## 1. Architectural Insights
- **Pivot to Pennies**: The refactor of `MatchingEngine` to use `price_pennies` is the final step in the "Penny Standard" migration.
- **Zero-Sum Enforcement**: By using `// 2` for mid-price and `int()` for total value, we guarantee that the amount debited from the Buyer is **exactly** equal to the amount credited to the Seller.
- **Integration Friction**: The `Transaction` model is a shared artifact. While we are changing the *engine* to use integers, the *output* (Transaction) still expects a float `price`. We are bridging this by back-calculating `effective_price = total_pennies / quantity`. This allows legacy agents to continue functioning without a breaking schema change, but it introduces a "Soft Debt" where `price * quantity` might slightly deviate from `total_pennies` if re-calculated in float.

## 2. Technical Debt & Risks
- **TD-TRANS-INT-SCHEMA**: The `Transaction` object is the next bottleneck. It needs to be upgraded to store `total_pennies` explicitly to avoid float division artifacts during settlement.
- **Agent Learning**: Agents training on `price` history might see slightly more "step-like" behavior due to integer flooring. This is actually more realistic (tick size).

## 3. Mandatory Ledger Audit
- **Analyzed**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Action**: This spec directly addresses **TD-MKT-FLOAT-MATCH** (Critical).
- **Risk**: Does not exacerbate `TD-CRIT-FLOAT-SETTLE` but rather aligns the Market upstream with the Settlement downstream.

## 4. Verification Strategy
- A new test file `tests/market/test_precision_matching.py` will be required to validate the integer math specifically.
- **Pass Criteria**: `sum(buyer_deltas) + sum(seller_deltas) == 0` over 1,000,000 random trades.
```