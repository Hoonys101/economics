# Work Order: (Phase 17-3B: Real Estate - Sales & Mortgage) [Updated]

**Objective**: Implement Real Estate Sales Market, Mortgage System, and **Personality-driven** Housing Manager.

**Reference Spec**: `design/specs/phase17_3_real_estate_spec.md`

## Required Changes

### 1. Household Update (`simulation/core_agents.py`)
- **Personality Attributes**:
 - Add `ambition`, `conformity`, `patience`, `optimism` (float 0.0~1.0).
 - Initialize with random values (or Gaussian distribution).

### 2. HousingManager AI (`simulation/decisions/housing_manager.py`)
- **Proxy Planner**:
 - `should_buy(household, unit_price, rent_price)`:
 - **Base Logic**: NPV(Buy) > NPV(Rent).
 - **Personality Bias**:
 - `Optimism`: Increases perceived appreciation rate (overvalues future gains).
 - `Ambition`: Adds "Prestige Value" to Buy Utility (Buy NPV += Price * 0.1 * Ambition).
 - If `Buy NPV + Bias > Rent NPV`, return True.

### 3. Market Structure (`simulation/markets.py` & `engine.py`)
- **HousingMarket**: Reuse `OrderBookMarket` with unique `item_id`.
- **Engine**: Match orders in `_process_market_matching`.

### 4. Mortgage System (`simulation/bank.py`)
- **Mortgage Loan**: LTV 80%, 360 ticks.
- **Foreclosure**: 3 missed payments -> Seize -> Fire Sale.

### 5. Engine Integration (`simulation/engine.py`)
- **Run Tick**: Mortgage -> Rent -> Matches -> Foreclosure.
- **Initialization**: Government sells remaining units.

---

## Verification
Create `tests/verify_real_estate_sales.py`:
1. **Mortgage Creation**: Verify Loan parameters.
2. **Ownership Transfer**: Verify Seller -> Buyer.
3. **Foreclosure**: Verify Eviction & Fire Sale.
4. **Personality Bias**:
 - Create two households: Optimist (opt=1.0) vs Pessimist (opt=0.0).
 - Verify Optimist buys even when NPV is slightly negative (due to bias).
 - Verify Pessimist rents even when NPV is slightly positive (optional).
