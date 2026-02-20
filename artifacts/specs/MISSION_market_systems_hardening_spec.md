File: modules\market\api.py
```python
from __future__ import annotations
from typing import List, Dict, Any, Optional, Protocol, TypedDict, Union, Tuple
from dataclasses import dataclass, field
import math
from enum import Enum

# ==============================================================================
# 1. Fundamental Types & Constants
# ==============================================================================

class MarketSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

# ==============================================================================
# 2. Financial Precision Utilities (TD-MARKET-FLOAT-CAST Resolution)
# ==============================================================================

class MarketMath:
    """
    Centralized utility for financial precision and identifier handling.
    Enforces 'Penny Standard' via strict rounding.
    """
    
    @staticmethod
    def round_to_pennies(amount: float) -> int:
        """
        Converts a float dollar amount to integer pennies using standard rounding.
        Uses rounding half-up logic (0.5 -> 1) to avoid banker's rounding bias in fees.
        
        Args:
            amount: Float value (e.g., 10.505)
            
        Returns:
            int: Pennies (e.g., 1051)
        """
        # Python's round() is 'Round Half to Even'. 
        # For financial ledger safety, we typically prefer explicit behavior.
        # Here we map float dollars to pennies: 10.505 -> 1050.5 -> 1051
        return int(amount * 100.0 + 0.5) if amount >= 0 else int(amount * 100.0 - 0.5)

    @staticmethod
    def pennies_to_dollars(pennies: int) -> float:
        """Converts integer pennies to float dollars for display/logging."""
        return pennies / 100.0

# ==============================================================================
# 3. Identifier Standardization (TD-MARKET-STRING-PARSE Resolution)
# ==============================================================================

class StockSymbol:
    """
    Encapsulates the logic for Stock Item IDs.
    Prevents brittle string splitting logic in Engines.
    """
    PREFIX = "stock"
    SEPARATOR = "_"

    @classmethod
    def create(cls, firm_id: Union[int, str]) -> str:
        """Generates a canonical item_id for a firm's stock."""
        return f"{cls.PREFIX}{cls.SEPARATOR}{firm_id}"

    @classmethod
    def parse(cls, item_id: str) -> str:
        """
        Extracts the firm_id from a stock item_id.
        Raises ValueError if format is invalid.
        """
        parts = item_id.split(cls.SEPARATOR)
        if len(parts) != 2 or parts[0] != cls.PREFIX:
            raise ValueError(f"Invalid Stock Item ID format: {item_id}")
        return parts[1]
    
    @classmethod
    def is_valid(cls, item_id: str) -> bool:
        try:
            cls.parse(item_id)
            return True
        except ValueError:
            return False

# ==============================================================================
# 4. Data Transfer Objects (DTOs)
# ==============================================================================

@dataclass(frozen=True)
class CanonicalOrderDTO:
    """
    Immutable representation of an order.
    Replaces legacy dicts and StockOrder classes.
    """
    agent_id: Union[int, str]
    side: str  # "BUY" or "SELL"
    item_id: str
    quantity: float
    price_pennies: int
    price_limit: float  # Legacy/Display convenience
    market_id: str
    id: Optional[str] = None # Original Order ID if needed
    target_agent_id: Optional[Union[int, str]] = None
    brand_info: Optional[Dict[str, Any]] = None
    expiration_tick: Optional[int] = None

@dataclass
class OrderBookStateDTO:
    """
    Snapshot of the order book passed to the Matching Engine.
    Engine must NOT mutate this.
    """
    market_id: str
    buy_orders: Dict[str, List[CanonicalOrderDTO]]
    sell_orders: Dict[str, List[CanonicalOrderDTO]]

@dataclass
class StockMarketStateDTO:
    """
    Snapshot specifically for Stock Market matching.
    Keys are firm_ids (str).
    """
    market_id: str
    buy_orders: Dict[str, List[CanonicalOrderDTO]]
    sell_orders: Dict[str, List[CanonicalOrderDTO]]

@dataclass
class MatchingResultDTO:
    """
    Result returned by the Matching Engine.
    Contains executed transactions and the remaining state of orders.
    """
    transactions: List[Any]  # List[Transaction] - Any used to avoid circular import with simulation.models
    unfilled_buy_orders: Dict[str, List[CanonicalOrderDTO]]
    unfilled_sell_orders: Dict[str, List[CanonicalOrderDTO]]
    market_stats: Dict[str, Any]

# ==============================================================================
# 5. Interfaces / Protocols
# ==============================================================================

class IMatchingEngine(Protocol):
    """
    Protocol for Stateless Matching Engines.
    Must handle generic OrderBook matching or specialized Stock matching.
    """
    def match(self, state: Union[OrderBookStateDTO, StockMarketStateDTO], current_tick: int) -> MatchingResultDTO:
        ...

```

File: design\3_work_artifacts\specs\market_systems_spec.md
```markdown
# Specification: Market Systems Hardening (TD-MARKET)

## 1. Overview
This specification outlines the refactoring of the Market Matching Systems to address critical technical debt regarding financial precision and identifier fragility. The goal is to enforce "Penny Standard" integer math and encapsulate brittle string parsing logic.

### Objectives
1.  **Resolve `TD-MARKET-FLOAT-CAST`**: Replace unsafe `int()` casting with standard `round_to_pennies()` to prevent truncation errors in transaction totals.
2.  **Resolve `TD-MARKET-STRING-PARSE`**: Eliminate `item_id.split('_')` logic in `StockMatchingEngine` by introducing a `StockSymbol` utility.
3.  **Enforce Architectural Purity**: Ensure Matching Engines remain stateless and decoupled from specific Model implementations where possible.

---

## 2. Technical Debt Analysis

### 2.1. Float Casting (`TD-MARKET-FLOAT-CAST`)
*   **Current State**: `trade_total_pennies = int(trade_price_pennies * trade_qty)` in `matching_engine.py`.
*   **Problem**: Python's `int()` floors the result.
    *   Example: `100.99999` becomes `100`.
    *   Impact: Systematic under-payment/under-revenue in high-volume fractional trades, breaking "Zero-Sum" over time.
*   **Solution**: Implement `MarketMath.round_to_pennies()` utilizing `int(x + 0.5)` for positive numbers to ensure nearest-penny rounding.

### 2.2. String Parsing (`TD-MARKET-STRING-PARSE`)
*   **Current State**: `Transaction(..., item_id=f'stock_{firm_id}', ...)` and implicit splitting in various consumers.
*   **Problem**: Changing the ID format requires "Shotgun Surgery" across the codebase.
*   **Solution**: Introduce `StockSymbol` class in `modules.market.api` to centrally handle `create` and `parse` logic.

---

## 3. Detailed Design

### 3.1. API Updates (`modules/market/api.py`)
Refer to the generated `api.py` for the code definition of:
*   `class MarketMath`: Static utility for rounding.
*   `class StockSymbol`: Static utility for ID generation/parsing.

### 3.2. Logic Refactoring (`matching_engine.py`)

#### 3.2.1. Rounding Update
All matching engines (`OrderBookMatchingEngine`, `StockMatchingEngine`) must replace direct calculation with `MarketMath`:

```python
# BEFORE
trade_total_pennies = int(trade_price_pennies * trade_qty)

# AFTER
from modules.market.api import MarketMath
# ...
trade_total_pennies = MarketMath.round_to_pennies(trade_price_pennies * trade_qty)
```

#### 3.2.2. Stock ID Encapsulation
The `StockMatchingEngine` must explicitly use `StockSymbol` for transaction creation:

```python
# BEFORE
tx = Transaction(..., item_id=f'stock_{firm_id}', ...)

# AFTER
from modules.market.api import StockSymbol
# ...
tx = Transaction(..., item_id=StockSymbol.create(firm_id), ...)
```

### 3.3. Refactoring `_calculate_labor_utility` (SRP Fix)
The audit identified `_calculate_labor_utility` as an SRP violation inside the matching engine. While not the primary scope, we will move the calculation constant/logic to a protected helper or defer to a injected strategy if feasible. For this strict hardening phase, we will at least ensure it handles the `MarketMath` rounding if it involves price.

---

## 4. Verification Plan

### 4.1. Unit Tests (`tests/modules/market/test_api.py`)
*   **`MarketMath` Tests**:
    *   `test_round_to_pennies_exact`: `100.0` -> `10000`
    *   `test_round_to_pennies_fractional_up`: `10.005` -> `1001`
    *   `test_round_to_pennies_fractional_down`: `10.004` -> `1000`
*   **`StockSymbol` Tests**:
    *   `test_create_symbol`: `1` -> `"stock_1"`
    *   `test_parse_valid`: `"stock_50"` -> `"50"`
    *   `test_parse_invalid`: `"bond_50"` -> `ValueError`

### 4.2. Integration Regression (`tests/simulation/markets/test_matching_engine.py`)
*   **Precision Check**: Run existing matching scenarios.
    *   *Expected Behavior*: Some assert values might change by ±1 penny due to the fix from `floor` to `round`.
    *   *Action*: Update test expectations to reflect the *correct* (rounded) values.
*   **ID Contract Check**: Ensure stock transactions still route correctly to portfolios.

### 4.3. Audit Compliance
*   **Golden Data**: If the rounding changes alter the deterministic outcome of the "Golden" simulation run, the `tests/conftest.py` Golden Fixtures will need to be regenerated (`scripts/fixture_harvester.py`).

---

## 5. Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| **Test Failures (Precision)** | High | Medium | Bulk update of test assertions; verify manual math. |
| **Parsing Regression** | Low | High | Use `StockSymbol.is_valid` checks in `Transaction` init if possible. |
| **Performance Overhead** | Low | Low | Function call overhead for `round_to_pennies` is negligible compared to logic. |

---

## 6. Pre-Implementation Checklist
1.  [ ] Create `modules/market/api.py` with `MarketMath` and `StockSymbol`.
2.  [ ] Create unit tests for `MarketMath` and `StockSymbol`.
3.  [ ] Refactor `matching_engine.py` to import and use new API tools.
4.  [ ] Run `pytest tests/simulation/markets/test_matching_engine.py` and fix assertions.
5.  [ ] Run full suite to ensure no downstream settlement breakages.
```