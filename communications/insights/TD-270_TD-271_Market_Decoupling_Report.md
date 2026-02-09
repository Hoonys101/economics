# Technical Insight Report: Market Decoupling & Protocol Hardening (TD-270/271)

## 1. Problem Phenomenon
The legacy `OrderBookMarket` and `StockMarket` classes tightly coupled state management with matching logic. This made the matching logic difficult to test in isolation, reuse, or swap. Additionally, `IFinancialAgent` lacked a standardized way to access multi-currency balances and total wealth, leading to inconsistent implementations across `Household` and `Firm`. Finally, firm-owned real estate provided no direct operational benefit, creating a disconnect between asset ownership and productivity.

## 2. Root Cause Analysis
- **Coupled Logic:** Matching algorithms (Price-Time Priority, Targeted Matching) were embedded directly within the Market classes (`_match_orders_for_item`, `_match_orders_for_firm`), operating on internal mutable state.
- **Protocol Gaps:** `IFinancialAgent` was designed primarily for transactional methods (`deposit`, `withdraw`) but lacked a uniform read interface for comprehensive financial state (`get_all_balances`).
- **Missing Feature:** No mechanism existed to translate `owned_properties` into a production cost advantage for firms.

## 3. Solution Implementation Details

### Track 1: Stateless Matching Engines
- **New Architecture:** Extracted matching logic into `simulation/markets/matching_engine.py`.
- **DTOs:** Defined `OrderBookStateDTO`, `StockMarketStateDTO`, and `MatchingResultDTO` in `modules/market/api.py`.
- **Stateless Engines:**
    - `OrderBookMatchingEngine`: Implements generic order book matching (Goods/Labor) with Targeted (Brand) and General matching phases.
    - `StockMatchingEngine`: Implements stock matching logic.
- **Market Refactoring:** Updated `OrderBookMarket` and `StockMarket` to delegate matching to these engines. The Markets now construct a State DTO, invoke the engine, and apply the returned `MatchingResultDTO` (transactions and unfilled orders) back to their internal state.

### Track 2: Protocol Hardening (TD-270)
- **Interface Update:** Enhanced `IFinancialAgent` in `modules/finance/api.py` with:
    - `get_all_balances() -> Dict[CurrencyCode, float]`
    - `@property total_wealth -> float`
- **Implementation:** Updated `Household` and `Firm` agents to implement these methods, ensuring consistent access to financial state across the simulation.

### Track 3: Firm Real Estate Utilization (TD-271)
- **Component:** Created `RealEstateUtilizationComponent` in `simulation/firms.py`.
- **Logic:** Calculates a virtual revenue/cost reduction based on `owned_space * space_utility_factor * regional_rent_index`.
- **Integration:**
    - Updated `Firm.produce` to accept an `effects_queue`.
    - Invokes `RealEstateUtilizationComponent.apply` during production.
    - Records the bonus as internal revenue (`firm.record_revenue`) to reflect increased efficiency/reduced cost in profit calculations.
    - Emits a `PRODUCTION_COST_REDUCTION` effect to the `effects_queue` for system visibility.
    - Updated `Phase_Production` to inject the `effects_queue`.

## 4. Lessons Learned & Technical Debt
- **DTO Strictness:** `CanonicalOrderDTO` is strict about arguments. Legacy tests often used `Order(...)` aliases with old argument names (`order_type` vs `side`, `price` vs `price_limit`). Migration requires careful updates to tests.
- **Statelessness vs. Metadata:** Stateless engines sometimes need metadata (like `created_tick` for order expiry) that isn't intrinsic to the matching logic but needs to be preserved. Passing this through `metadata` fields in DTOs is a viable pattern but requires careful handling during DTO-to-Domain object conversion.
- **Audit Noise:** `audit_zero_sum.py` tracks "Real Wealth" which can be sensitive to valuation changes. Virtual revenues (like the Real Estate Bonus) affect Profit (and thus Valuation) but not Cash, potentially causing divergences in simplified wealth audit models if they assume Revenue == Cash. `trace_leak.py` (M2 tracking) remains the gold standard for monetary integrity.
