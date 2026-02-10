# Integrated Mission Guide: Phase 10 Market Decoupling & Protocol Hardening

## 1. Objectives
- **Decouple Matching Logic**: Extract matching logic from `OrderBookMarket` and `StockMarket` into standalone engines.
- **Standardize Financial Protocols (TD-270)**: Unify `Dict[str, float]` for asset representation across `IFinancialAgent` and `IMortgageBorrower`.
- **Implement Real Estate ROI for Firms (TD-271)**: Allow firms to utilize owned property for production or rental income.
- **Ensure Zero-Leak Integrity**: Verify all changes against `trace_leak.py`.

## 2. Reference Context
- `simulation/markets/order_book_market.py`: Contains `_match_orders_for_item`.
- `simulation/markets/stock_market.py`: Contains `_match_orders_for_firm`.
- `simulation/interfaces/market_interface.py`: Base for market protocols.
- `simulation/firms.py`: Needs real estate utilization logic.
- `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`: Background on TD-270/271.

## 3. Implementation Roadmap

### Phase 1: Matching Engine Extraction
- Create `simulation/markets/matching_engine.py`.
- Define `IMatchingEngine` Protocol.
- Implement `OrderBookMatchingEngine`: Port logic from `OrderBookMarket._match_orders_for_item`.
- Implement `StockMatchingEngine`: Port logic from `StockMarket._match_orders_for_firm`.
- Integration: Update `OrderBookMarket` and `StockMarket` to use the new engines.

### Phase 2: Financial Protocol Hardening (TD-270)
- Update `IFinancialAgent` and `IMortgageBorrower` to use `Dict[str, float]` for `assets`.
- Implement `total_wealth` property/method on both to return the sum of assets in `DEFAULT_CURRENCY`.
- Fix any broken call sites in `HousingTransactionHandler` and `SettlementSystem`.

### Phase 3: Firm Real Estate Utilization (TD-271)
- Add `RealEstateUtilizationComponent` to `Firm`.
- Logic: If property is held, it provides a "Production Space Bonus" (reducing manufacturing cost) or is marked for "Rental" (not yet fully implemented but tracked).
- Update `Firm.produce()` to reflect the space bonus.

## 4. Verification
- Run `pytest tests/simulation/test_markets.py`
- Run `python trace_leak.py`
- Run `python tests/simulation/test_firms.py`
- Verify that firms with property have lower production costs than those without.
