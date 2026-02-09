# PH9.2 Market DTO Unification Insights

## 1. Problem Phenomenon
The system currently has two conflicting Order definitions:
- `OrderDTO` (in `modules/market/api.py`): The intended modern, immutable DTO.
- `StockOrder` (in `simulation/models.py`): A legacy mutable dataclass used for stock markets.

Audit reports indicated that `StockMarket` was using `StockOrder` and failing parity checks. However, code inspection reveals `StockMarket` currently enforces `OrderDTO` via `isinstance` checks, suggesting a partial refactor occurred but left `StockOrder` as dead/legacy code or potentially causing silent failures if passed.

## 2. Root Cause Analysis
- **Incomplete Refactoring**: Previous efforts to modernize `StockMarket` updated the method signature to `OrderDTO` but didn't fully eradicate `StockOrder` from `simulation/models.py` or legacy logic.
- **DTO Fragmentation**: `StockOrder` has different field names (`order_type` vs `side`, `price` vs `price_limit`, `firm_id` vs `item_id`), making them incompatible without adaptation.

## 3. Solution Implementation Details
- **CanonicalOrderDTO**: Renamed `OrderDTO` to `CanonicalOrderDTO` in `modules/market/api.py` to strictly follow the spec. Aliased `OrderDTO` for backward compatibility.
- **Adapter Pattern**: Implemented `convert_legacy_order_to_canonical` to handle `StockOrder` (via structural typing to avoid circular imports) and dictionary inputs. It handles field mapping (`order_type` -> `side`, `firm_id` -> `item_id`).
- **Market Purity**: Updated `StockMarket` and `OrderBookMarket` to explicitly type hint `CanonicalOrderDTO`.
- **Legacy Cleanup**: Removed unused imports of `StockOrder` in decision modules to prevent future usage.

## 4. Lessons Learned
- **Dead Code Persistence**: Legacy classes like `StockOrder` can persist in the codebase long after they are supposedly replaced, causing confusion in audits.
- **Naming Consistency**: Field name mismatches (`order_type` vs `side`) are a major source of friction in DTO unification.
