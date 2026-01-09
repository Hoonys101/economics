# Work Order: WO-029-D (Phase 17-3B: Real Estate - Sales & Mortgage) [Updated]

**Objective**: Implement Real Estate Sales Market and Mortgage System.

**Reference Spec**: `design/specs/phase17_3_real_estate_spec.md`

## Required Changes

### 1. Data Model Update (`simulation/models.py`)
- **RealEstateUnit**: Add `quality_tier: int` (1=Low, 2=Mid, 3=High).
    - Initialization: Assign Random Tier (Weighted: 50% T1, 30% T2, 20% T3).
    - Value scaling: T1=10k, T2=30k, T3=100k.

### 2. Market Structure (`simulation/markets.py` & `engine.py`)
- **HousingMarket**: Reuse `OrderBookMarket`.
    - Transaction item: `real_estate_id` (Unique Item).
- **Engine**: In `_process_market_matching`, handle `housing_market`.

### 3. Mortgage System (`simulation/bank.py`)
- **Mortgage Loan**:
    - Principal: `Price * 0.8` (LTV 80%)
    - Term: 360 ticks.
    - Collateral: `RealEstateUnit.id`.
- **Foreclosure Logic**:
    - If 3 missed payments -> Seize -> Evict.
    - Bank places SELL order at 80% of value (Fire Sale).

### 4. HousingManager AI (`simulation/decisions/housing_manager.py`)
- **Proxy Planner**:
    - `should_buy(household, unit_price, rent_price)`: NPV Logic.
    - **New**: `quality_tier` preference (Rich households prefer T3).

### 5. Engine Integration (`simulation/engine.py`)
- **Initialization**:
    - Remaining 80 units: Government places active SELL orders.
- **Run Tick**:
    - Process Mortgage -> Rent -> Market Matching -> Foreclosure.

---

## Verification
Create `tests/verify_real_estate_sales.py`:
1. **Mortgage Creation**: Loan created with correct Principal.
2. **Ownership Transfer**: Seller -> Buyer.
3. **Foreclosure**: Default -> Bank ownership -> Fire Sale order.
4. **Quality Tier**: Verify units have tiers and rich agents buy expensive ones (if possible).
