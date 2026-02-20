# Insight Report: Fix M&A and StockMarket Pennies Migration

## [Architectural Insights]

### M&A Manager (`simulation/systems/ma_manager.py`)
- **Issue**: The `MAManager` was performing financial calculations using floating-point arithmetic (dollars) and passing these values directly to the `SettlementSystem`.
- **Constraint**: `SettlementSystem.transfer` and `record_liquidation` strictly enforce integer arguments (pennies) for Zero-Sum Integrity.
- **Resolution**: Refactored `_execute_merger` to accept `price: int`. Updated `process_market_exits_and_entries` and `_attempt_hostile_takeover` to calculate `offer_price` in pennies (casting from float where necessary) before invoking settlement.
- **Bankruptcy**: Updated `_execute_bankruptcy` to calculate `inventory_value` and `capital_value` in pennies. Fixed a crash where `recovered_cash` (a Dict) was being logged as a float.

### StockMarket (`simulation/markets/stock_market.py`)
- **Status**: Mostly compliant. It uses `CanonicalOrderDTO` which carries `price_pennies`.
- **Matching**: `StockMatchingEngine` performs integer math for trade execution, ensuring `Transaction.total_pennies` is an integer.
- **Observation**: `StockMarket` maintains `last_prices` as floats for display and limit checking. This is acceptable as long as the underlying settlement is integer-based.

## [Test Evidence]

### Unit Tests: `tests/unit/test_ma_pennies.py`
Verifies that `MAManager` correctly handles integer conversion for Friendly Mergers, Hostile Takeovers, and Bankruptcy liquidation.

```
tests/unit/test_ma_pennies.py::TestMAManagerPennies::test_friendly_merger_price_is_int
-------------------------------- live log call ---------------------------------
INFO     MAManager:ma_manager.py:183 FRIENDLY_MERGER_EXECUTE | Predator 101 acquires Prey 202. Price: 550000 pennies.
INFO     MAManager:ma_manager.py:229 FRIENDLY_MERGER_RESULT | Retained 0, Fired 0.
PASSED                                                                   [ 33%]
tests/unit/test_ma_pennies.py::TestMAManagerPennies::test_hostile_takeover_price_is_int
-------------------------------- live log call ---------------------------------
INFO     MAManager:ma_manager.py:173 HOSTILE_TAKEOVER_SUCCESS | Predator 101 seizes Target 303. Offer: 6,000.00
INFO     MAManager:ma_manager.py:183 HOSTILE_MERGER_EXECUTE | Predator 101 acquires Prey 303. Price: 600000 pennies.
INFO     MAManager:ma_manager.py:229 HOSTILE_MERGER_RESULT | Retained 0, Fired 0.
PASSED                                                                   [ 66%]
tests/unit/test_ma_pennies.py::TestMAManagerPennies::test_bankruptcy_liquidation_values_are_int
-------------------------------- live log call ---------------------------------
INFO     MAManager:ma_manager.py:258 BANKRUPTCY | Firm 303 liquidated. Cash Remaining: 12345 pennies.
PASSED                                                                   [100%]
```

### Market Tests: `tests/market/test_stock_market_pennies.py`
Verifies that `StockMatchingEngine` produces transactions with correct integer `total_pennies`.

```
tests/market/test_stock_market_pennies.py::TestStockMarketPennies::test_stock_matching_fractional_shares PASSED [ 50%]
tests/market/test_stock_market_pennies.py::TestStockMarketPennies::test_stock_matching_integer_math PASSED [100%]
```
