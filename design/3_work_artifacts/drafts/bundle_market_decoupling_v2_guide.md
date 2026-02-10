# Integrated Mission Guide: Phase 10 Market Decoupling & Protocol Hardening (High-Fidelity)

## 1. Objectives (Based on Spec Draft 082543)
- **Track 1: Matching Engine Decoupling**: Extract stateless matching logic from `Market` classes.
- **Track 2: Protocol Hardening (TD-270)**: Standardize on multi-currency balances while maintaining compatibility.
- **Track 3: Firm Real Estate Utilization (TD-271)**: Convert firm-owned property into a production space bonus.
- **Goal**: Maintain 0.0000% monetary leak and architectural purity.

## 2. Reference Context (MUST READ)
- **Core Spec**: `design/3_work_artifacts/drafts/draft_082543___Phase_10_Architecture_De.md`
- **Architecture**: `design/1_governance/architecture/ARCH_SEQUENCING.md` (Execute-Sync loop)
- **Files to Modify**:
    - `modules/market/api.py` (New DTOs & Protocols)
    - `modules/finance/api.py` (IFinancialAgent hardening)
    - `simulation/markets/matching_engine.py` (**NEW FILE**)
    - `simulation/markets/order_book_market.py` (Refactor to use engine)
    - `simulation/markets/stock_market.py` (Refactor to use engine)
    - `simulation/firms.py` (Add RealEstateUtilizationComponent)

## 3. Implementation Roadmap

### Phase 1: API & DTO Definition
- Update `modules/market/api.py` with `OrderBookStateDTO`, `StockMarketStateDTO`, and `MatchingResultDTO`.
- Implement initial `IMatchingEngine` protocols.

### Phase 2: Stateless Matching Engines
- Create `simulation/markets/matching_engine.py`.
- Implement `OrderBookMatchingEngine` and `StockMatchingEngine`.
- **Logic**: Port the existing nested loops/logic from the markets but ensure they only operate on the passed DTOs.

### Phase 3: Market Refactoring
- Modify `OrderBookMarket` and `StockMarket` constructors to accept their respective engines.
- Refactor `match_orders` to:
    1. Create `StateDTO` snapshot.
    2. Call `engine.match()`.
    3. Apply results to internal state.

### Phase 4: Protocol Hardening (TD-270)
- Add `get_all_balances()` and `total_wealth` property to `IFinancialAgent` in `modules/finance/api.py`.
- Implement these in `Household` and `Firm` agents. Ensure `total_wealth` is a sum of balances for now.

### Phase 5: Firm Real Estate ROI (TD-271)
- Implement `RealEstateUtilizationComponent` in `simulation/firms.py`.
- Apply the production cost reduction formula: `owned_space * space_utility_factor * regional_rent_index`.
- Ensure it emits an `Effect` for the `SimulationState.effects_queue`.

## 4. Verification
- `pytest tests/simulation/test_markets.py`
- `python trace_leak.py` (Non-negotiable)
- `python scripts/audit_zero_sum.py`
