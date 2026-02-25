# 🐙 Gemini-CLI Subordinate Worker: Code Review Report

## 🔍 Summary
The PR introduces a macro-level `IndexCircuitBreaker` intended to halt trading across markets when a unified index drops significantly. It integrates this breaker into both `OrderBookMarket` and `StockMarket` matching engines via Dependency Injection.

## 🚨 Critical Issues
1.  **Macro vs. Micro Index Conflict (Data Contamination)**: The `IndexCircuitBreaker` is designed as a "Market-wide" component, but `check_market_health()` is called inside each individual market's `match_orders()` using disjointed, unscaled local data. `StockMarket` passes the sum of all stock prices as `market_index`, while `OrderBookMarket` passes the simple average of goods prices. If the markets share the same breaker instance, the differing scales (e.g., `5000` vs `10.5`) will cross-contaminate `_reference_index` comparisons, immediately triggering false Level 3 halts.
2.  **100% Drop Bug on Initialization**: In `OrderBookMarket`, if `self.last_traded_prices` is empty (e.g., at simulation start), it sets `current_index = 0.0`. Passing `0.0` bypasses the `None` fail-open check in `check_market_health`, resulting in a `drop_pct` of `1.0` (100% drop) compared to the reference index, indefinitely halting the market on Tick 1.
3.  **State Mutation in Read Path**: Calling `check_market_health()` (which mutates `_is_halted` and `_current_level`) multiple times per tick across different markets violates the **Late-Reset Principle** and causes unpredictable state transitions depending on market execution order.

## ⚠️ Logic & Spec Gaps
*   **Inappropriate Index for Goods Market**: Using a simple equal-weighted average of `last_traded_prices` in the `OrderBookMarket` is highly volatile and structurally inappropriate to act as a trigger for a macroeconomic index circuit breaker.
*   **Incomplete Test Evidence**: The insight document `MARKET_INDEX_BREAKER_IMPL.md` contains an empty placeholder `(To be filled after implementation)`. Insight reports in PRs must contain finalized evidence.

## 💡 Suggestions
*   **Decouple Evaluation from Markets (SRP)**: Markets should *only* consume the breaker state. Change the pre-check in `match_orders` to simply:
    ```python
    if self.index_circuit_breaker and self.index_circuit_breaker.is_active():
        return []
    ```
*   **Centralize Orchestration**: A central authority (e.g., `MarketOrchestrator` or `Government`) should be responsible for calculating a true, unified Macro Index (like total market cap) exactly once per tick, and calling `check_market_health()` to update the breaker state.
*   **Fix Fallback Values**: If local index calculation remains, pass `None` instead of `0.0` when data is insufficient to ensure the fail-open fallback works correctly.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    "Goal: Implement `IndexCircuitBreaker` to halt trading when market index drops significantly... Logic Change: `match_orders` now has a pre-check. If halted, it returns empty transactions."
*   **Reviewer Evaluation**:
    The insight correctly identifies the Dependency Injection pattern but fundamentally misses the architectural flaw of coupling macro-level index evaluation into the localized execution loops of individual micro-markets. The author failed to recognize that calculating `market_index` differently per market and feeding it into a shared stateful breaker would cause catastrophic data contamination.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### 2026-02-25: Circuit Breaker Evaluation Coupling
    - **Symptom**: `IndexCircuitBreaker` triggered false Level 3 halts immediately upon simulation start or when executing multiple markets.
    - **Root Cause**: Macro-level market health evaluation (`check_market_health`) was coupled into the `match_orders` lifecycle of individual micro-markets, causing multiple state mutations per tick using conflicting `market_index` scales (goods average vs. stock sum), and passing `0.0` on empty data.
    - **Resolution**: Circuit breaker state evaluation must be separated from consumption. Markets should only call `is_active()` to read the state. A central orchestrator must calculate the unified macro index and call `check_market_health()` exactly once per tick.
    ```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**