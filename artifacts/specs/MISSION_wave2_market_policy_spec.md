# Spec: Wave 2 Market & Policy Refinement

## 1. Introduction
This specification addresses three critical technical debt items aimed at hardening the Market and Government domains for Phase 2 operations.
1.  **TD-DEPR-STOCK-DTO**: Complete the deprecation of legacy `StockOrder` by enforcing `CanonicalOrderDTO` in `StockMarket`.
2.  **TD-MARKET-STRING-PARSE**: Eliminate brittle string splitting in `StockMarket` by introducing a robust `StockIDHelper`.
3.  **TD-ECON-WAR-STIMULUS**: Implement the architectural foundation for Progressive Taxation to replace the scalar `income_tax_rate`.

## 2. Architectural Changes

### 2.1. Stock Market Hardening (`modules/market/`)
-   **Problem**: `StockMarket.place_order` and `get_price` currently rely on `item_id.split('_')[1]` to extract `firm_id`. This crashes if the ID format varies or is invalid.
-   **Solution**: Introduce `StockIDHelper`, a stateless utility class to encapsulate ID serialization/deserialization logic.
-   **Standard**: All Stock IDs must follow the format `stock_<firm_id>`.

### 2.2. Progressive Taxation Foundation (`modules/government/`)
-   **Problem**: `Government` and `FiscalPolicyDTO` store `income_tax_rate` as a single `float`. This prevents the implementation of bracket-based or progressive tax policies required for economic balancing.
-   **Solution**:
    -   Introduce `TaxBracketDTO` to define tax bands.
    -   Update `FiscalPolicyDTO` to carry a list of brackets (`tax_brackets`).
    -   Refactor `TaxService.calculate_tax_liability` to process brackets.
    -   **Legacy Compatibility**: `Government.income_tax_rate` will remain as a read-only property returning the "Effective Base Rate" (or the rate of the lowest/highest bracket) to prevent breaking `FiscalEngine` or Reporting until they are fully migrated.

## 3. Detailed Design

### 3.1. Market Domain (`modules/market/`)

#### 3.1.1. `StockIDHelper`
A static utility class to strictly manage Stock ID formats.

```python
class StockIDHelper:
    PREFIX = "stock"
    SEPARATOR = "_"

    @staticmethod
    def is_valid_stock_id(item_id: str) -> bool:
        """Checks if the item_id matches the 'stock_{int}' format."""
        if not item_id or not isinstance(item_id, str):
            return False
        parts = item_id.split(StockIDHelper.SEPARATOR)
        if len(parts) != 2 or parts[0] != StockIDHelper.PREFIX:
            return False
        return parts[1].isdigit()

    @staticmethod
    def parse_firm_id(item_id: str) -> int:
        """
        Parses the firm_id from a stock item_id.
        Raises ValueError if format is invalid.
        """
        if not StockIDHelper.is_valid_stock_id(item_id):
            raise ValueError(f"Invalid Stock ID format: {item_id}. Expected 'stock_<int>'.")
        return int(item_id.split(StockIDHelper.SEPARATOR)[1])

    @staticmethod
    def format_stock_id(firm_id: int | str) -> str:
        """Formats a firm_id into a stock item_id."""
        return f"{StockIDHelper.PREFIX}{StockIDHelper.SEPARATOR}{firm_id}"
```

#### 3.1.2. `StockMarket` Refactor
-   **`place_order`**: Call `StockIDHelper.parse_firm_id(order.item_id)`. Catch `ValueError` and log specific error/reject order.
-   **`get_price`**: Call `StockIDHelper.parse_firm_id(item_id)`. Catch `ValueError` and return 0.0 (or handle gracefully).

### 3.2. Government Domain (`modules/government/`)

#### 3.2.1. DTO Updates
**New DTO**: `TaxBracketDTO`
```python
@dataclass
class TaxBracketDTO:
    threshold: float  # The lower bound income for this bracket (tick-based)
    rate: float       # Tax rate (0.0 to 1.0)
```

**Updated**: `FiscalPolicyDTO`
```python
@dataclass
class FiscalPolicyDTO:
    # Deprecated: Kept for legacy compatibility (Scalar Flat Tax)
    # If tax_brackets is empty, this rate is used as a flat tax.
    income_tax_rate: float
    
    corporate_tax_rate: float
    
    # New: Progressive Tax Schedule
    # If populated, overrides income_tax_rate.
    tax_brackets: List[TaxBracketDTO] = field(default_factory=list)
```

#### 3.2.2. `TaxService` Refactor
-   **`calculate_tax_liability(policy, income)`**:
    1.  Check if `policy.tax_brackets` is populated.
    2.  If yes, sort brackets by threshold descending.
    3.  Iterate and apply rates to the relevant portions of income.
    4.  If no, fallback to `policy.income_tax_rate * income`.

#### 3.2.3. `Government` State Migration
-   **State**: `self.fiscal_policy` acts as the source of truth.
-   **Attribute**: `self.income_tax_rate` (getter) -> returns `self.fiscal_policy.income_tax_rate`.
-   **Setter**: `self.income_tax_rate` (setter) -> updates `self.fiscal_policy.income_tax_rate` AND clears `self.fiscal_policy.tax_brackets` (enforcing flat tax when scalar is set manually). This ensures backward compatibility with `FiscalEngine` outputs.

## 4. Interface Changes (API Drafts)

### `modules/market/api.py` (Additions)
```python
# ... Existing Imports ...

class StockIDHelper:
    """Helper for Stock ID formatting and parsing."""
    PREFIX = "stock"
    SEPARATOR = "_"

    @staticmethod
    def is_valid_stock_id(item_id: str) -> bool:
        ...

    @staticmethod
    def parse_firm_id(item_id: str) -> int:
        ...

    @staticmethod
    def format_stock_id(firm_id: int | str) -> str:
        ...
```

### `modules/government/dtos.py` (Additions/Updates)
```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class TaxBracketDTO:
    threshold: float
    rate: float

@dataclass
class FiscalPolicyDTO:
    income_tax_rate: float
    corporate_tax_rate: float
    tax_brackets: List[TaxBracketDTO] = field(default_factory=list)
```

## 5. Verification Plan

### 5.1. Test Cases
1.  **Stock ID Parsing**:
    -   `test_stock_id_helper_valid`: `stock_101` -> `101`.
    -   `test_stock_id_helper_invalid`: `bond_101`, `stock_abc`, `101` -> Raise `ValueError`.
    -   `test_stock_market_invalid_order`: Submit order with `item_id="bad_id"`. Ensure it is rejected safely (logged, no crash).

2.  **Progressive Tax**:
    -   **Fixture**: 3 Brackets.
        -   0 - 1000: 0%
        -   1000 - 5000: 10%
        -   5000+: 20%
    -   `test_progressive_tax_calculation`:
        -   Income 500: Tax 0.
        -   Income 2000: Tax (1000*0 + 1000*0.1) = 100.
        -   Income 6000: Tax (1000*0 + 4000*0.1 + 1000*0.2) = 400 + 200 = 600.
    -   `test_flat_tax_fallback`: Ensure empty brackets list uses `income_tax_rate`.

### 5.2. Impact Analysis
-   **FiscalEngine**: The engine currently outputs `new_income_tax_rate` (scalar). The `Government` agent's setter will handle this by resetting to a flat tax structure. This prevents breakage but delays the full utilization of progressive tax until `FiscalEngine` is updated (Phase 3).
-   **Reporting**: `Government.get_agent_data` uses `self.income_tax_rate`. This will continue to work for flat tax. for progressive, it will return the base rate (0th bracket) or the deprecated scalar, which is acceptable for now.

## 6. Risk Audit
-   **[TD-MARKET-STRING-PARSE]**: Resolved by `StockIDHelper`.
-   **[TD-ECON-WAR-STIMULUS]**: Infrastructure Resolved. Logic (Policy) Pending `FiscalEngine` update.
-   **Data Migration**: `Government` instantiation must ensure `FiscalPolicyDTO` is initialized correctly. The `__init__` logic in `Government` must be checked to ensure it creates a valid default policy.

## 7. Mandatory Reporting (Scribe Note)
*The following insights must be recorded in `communications/insights/wave2-market-policy-spec.md` upon mission completion:*
-   **Insight**: The `StockIDHelper` exposes how many legacy string-parsing hacks exist in `StockMarket`.
-   **Debt Created**: `FiscalPolicyDTO` now has dual modes (Scalar vs Brackets). This is "Transitional Debt" and must be cleaned up when `FiscalEngine` supports brackets natively.
-   **Verification**: All Market tests must pass with strict ID validation enabled.