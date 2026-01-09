# Work Order: WO-029-D (Phase 17-3B: Real Estate - Sales & Mortgage)

**Objective**: Implement Real Estate Sales Market and Mortgage System.

**Reference Spec**: `design/specs/phase17_3_real_estate_spec.md`

## Required Changes

### 1. Market Structure (`simulation/markets.py` & `engine.py`)
- **HousingMarket**: Reuse or extend `OrderBookMarket`.
    - Transaction item: `real_estate_id` (Unique Item).
    - Unlike fungible goods (Apple), each order is for specific `RealEstateUnit`.
- **Engine**: In `_process_market_matching`, handle `housing_market`.

### 2. Mortgage System (`simulation/bank.py` or new `mortgage.py`)
- **Mortgage Loan**:
    - Principal: `Price * 0.8` (LTV 80%)
    - Term: 360 ticks (30 years equivalent)
    - Monthly Payment: Amortization logic.
    - Collateral: Link to `RealEstateUnit.id`.
- **Foreclosure Logic**:
    - If borrower defaults (misses 3 payments?), Bank seizes property.
    - `unit.owner_id = Bank`, `unit.occupant_id = None` (Eviction).
    - Bank places SELL order at 80% of value (Fire Sale).

### 3. HousingManager AI (`simulation/decisions/housing_manager.py`)
**This is the "Proxy Planner" module.**
- Implement `should_buy(household, unit_price, rent_price)`:
    - Calculate NPV of Renting vs Buying.
    - Hardcoded economic wisdom (not RL).
- **Integration**:
    - In `AIDrivenHouseholdDecisionEngine`, call `HousingManager`.
    - If `HousingManager` says BUY, override other consumption signals if affordable.

### 4. Engine Integration (`simulation/engine.py`)
- **Initialization**:
    - Ensure remaining 80 units (Government/Bank owned) are listed for SALE.
- **Run Tick**:
    - Process Mortgage Payments (before Rent).
    - Match Sales Orders.
    - Execute Foreclosures.

---

## Verification
Create `tests/verify_real_estate_sales.py`:
1. **Mortgage Creation**: Buying a house creates a loan with correct LTV.
2. **Ownership Transfer**: Seller -> Buyer update.
3. **Foreclosure**: Default -> Bank ownership -> Eviction.
4. **AI Rationality**: Manager chooses BUY when Price < Rent * Multiplier (NPV logic).
