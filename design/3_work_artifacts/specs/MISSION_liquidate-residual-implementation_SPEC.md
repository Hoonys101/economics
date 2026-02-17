file: modules/market/api.py
```python
from __future__ import annotations
from typing import Protocol, List, Dict, Any, Optional, TypedDict, runtime_checkable
from dataclasses import dataclass
from modules.system.api import MarketContextDTO, MarketSignalDTO, AgentID, CurrencyCode

# Strict Type Alias for clarity - ensuring we mean Pennies/Integers
PennyAmount = int

@dataclass(frozen=True)
class PriceMatchResultDTO:
    """
    Result of a market matching execution using strict integer math.
    """
    clearing_price: PennyAmount
    volume: int
    buyer_surplus: PennyAmount
    seller_surplus: PennyAmount
    unfilled_buy_orders: int
    unfilled_sell_orders: int
    # Zero-sum check: total_paid_by_buyers must equal total_received_by_sellers

class IOrderBook(Protocol):
    """
    Protocol for a strict integer-based OrderBook.
    """
    def add_order(self, order: Any) -> None: ...
    def match(self) -> PriceMatchResultDTO: ...
    def get_depth(self) -> Dict[PennyAmount, int]: ...

@runtime_checkable
class IMatchingEngine(Protocol):
    """
    Interface for the Market Matching Engine.
    Refactored to enforce TD-MKT-FLOAT-MATCH resolution.
    """
    def match_orders(self, bids: List[Any], asks: List[Any]) -> PriceMatchResultDTO:
        """
        Executes the double-auction matching logic using Integer Math.
        
        Args:
            bids: List of Buy Orders (price is strictly PennyAmount)
            asks: List of Sell Orders (price is strictly PennyAmount)
            
        Returns:
            PriceMatchResultDTO containing the clearing price and execution details.
            
        Raises:
            PrecisionError: If float inputs are detected in critical price fields.
        """
        ...

    def calculate_clearing_price(self, aggregated_bids: Dict[PennyAmount, int], aggregated_asks: Dict[PennyAmount, int]) -> PennyAmount:
        """
        Determines the equilibrium price where supply meets demand.
        Must use integer division `//` and explicit rounding rules.
        """
        ...

@runtime_checkable
class ISalesEngine(Protocol):
    """
    Interface for the Sales Engine component of a Firm.
    Enforces integer pricing and precise inventory management.
    """
    
    def post_ask(self, state: Any, context: Any) -> Any: # Returns Order
        """
        Generates a Sell Order with a price guaranteed to be an integer (PennyAmount).
        """
        ...

    def check_and_apply_dynamic_pricing(self, state: Any, orders: List[Any], current_time: int, config: Any = None) -> None:
        """
        Applies dynamic pricing logic (e.g., clearance sales).
        Must ensure resultant prices are `max(cost_floor, calculated_price)` and cast to int.
        """
        ...
```

file: design/3_work_artifacts/specs/liquidate_residual_spec.md
```markdown
# Spec: Liquidate Residual Failures & Market Precision Refactor

## 1. Context & Objectives
This specification addresses persistent technical debt and residual test failures identified in `MISSION_liquidate_residual_and_precision_SPEC.md`. 
The primary goals are to:
1.  **Strictly Enforce Integer Math** in Market and Sales engines to resolve `TD-MKT-FLOAT-MATCH` (The "Financial Dust" problem).
2.  **Fix API Desync** in `WelfareService` regarding `BailoutCovenant`.
3.  **Harden FinanceEngine** against float/int mixing errors.

**Related Tech Debt**:
- `TD-MKT-FLOAT-MATCH`: Market Matching Engine Float Leakage.
- `TD-CRIT-FLOAT-SETTLE`: Float-to-Int Migration Bridge.

## 2. Component Specifications

### 2.1. Welfare Service (`modules/government/services/welfare_service.py`)
**Problem**: The `provide_firm_bailout` method constructs `BailoutCovenant` using the legacy argument `executive_salary_freeze`, which has been renamed to `executive_bonus_allowed` in the DTO definition.
**Refactor Logic**:
- **Update Construction**: Ensure `BailoutCovenant` is instantiated with correct keys.
- **Verification**: `modules/finance/api.py` defines the Source of Truth.

```python
# Target Implementation Update
def provide_firm_bailout(self, firm: IAgent, amount: int, ...) -> Optional[BailoutResultDTO]:
    # ... logic ...
    loan_dto = BailoutLoanDTO(
        # ...
        covenants=BailoutCovenant(
            dividends_allowed=False,
            executive_bonus_allowed=False,  # REPLACES executive_salary_freeze
            min_employment_level=None       # Explicitly set defaults
        )
    )
    # ...
```

### 2.2. Sales Engine (`simulation/components/engines/sales_engine.py`)
**Problem**: Pricing logic occasionally drifts into floats due to multipliers (dynamic pricing, marketing adjustments), creating `Order` objects with float prices that crash downstream integer-expecting systems.
**Refactor Logic**:
1.  **Post Ask**: Ensure `context.price` is cast to `int` before Order creation.
2.  **Dynamic Pricing**:
    -   Calculation: `discounted_price = int(original_price * reduction_factor)`
    -   Floor Check: `max(discounted_price, unit_cost_pennies)`
    -   **CRITICAL**: Explicitly cast final value to `int` before updating `Order.price_limit`.

### 2.3. Finance Engine (`simulation/components/engines/finance_engine.py`)
**Problem**: `holding_cost` and `valuation` calculations mix float rates with integer bases, leading to implicit float returns.
**Refactor Logic**:
-   **Holding Cost**: `holding_cost_pennies = int(inventory_value_pennies * rate)` (Use `math.floor` or `int()` truncation consistently).
-   **Valuation**: Ensure `avg_profit` (which comes from history) is handled carefully. If history contains floats, cast sum to int.

### 2.4. Matching Engine (`simulation/markets/matching_engine.py`)
**Problem**: Mid-price calculation uses `(best_bid + best_ask) / 2`, resulting in `.5` pennies.
**Refactor Logic**:
-   **Integer Division**: Use `(best_bid + best_ask) // 2`.
-   **Surplus Allocation**: Define explicit rule for the odd penny (e.g., "Buyer Advantage" or "Market Maker Capture").
-   **Execution**:
    ```python
    clearing_price = (bid_price + ask_price) // 2
    total_transaction_value = clearing_price * quantity
    ```

## 3. Data Transfer Objects (Impact Analysis)

### New/Modified DTOs
-   **No Schema Changes required** for `BailoutCovenant` (Correcting usage to match existing schema).
-   `PriceMatchResultDTO` (New internal DTO for MatchingEngine to formalize zero-sum check).

### API Contract Adherence
-   **Violations Found**: `WelfareService` violates `BailoutCovenant` contract (Fixing this).
-   **New Protocol**: `IMatchingEngine` defined in `modules/market/api.py` to enforce future compliance.

## 4. Verification Plan

### 4.1. Unit Tests
-   **Welfare**: `pytest tests/unit/modules/government/test_welfare_service.py`
    -   *Case*: `test_bailout_creates_valid_covenant`: Verify `executive_bonus_allowed` attribute exists on result.
-   **Sales**: `pytest tests/unit/components/test_sales_engine.py`
    -   *Case*: `test_dynamic_pricing_integers`: Set `reduction_factor=0.33`, price `100`. Result must be `33` (int), not `33.0`.
-   **Finance**: `pytest tests/unit/components/test_finance_engine.py`
    -   *Case*: `test_holding_cost_precision`: Inventory `12345`, rate `0.01`. Cost `123` (int).

### 4.2. Integration Audit
-   **Run**: `pytest tests/integration/test_m2_integrity.py` (if exists) or generic simulation run.
-   **Check**: M2 Delta must be exactly `0.0` after 100 ticks. Any float dust indicates failure.

## 5. Mandatory Reporting & Debt
-   **Report Location**: `communications/insights/liquidate-residual.md`
-   **Identified Debt**:
    -   `TD-MKT-FLOAT-MATCH` will be marked **RESOLVED** upon completion.
    -   **New Risk**: Aggressive integer truncation might slightly reduce liquidity if prices are very low (e.g., 1 penny).
```