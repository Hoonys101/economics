# Phase 17-3: Real Estate Market (The Landlord & The Mortgage)

## 1. Overview
This phase introduces **Real Estate** as the third asset class (after Goods and Stocks).
Real Estate has unique physics: **Finite Supply**, **Durability**, and **Exclusivity**.

> **Scope**: Residential Real Estate only. Commercial real estate is out of scope.
> **AI Approach**: Manager-driven (NPV calculation), not RL-driven.

---

## 2. Core Data Model

### 2.1. `RealEstateUnit` (New Class)
```python
@dataclass
class RealEstateUnit:
    id: int
    owner_id: Optional[int] = None  # None = Government-owned
    occupant_id: Optional[int] = None  # Tenant (if rented)
    condition: float = 1.0  # 0.0 = uninhabitable
    estimated_value: float = 10000.0  # Market price anchor
    rent_price: float = 100.0  # Monthly rent set by owner
    quality_tier: int = 1  # 1=Low (Slum), 2=Mid (Apartment), 3=High (Mansion) (For Phase 17-4 Vanity)
    mortgage_id: Optional[int] = None  # Linked loan ID
```

### 2.2. Household Updates
```python
class Household:
    # Existing attributes...
    owned_properties: List[int] = []  # IDs of owned RealEstateUnits
    residing_property_id: Optional[int] = None  # Where I live
    is_homeless: bool = False
```

---

## 3. Market Structure

### 3.1. Rental Market (Phase 17-3A Priority)
- **Mechanism**: Service-like (1-tick usage right).
- **Landlord**: Sets `rent_price` on vacant properties.
- **Tenant**: Pays rent to landlord each tick.
- **Eviction**: Failure to pay → `occupant_id = None`, tenant becomes homeless.
- **Homeless Penalty**: `Utility -= HOMELESS_PENALTY_PER_TICK` (e.g., 50.0).

### 3.2. Sales Market (Phase 17-3B)
- **Mechanism**: Order Book (like Stock Market).
- **Buyer**: Places BUY order for property ID.
- **Seller**: Places SELL order with asking price.
- **Mortgage Integration**: Buyer can use Mortgage (LTV 80%) to fund purchase.

---

## 4. Financial Integration

### 4.1. Mortgage (Phase 17-3B)
- **LTV (Loan-to-Value)**: 80% of property value.
- **Down Payment**: Buyer pays 20% from assets.
- **Monthly Payment**: Interest + Principal amortization.
- **Collateral**: Property is linked to `mortgage_id`.

### 4.2. Maintenance Cost (Phase 17-3A)
- **Rate**: `0.1%` of property value per tick.
- **Deduction**: Owner's assets decrease by maintenance cost.
- **Condition Decay**: If not paid, `condition` decreases (future enhancement).

---

## 5. AI Logic: HousingManager

### 5.1. Rent vs Buy Calculator
```python
def should_buy(self, household, property_value, rent_price, interest_rate):
    """NPV-based decision."""
    horizon = 120  # ticks
    discount_rate = 0.05 / 100  # per tick
    
    # Rent NPV (cost over horizon)
    rent_npv = sum(rent_price / (1 + discount_rate)**t for t in range(horizon))
    
    # Buy NPV (down payment + mortgage payments + maintenance - appreciation)
    down_payment = property_value * 0.2
    monthly_payment = (property_value * 0.8 * interest_rate) / 12
    maintenance = property_value * 0.001
    appreciation_rate = 0.002  # per tick
    
    buy_cost_npv = down_payment + sum(
        (monthly_payment + maintenance) / (1 + discount_rate)**t 
        for t in range(horizon)
    )
    appreciation_npv = sum(
        property_value * appreciation_rate / (1 + discount_rate)**t 
        for t in range(horizon)
    )
    buy_npv = buy_cost_npv - appreciation_npv
    
    return buy_npv < rent_npv
```

### 5.2. Landlord AI (Rent Pricing)
```python
def set_rent_price(self, property, vacancy_rate):
    """Greedy algorithm based on vacancy."""
    if vacancy_rate > 0.1:  # High vacancy
        return property.rent_price * 0.95  # Reduce 5%
    else:  # Low vacancy
        return property.rent_price * 1.05  # Increase 5%
```

---

## 6. Initial Distribution (Genesis)

### 6.1. Strategy: "Indebted Landlord"
- **Top 20%** households by initial assets receive 1 property each.
- **Simultaneously**, they receive a **Mortgage Loan** for 80% of property value.
- **Effect**: Rich households start with assets but also debt. Creates rental supply.

### 6.2. Remaining Properties
- Owned by **Government** (or Bank as placeholder).
- Available for purchase in Sales Market.

---

## 7. Engine Integration

### 7.1. `Simulation.__init__`
```python
# Create 100 RealEstateUnits
self.real_estate_units: List[RealEstateUnit] = [
    RealEstateUnit(id=i, estimated_value=10000.0) for i in range(100)
]

# Distribute to top 20% households
top_households = sorted(self.households, key=lambda h: h.assets, reverse=True)[:20]
for i, hh in enumerate(top_households):
    unit = self.real_estate_units[i]
    unit.owner_id = hh.id
    hh.owned_properties.append(unit.id)
    hh.residing_property_id = unit.id  # Owner lives there initially
    # Create mortgage (details in Bank/LoanMarket)
```

### 7.2. `run_tick` Order
1. **Rent Collection**: Tenants pay landlords.
2. **Maintenance Deduction**: Owners pay upkeep.
3. **Mortgage Payment**: Owners pay bank.
4. **Homeless Check**: Households without residence get penalty.
5. **Housing Market Matching**: (Phase 17-3B)

---

## 8. Configuration (`config.py`)

```python
# Real Estate
NUM_HOUSING_UNITS = 100
INITIAL_PROPERTY_VALUE = 10000.0
INITIAL_RENT_PRICE = 100.0
MAINTENANCE_RATE_PER_TICK = 0.001  # 0.1%
HOMELESS_PENALTY_PER_TICK = 50.0
MORTGAGE_LTV = 0.8  # 80%
PROPERTY_APPRECIATION_RATE = 0.002  # 0.2% per tick
```

---

## 9. Implementation Phases

### Phase 17-3A (Priority)
1. Create `RealEstateUnit` class in `simulation/models.py`.
2. Add `owned_properties`, `residing_property_id`, `is_homeless` to `Household`.
3. Implement Rental Market (rent collection, eviction).
4. Implement Maintenance Cost deduction.
5. Implement Homeless Penalty.
6. Initial Distribution (top 20%).

### Phase 17-3B (Deferred)
1. Sales Market (Order Book for properties).
2. Mortgage integration with Bank.
3. HousingManager `should_buy()` logic.

---

## 10. Verification Plan

### Test Script: `tests/verify_real_estate.py`
1. **Rent Flow**: Tenant pays landlord → landlord's assets increase.
2. **Eviction**: Tenant with 0 assets → becomes homeless.
3. **Homeless Penalty**: Homeless household utility decreases.
4. **Maintenance**: Owner's assets decrease by 0.1% of property value.
5. **Initial Distribution**: Top 20% have properties.

### Manual Verification
- Run 100-tick simulation.
- Check: Rent transactions in logs.
- Check: Homeless count over time.
- Check: Property value stability.
