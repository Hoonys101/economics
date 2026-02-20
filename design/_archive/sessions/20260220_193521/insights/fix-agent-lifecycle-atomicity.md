# Fix Agent Lifecycle Atomicity & Queue Scrubbing

## Architectural Insights
1.  **Protocol Purity Enforcement**: The `DeathSystem` now strictly checks for `isinstance(market, IMarket)` before attempting to cancel orders. This required updating `IMarket` in `modules/market/api.py` (adding `@runtime_checkable`) and `simulation/interfaces/market_interface.py` (adding `cancel_orders`).
2.  **StockMarket Compliance**: The `StockMarket` class was found to be technically non-compliant with the `Market` base class contract (missing `matched_transactions` initialization). This was fixed to ensure it passes `isinstance` checks against `IMarket` and behaves consistently with other markets.
3.  **Atomicity Strategy**: Order cancellation is now the *first* step in the liquidation process (`_handle_agent_liquidation`), ensuring that assets are not locked in phantom orders while the agent is being liquidated. This prevents race conditions where a dead agent might "trade" in the matching phase.
4.  **Market Interface Evolution**: `IMarket` has evolved from a purely read-only snapshot interface to include `cancel_orders`, acknowledging that system-level components need privileged access to manage market state for lifecycle events.

## Test Evidence
All relevant tests passed, including new unit tests for cancellation logic and the regression test for `DeathSystem`.

```
tests/unit/markets/test_order_book_market_cancellation.py::TestOrderBookMarketCancellation::test_cancel_orders_removes_agent_orders PASSED [ 16%]
tests/unit/markets/test_order_book_market_cancellation.py::TestOrderBookMarketCancellation::test_cancel_orders_no_effect_if_no_orders PASSED [ 33%]
tests/unit/markets/test_stock_market_cancellation.py::TestStockMarketCancellation::test_cancel_orders_removes_agent_orders PASSED [ 50%]
tests/unit/markets/test_stock_market_cancellation.py::TestStockMarketCancellation::test_cancel_orders_mixed_int_str_id PASSED [ 66%]
tests/unit/systems/lifecycle/test_death_system.py::TestDeathSystem::test_firm_liquidation PASSED [ 83%]
tests/unit/systems/lifecycle/test_death_system.py::TestDeathSystem::test_firm_liquidation_cancels_orders PASSED [100%]
```
