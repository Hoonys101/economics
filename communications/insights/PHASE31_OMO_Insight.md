# Insight Report: OMO Infrastructure Gap and Resolution

## Phenomenon
The specification `SPEC_PHASE31_OMO.md` explicitly assumed the existence of an established `SecurityMarket` and `government_bond` infrastructure from `WO-075` (National Debt Auction).
> "**기존 인프라 활용**: 신규 시장을 만들지 않고, `WO-075`에서 구축된 기존 국채 및 `SecurityMarket` 인프라를 그대로 사용합니다."

However, upon inspecting `simulation/initialization/initializer.py`, no market with ID `security_market` or `bond_market` was found. The existing bond issuance logic in `modules/finance/system.py` uses direct allocation (or "financial" market ID in transactions) rather than an order book market.

## Cause
`WO-075` implementation likely focused on the *primary* market (Issuance) which was implemented via `FinanceSystem.issue_treasury_bonds` directly generating transactions, bypassing a continuous secondary market structure. The OMO specification (Phase 31) requires a *secondary* market mechanism (`SecurityMarket`) for the Central Bank to intervene via standard `Order` objects.

## Solution
To satisfy the Phase 31 requirement without major refactoring of the primary issuance logic:
1.  **Initialized `security_market`**: Added `sim.markets["security_market"] = OrderBookMarket(...)` in `simulation/initialization/initializer.py`.
2.  **Integrated OMO Logic**: Implemented `CentralBankSystem` to place orders into this specific market.
3.  **Settlement Handling**: Updated `TransactionManager` to handle `omo_purchase` (Mint) and `omo_sale` (Burn) transactions resulting from these market matches.

## Lessons Learned
- **Implicit Assumptions**: Specifications often assume "infrastructure" means "generic capability," but in code, it requires specific instances (e.g., an initialized `Market` object).
- **Primary vs. Secondary Markets**: Economic simulations must distinguish between primary issuance (often administrative/direct) and secondary trading (market-based). OMO operates in the secondary market.
