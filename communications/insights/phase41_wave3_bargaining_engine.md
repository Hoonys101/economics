# Insight Report: Wave 3.3 Search & Bargaining Market Engine

## 1. Architectural Insights
*   **Nash Bargaining**: The introduction of Nash Bargaining in `LaborMarket` shifts the wage determination from a simple "Buyer Price" (Firm Offer) model to a "Surplus Sharing" model. This required calculating the surplus ($WTP - WTA$) and splitting it based on bargaining power (default 0.5).
*   **Adaptive Learning (TD-Error)**: Implemented a feedback loop where Firms learn from their previous tick's hiring outcomes. This necessitated extending the `HRState` (Runtime) and `HRContextDTO` (Data Contract) to persist history: `target_hires`, `actual_hires`, and `wage_offer`.
*   **State Rotation**: To support this, `Firm.reset()` now rotates "current tick" counters to "previous tick" history fields, ensuring that the decision engine in the *next* tick has access to the *result* of the *previous* tick's actions.
*   **DTO Evolution**: `HRStateDTO` and `HRContextDTO` were evolved to carry these history fields across the stateless engine boundary, adhering to the "Stateless Engine Orchestration" (SEO) pattern.

## 2. Regression Analysis
*   **Mock Drift in Unit Tests**: Several unit tests (`tests/unit/modules/firm/test_engines.py`, `tests/unit/test_wave6_fiscal_masking.py`) failed because they mocked `HRStateDTO`/`HRContextDTO` without the newly added history fields (`target_hires_prev_tick`, etc.). Since `MagicMock` returns a mock for missing attributes, comparisons like `if target_hires > 0` raised `TypeError`.
    *   *Fix*: Explicitly initialized these fields to `0` in the test mocks.
*   **Logic Change in Market Matching**: Tests in `tests/unit/test_labor_market_system.py` failed because they expected the matched wage to be exactly the Firm's Offer Wage. With Nash Bargaining, the wage is now `(Offer + Reservation) / 2`.
    *   *Fix*: Updated test assertions to expect the bargained wage (e.g., `17.5` instead of `20.0`).

## 3. Test Evidence
```
=========================== short test summary info ============================
SKIPPED [1] tests/integration/test_server_integration.py:16: websockets is mocked
SKIPPED [1] tests/security/test_god_mode_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/security/test_server_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/security/test_websocket_auth.py:13: websockets is mocked
SKIPPED [1] tests/system/test_server_auth.py:11: websockets is mocked, skipping server auth tests
SKIPPED [1] tests/test_server_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/test_ws.py:11: fastapi is mocked
SKIPPED [1] tests/market/test_dto_purity.py:26: Pydantic is mocked
SKIPPED [1] tests/market/test_dto_purity.py:54: Pydantic is mocked
SKIPPED [1] tests/modules/system/test_global_registry.py:101: Pydantic is mocked
SKIPPED [1] tests/modules/system/test_global_registry.py:132: Pydantic is mocked
================= 985 passed, 11 skipped, 2 warnings in 7.46s ==================
```
