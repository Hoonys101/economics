# Market Index Circuit Breaker Implementation Insight

## 1. Architectural Insights
- **Goal**: Implement `IndexCircuitBreaker` to halt trading when market index drops significantly.
- **Design Pattern**: Dependency Injection. The circuit breaker is injected into Markets (`OrderBookMarket`, `StockMarket`) and `TickOrchestrator`.
- **State Management**: The circuit breaker maintains its own state (`is_active`, `halt_until_tick`).
- **Fail-Open**: If `market_index` is missing, the breaker defaults to "Healthy" (True) to prevent disruption.
- **Centralized Orchestration**: `TickOrchestrator` is responsible for calculating the unified macro index (Stock Market Cap) and updating the circuit breaker state *once per tick*. Markets only *read* the state via `is_active()`.
- **Mocking**: Strict mocking with `spec=IIndexCircuitBreaker` is enforced for tests.

## 2. Regression Analysis
- **Broken Tests**: Tests instantiating `OrderBookMarket` and `StockMarket` failed because `__init__` signature changed.
- **Fix**: All test instantiations were updated to include a mock `IIndexCircuitBreaker`.
- **Logic Change**: `match_orders` now has a pre-check `is_active()`. If halted, it returns empty transactions.
- **Initialization Bug Fix**: Previous iteration calculated index inside `OrderBookMarket` which caused 100% drop on tick 0. Moved calculation to Orchestrator using Stock Market data corrects this.

## 3. Implementation Plan
1.  Define `IndexCircuitBreakerConfigDTO` and `IIndexCircuitBreaker` in `modules/market/api.py`.
2.  Implement `IndexCircuitBreaker` logic in `simulation/markets/market_circuit_breaker.py`.
3.  Update `TickOrchestrator` to calculate index and update breaker.
4.  Update `OrderBookMarket` and `StockMarket` to read breaker state.
5.  Update configuration `config/economy_params.yaml`.
6.  Create new tests for the breaker and halt logic.
7.  Update existing tests to pass the new dependency.

## 4. Test Evidence
- `tests/unit/markets/test_index_circuit_breaker.py`: Passed (8 tests).
- `tests/unit/markets/test_market_halt.py`: Passed (3 tests).
- `tests/unit/markets/test_order_book_market.py`: Passed.
- `tests/integration/scenarios/diagnosis/test_market_mechanics.py`: Passed.
