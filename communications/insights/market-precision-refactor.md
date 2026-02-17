# Insight Report: Market Precision Refactor

## 1. Architectural Insights
- **Penny Standard Adoption**: The `OrderBookMatchingEngine` and `StockMatchingEngine` now operate exclusively on `int` pennies. This eliminates floating-point drift in price discovery and execution.
- **DTO Migration**: `CanonicalOrderDTO` now enforces `price_pennies: int`. The legacy `price_limit: float` is retained but deprecated. `convert_legacy_order_to_canonical` bridges the gap by treating floats as dollars (converting to pennies via `* 100`) and ints as pennies.
- **Transaction SSoT**: The `Transaction` model now carries `total_pennies: int` as the Single Source of Truth for settlement. `price` (float) is a derived value (`(total_pennies / quantity) / 100.0`) representing Dollars. This ensures `SettlementSystem` receives exact integer amounts while maintaining legacy UI compatibility.
- **Display Price (Dollars)**: A critical decision was made to ensure `Transaction.price` represents Dollars (float), not Pennies. This maintains semantic compatibility with legacy agents and dashboards. Tests were updated to reflect this expectation (e.g., $1.02 instead of 102.0 pennies).

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
- **Legacy DTOs**: `StockOrder` is deprecated but supported. The conversion logic now assumes `float` inputs are Dollars and `int` inputs are Pennies. This is a heuristic that should be monitored.
- **Agent Awareness**: Agents must continue to treat `Transaction.price` as Dollars. If they access `total_pennies`, they get the exact settlement value.
