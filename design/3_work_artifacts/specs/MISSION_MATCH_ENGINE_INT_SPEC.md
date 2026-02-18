file: modules/market/api.py
```python
from __future__ import annotations
from typing import List, Dict, Any, Optional, Protocol, TypedDict, runtime_checkable
from dataclasses import dataclass, field
from simulation.models import Transaction

# Type Alias for clarity
AgentID = int
Penny = int

@dataclass
class CanonicalOrderDTO:
    """
    Standardized Order DTO for matching engines.
    Strictly uses Integer Pennies.
    """
    order_id: str
    agent_id: AgentID
    item_id: str
    quantity: float  # Quantity can be float (e.g. 0.5kg food)
    price_pennies: Penny
    is_buy: bool
    time: int
    expiration: int = 0
    # Targeted matching (Brand Loyalty / Specific Seller)
    target_agent_id: Optional[AgentID] = None
    brand_info: Optional[Dict[str, Any]] = None

@dataclass
class OrderBookStateDTO:
    """
    Snapshot of the Order Book passed to the engine.
    """
    market_id: str
    buy_orders: Dict[str, List[CanonicalOrderDTO]]  # item_id -> orders
    sell_orders: Dict[str, List[CanonicalOrderDTO]] # item_id -> orders

@dataclass
class StockMarketStateDTO:
    """
    Snapshot of the Stock Market Order Book.
    """
    market_id: str
    buy_orders: Dict[int, List[CanonicalOrderDTO]]  # firm_id -> orders
    sell_orders: Dict[int, List[CanonicalOrderDTO]] # firm_id -> orders

@dataclass
class MatchingResultDTO:
    """
    Result of a matching cycle.
    Includes executed transactions and remaining orders.
    """
    transactions: List[Transaction]
    unfilled_buy_orders: Dict[str, List[CanonicalOrderDTO]]
    unfilled_sell_orders: Dict[str, List[CanonicalOrderDTO]]
    # Market stats for updating History/Dashboard (Legacy float support allowed here only for display)
    market_stats: Dict[str, Any] 

@runtime_checkable
class IMatchingEngine(Protocol):
    """
    Interface for Matching Engines.
    Must be stateless and deterministic.
    """
    def match(self, state: OrderBookStateDTO | StockMarketStateDTO, current_tick: int) -> MatchingResultDTO:
        ...

```

file: design/3_work_artifacts/specs/matching_engine_int_math_spec.md
```markdown
# Spec: Matching Engine Integer Math Hardening

## 1. Overview
- **Goal**: Refactor `MatchingEngine` (Goods/Labor) and `StockMatchingEngine` to use strict Integer Math (Pennies) for all value calculations.
- **Scope**: Internal matching logic, price discovery, and transaction generation.
- **Constraint**: Must eliminate "Financial Dust" (floating point residuals) that causes M2 drift.
- **Mandate**: **Zero-Sum Integrity**. The amount deducted from Buyer MUST exactly match amount added to Seller.

## 2. Architecture & Principles

### 2.1. Integer-First Logic
- **Prices**: All inputs and internal comparisons use `price_pennies` (int).
- **Execution Value**: `total_pennies` is the primary truth. `unit_price` is derived.
- **Rounding Rule**: **FLOOR** (Round Down).
    - Logic: `total_pennies = int(execution_price_pennies * quantity)`
    - This ensures we never create value out of thin air. Any fractional penny value remains with the buyer (i.e., not spent).

### 2.2. Mid-Price Discovery
When a generic buy order matches a sell order:
- **Formula**: `execution_price_pennies = (bid_pennies + ask_pennies) // 2`
- **Integrity**: Integer division `//` automatically floors.

### 2.3. Zero-Sum Enforcement
- The `Transaction` object must be constructed with `total_pennies`.
- `Transaction.price` (float) is retained for UI/Legacy compatibility but must be strictly derived: `total_pennies / 100.0 / quantity` (if quantity > 0).

## 3. Detailed Logic (Pseudo-code)

### 3.1. `_match_item` / `_match_firm_stock`

```python
def calculate_trade_value(buyer_order, seller_order, market_type):
    # 1. Determine Execution Price (Per Unit)
    if market_type in ['labor', 'research_labor']:
        # Labor Market: Buyer (Employer) pays their bid (Wage) - distinct from goods
        # Or usually strictly based on the existing deal. 
        # For open market: Average? 
        # Current logic: price = b_wrapper.dto.price_pennies (Buyer Power?) 
        # REVISION: Stick to Mid-Price for generic, or Bid price if Labor specific.
        # Let's standardize on Mid-Price for open markets to be fair, 
        # unless spec says otherwise.
        # PRESERVING LEGACY BEHAVIOR for Labor: "trade_price_pennies = b_wrapper.dto.price_pennies"
        execution_price_pennies = buyer_order.price_pennies
    else:
        # Goods/Stock: Mid-Point
        execution_price_pennies = (buyer_order.price_pennies + seller_order.price_pennies) // 2

    # 2. Determine Quantity
    trade_qty = min(buyer_order.remaining_qty, seller_order.remaining_qty)
    
    # 3. Calculate Total Value (The Source of Truth)
    # Using float quantity * int pennies -> float -> int cast (FLOOR)
    trade_total_pennies = int(execution_price_pennies * trade_qty)
    
    # 4. Guard: Minimum Transaction
    if trade_total_pennies == 0 and trade_qty > 0:
        # Edge case: Quantity too small to worth 1 penny.
        # Option A: No Trade.
        # Option B: Trade free (Charity).
        # Decision: NO TRADE if value < 1 penny.
        return None 

    return trade_total_pennies, trade_qty
```

### 3.2. Error Handling & Edge Cases
- **Quantity Precision**: `1e-09` used as epsilon for "zero quantity".
- **Zero Value Trade**: If `int(price * qty) == 0`, the trade is aborted to prevent free goods transfer (unless intended).

## 4. Verification Plan

### 4.1. New Test Cases (`tests/market/test_matching_int_math.py`)
- **Case 1: Odd Mid-Price**: Bid 101, Ask 100. Mid = 201 // 2 = 100. Seller gets 100. Buyer pays 100. Surplus 1 stays with Buyer.
- **Case 2: Fractional Quantity**: Price 100 pennies, Qty 0.33. Total = `int(33.0)` = 33 pennies.
- **Case 3: Zero-Sum Check**: Sum of `total_pennies` in all generated transactions matches `sum(buyer_deductions)` and `sum(seller_incomes)`.

### 4.2. Legacy Impact
- **`MatchingEngine.match`**: API signature changes slightly (type hinting hardening).
- **`Transaction` Model**: Ensure `total_pennies` is used by `SettlementSystem`.
- **Audits**: `audit_zero_sum.py` should show 0.0 drift.

## 5. Technical Debt Resolution
- **Resolves `TD-MKT-FLOAT-MATCH`**: Removes float logic from MatchingEngine.
- **Resolves `TD-CRIT-FLOAT-SETTLE`**: Provides clean integer inputs to Settlement.

## 6. Risk Assessment
- **Volume Drop**: Strict floor rounding might slightly reduce total trade volume in micro-transaction scenarios (high granularity, low price goods).
- **Labor Market**: Existing logic favors Buyer (Employer) setting wage. Changing this might affect wage inflation. (Kept as-is for now: `trade_price = b.price`).

## 7. Mandatory Reporting
- Insight Report: `communications/insights/spec-matching-engine-int-math.md`
- Contents: Confirmation of integer math use, rounding decisions, and Zero-Sum verification strategy.
```

file: communications/insights/spec-matching-engine-int-math.md
```markdown
# Insight Report: Matching Engine Integer Math Hardening

## 1. Architectural Decisions
- **Integer Supremacy**: Adopted `total_pennies = int(price_pennies * quantity)` with strictly `floor` rounding.
- **Mid-Price Logic**: Standardized on `(Bid + Ask) // 2` for Goods/Stock to ensure fair value distribution without creating fractional pennies.
- **Labor Exception**: Retained legacy behavior where Labor Price = Bid Price (Employer's Offer), acknowledging power dynamic in current simulation logic.

## 2. Technical Debt & Risks
- **TD-MKT-FLOAT-MATCH**: Addressed. The engine now produces `Transaction` objects with `total_pennies` derived directly from integer inputs.
- **Risk (Micro-Friction)**: Very small quantities of cheap goods might fail to trade if `price * qty < 1 penny`. This is an acceptable simulation of transaction costs/indivisibility of currency.

## 3. Verification Strategy
- **Zero-Sum**: The primary success metric is that `SettlementSystem` receives exact integers.
- **Test Plan**:
    - `test_mid_price_rounding`: Verify `(101+100)//2 = 100`.
    - `test_fractional_qty_value`: Verify `price 10 * qty 0.5 = 5`.
```