# Market Index Circuit Breaker Implementation Insight

## 1. Architectural Insights
- **Goal**: Implement `IndexCircuitBreaker` to halt trading when market index drops significantly.
- **Design Pattern**: Dependency Injection. The circuit breaker is injected into Markets (`OrderBookMarket`, `StockMarket`).
- **State Management**: The circuit breaker maintains its own state (`is_active`, `halt_until_tick`).
- **Fail-Open**: If `market_index` is missing, the breaker defaults to "Healthy" (True) to prevent disruption.
- **Mocking**: Strict mocking with `spec=IIndexCircuitBreaker` is enforced for tests.

## 2. Regression Analysis
- **Broken Tests**: Tests instantiating `OrderBookMarket` and `StockMarket` will fail because `__init__` signature changes.
- **Fix**: All test instantiations must include a mock `IIndexCircuitBreaker`.
- **Logic Change**: `match_orders` now has a pre-check. If halted, it returns empty transactions. This is a behavioral change but shouldn't affect happy-path tests if the mock returns `True` for health.

## 3. Implementation Plan
1.  Define `IndexCircuitBreakerConfigDTO` and `IIndexCircuitBreaker` in `modules/market/api.py`.
2.  Implement `IndexCircuitBreaker` logic in `simulation/markets/market_circuit_breaker.py`.
3.  Update `OrderBookMarket` and `StockMarket` to use the breaker.
4.  Update configuration `config/economy_params.yaml`.
5.  Create new tests for the breaker.
6.  Update existing tests to pass the new dependency.

## 4. Test Evidence
(To be filled after implementation)
