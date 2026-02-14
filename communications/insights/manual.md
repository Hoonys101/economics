# Architectural Insight: Firm Decomposition

## Architectural Insights

### Pricing Engine Decomposition
- **Refactoring Strategy**: Moved the logic from `_calculate_invisible_hand_price` to `PricingEngine`.
- **Architectural Decision**: Implemented `PricingEngine` as a stateless component implementing `IPricingEngine`.
- **DTOs**: Created `PricingInputDTO` and `PricingResultDTO` to encapsulate data transfer between `Firm` and `PricingEngine`.
- **Change in Behavior**: The original `_calculate_invisible_hand_price` only logged shadow metrics. The refactored version calculates the new price and the `Firm` agent now updates `sales_state.last_prices` as per the specification. This aligns the implementation with the intended "Invisible Hand" mechanism.

### Asset Management Engine Update
- **Refactoring Strategy**: Moved liquidation logic from `Firm.liquidate_assets` to `AssetManagementEngine.calculate_liquidation`.
- **Architectural Decision**: `AssetManagementEngine` now calculates the liquidation outcome (assets to return, items to write off) without directly modifying the agent state. The `Firm` agent applies the result.
- **DTOs**: Created `LiquidationExecutionDTO` and `LiquidationResultDTO`.

### Protocol Purity
- **Strict Compliance**: All engine interactions use DTOs and Protocols. No direct state modification by engines.

## Test Evidence

```
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_no_liabilities PASSED [  9%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_with_liabilities PASSED [ 18%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_with_treasury_shares PASSED [ 27%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_negative_net_assets PASSED [ 36%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_zero_shares PASSED [ 45%]
tests/unit/test_firms.py::TestFirmProduction::test_produce PASSED        [ 54%]
tests/unit/test_firms.py::TestFirmSales::test_post_ask PASSED            [ 63%]
tests/unit/test_firms.py::TestFirmSales::test_adjust_marketing_budget_increase PASSED [ 72%]
tests/simulation/test_firm_refactor.py::test_firm_initialization_states PASSED [ 81%]
tests/simulation/test_firm_refactor.py::test_command_bus_internal_orders_delegation PASSED [ 90%]
tests/simulation/test_firm_refactor.py::test_produce_orchestration PASSED [100%]

============================== 11 passed in 0.22s ==============================
```
