# Insight Report: Market Precision Refactor

## 1. Architectural Insights
- **Penny Standard Adoption**: The `OrderBookMatchingEngine` and `StockMatchingEngine` now operate exclusively on `int` pennies. This eliminates floating-point drift in price discovery and execution.
- **DTO Migration**: `CanonicalOrderDTO` now enforces `price_pennies: int`. The legacy `price_limit: float` is retained but deprecated. `convert_legacy_order_to_canonical` bridges the gap by treating floats as dollars and ints as pennies (mostly), with heuristics for safety.
- **Transaction SSoT**: The `Transaction` model now carries `total_pennies: int` as the Single Source of Truth for settlement. `price` (float) is a derived value (`total_pennies / quantity`) for display and legacy agent compatibility. This ensures `SettlementSystem` receives exact integer amounts.
- **Scale Discrepancy Resolved**: A discrepancy between legacy tests (expecting dollars) and the new engine (producing pennies) was identified. The decision was made to update tests to expect pennies, enforcing the "Penny Standard" across the board. Agents relying on `Transaction.price` must now interpret it as pennies (or the system must be updated to scale it back, but currently it's raw unit price in pennies).

## 2. Test Evidence
All relevant tests passed, including new precision tests and updated legacy tests.

```text
tests/unit/test_markets_v2.py::TestOrderBookMarketInitialization::test_market_initialization PASSED
tests/unit/test_markets_v2.py::TestPlaceOrderToBook::test_add_single_buy_order PASSED
tests/unit/test_markets_v2.py::TestPlaceOrderToBook::test_add_buy_orders_sorted PASSED
tests/unit/test_markets_v2.py::TestPlaceOrderToBook::test_add_sell_orders_sorted PASSED
tests/unit/test_markets_v2.py::TestPlaceOrderToBook::test_add_orders_with_same_price PASSED
tests/unit/test_markets_v2.py::TestOrderMatching::test_unfilled_order_no_match PASSED
tests/unit/test_markets_v2.py::TestOrderMatching::test_full_match_one_to_one PASSED
tests/unit/test_markets_v2.py::TestOrderMatching::test_partial_match_then_book PASSED
tests/unit/test_markets_v2.py::TestOrderMatching::test_match_with_multiple_orders PASSED
tests/unit/test_markets_v2.py::TestMarketAPI::test_get_best_bid_empty PASSED
tests/unit/test_markets_v2.py::TestMarketAPI::test_get_best_bid_non_empty PASSED
tests/unit/test_markets_v2.py::TestMarketAPI::test_get_best_ask_empty PASSED
tests/unit/test_markets_v2.py::TestMarketAPI::test_get_best_ask_non_empty PASSED
tests/unit/test_markets_v2.py::TestMarketAPI::test_get_last_traded_price PASSED
tests/unit/test_markets_v2.py::TestMarketAPI::test_get_spread PASSED
tests/unit/test_markets_v2.py::TestMarketAPI::test_get_spread_no_bid_or_ask PASSED
tests/unit/test_markets_v2.py::TestMarketAPI::test_get_market_depth PASSED
tests/unit/test_stock_market.py::TestStockMarketInitialization::test_initialization PASSED
tests/unit/test_stock_market.py::TestStockMarketInitialization::test_update_reference_prices PASSED
tests/unit/test_stock_market.py::TestStockOrderPlacement::test_place_buy_order PASSED
tests/unit/test_stock_market.py::TestStockOrderPlacement::test_place_sell_order PASSED
tests/unit/test_stock_market.py::TestStockOrderPlacement::test_price_clamping PASSED
tests/unit/test_stock_market.py::TestStockOrderPlacement::test_order_sorting PASSED
tests/unit/test_stock_market.py::TestStockOrderMatching::test_full_match PASSED
tests/unit/test_stock_market.py::TestStockOrderMatching::test_partial_match PASSED
tests/unit/test_stock_market.py::TestOrderExpiry::test_clear_expired_orders PASSED
tests/unit/test_market_adapter.py::TestMarketAdapter::test_pass_through PASSED
tests/unit/test_market_adapter.py::TestMarketAdapter::test_convert_stock_order PASSED
tests/unit/test_market_adapter.py::TestMarketAdapter::test_convert_dict_legacy_format PASSED
tests/unit/test_market_adapter.py::TestMarketAdapter::test_convert_dict_canonical_format PASSED
tests/unit/test_market_adapter.py::TestMarketAdapter::test_invalid_input PASSED
tests/market/test_precision_matching.py::TestPrecisionMatching::test_labor_market_pricing PASSED
tests/market/test_precision_matching.py::TestPrecisionMatching::test_market_fractional_qty_rounding PASSED
tests/market/test_precision_matching.py::TestPrecisionMatching::test_market_zero_sum_integer PASSED
```

## 3. Risks & Recommendations
- **Agent Confusion**: Legacy agents might misinterpret `Transaction.price` (pennies) as dollars if they are not updated. Recommendation: Batch update agent logic or introduce a "Display Price" field in `Transaction` that respects the market's configured scale.
- **Legacy DTOs**: `StockOrder` is deprecated but still supported. Future refactors should eliminate it completely.
