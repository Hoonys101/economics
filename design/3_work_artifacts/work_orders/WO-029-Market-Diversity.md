# Work Order 029: Market Diversity & Economy of Things

**Phase**: 17+
**Target**: `simulation/markets`, `simulation/agents`
**Objective**: Introduce structural diversity to the economy by adding Service (Time-based), Real Estate (Asset-based), and Raw Material (B2B) markets.

---

## 1. Context & Motivation
Currently, our economy is "Flat". All goods behave like "Consumer Goods" (produced, stored, consumed).
- **Service Sector**: In reality, 70% of GDP is services, which cannot be stored (Time is the resource).
- **Real Estate**: The biggest asset class, providing "Housing Services" (Utility) and "Capital Gain" (Investment).
- **Raw Materials**: Firms currently produce from thin air (Labor + Capital). A real economy has a supply chain (Iron -> Steel -> Car).

This WO aims to implement these three pillars to create a "Deep Economy".

---

## 2. Design Specification

### 2.1 The Service Market (Time-Sensitive)
*Characteristics: Zero Inventory, Immediate Consumption, Labor Intensive.*

#### Architecture
- **Sector Definition**: `service.medical`, `service.education`, `service.hair`, `service.restaurant`.
- **The "Perishable" Logic**:
    - Unlike goods, Services **cannot be carried over** to the next tick.
    - **Implementation**: At `post_step()`, any unsold Service Inventory is **voided** (set to 0).
    - *Economic Consequence*: Service firms must price competitively to clear the market, or suffer 100% loss of COGS (Cost of Goods Sold).
- **Production Function**:
    - Heavily weighted on **Labor** ($L$).
    - $Y = A \cdot L^\alpha \cdot K^\beta$ where $\alpha > \beta$ (e.g., 0.8 vs 0.2).

#### Household Utility
- Services satisfy specific needs (Health, Education, Leisure).
- **Saturation**: Services often have high immediate utility that decays instantly (no "stockpile" benefit).

---

### 2.2 The Real Estate Market (Asset & Rent)
*Characteristics: High Value, Low Liquidity, Dual-Stream Income (Rent + Appreciation).*

#### Architecture
1.  **The Asset (Property)**
    - New Class: `RealEstateAsset` (ID, Location, Quality, OwnerID).
    - **Supply**: Fixed (Land) or Slow Growth (Construction). For MVP, treated as a unique "Stock" token or a specialized "Good" with `durability = infinite`.
    - **Valuation**: $P = \frac{Rent}{Rate} + FutureValue$.

2.  **The Rental Market (The Service)**
    - Property generates `service.housing` tokens every tick.
    - **Passive Production**: No Labor required (or minimal maintenance cost).
    - These `service.housing` tokens are sold in the **Service Market**.
    - **Demand**: Households need `service.housing` for the "Shelter" need (Critical Survival Need).

3.  **The Property Market (The Exchange)**
    - Trading the `RealEstateAsset` itself.
    - High transaction cost (taxes/fees).
    - *MVP*: Use the existing `StockExchange` mechanism but for Property IDs? Or a simplified `PropertyMarket`.

---

### 2.3 The Raw Material Market (B2B Supply Chain)
*Characteristics: Intermediate Goods, Bullwhip Effect.*

#### Architecture
- **Sector Definition**: `mining.iron`, `energy.oil`, `forestry.wood`.
- **Target Audience**: **Firms Only** (B2B). Households do not consume iron.
- **Production Chain**:
    1.  **Primary Sector**: Extracts Raw Material ($Y = f(L, K, Resource)$).
    2.  **Secondary Sector** (Manufacturing): Consumes Raw Material ($Y = f(L, K, Material)$).
        - **Constraint**: If Material < Required, Production is capped.
        - $Y = \min(Potential(L, K), \frac{Material}{UnitReq})$.

#### Integration
- **Firm Agent Update**:
    - `buy_inputs()`: Before `produce()`, firms must bid for Raw Materials.
    - **Inventory Split**: `InputInventory` (Raw) vs `OutputInventory` (Finished).

---

## 3. Implementation Plan (Phased)

### Step 1: Services (The Easy Win)
- [ ] Define Service Sectors in `config.py`.
- [ ] Implement `void_unsold_inventory()` logic for Service Firms.
- [ ] Update Household Preference to value services.

### Step 2: Raw Materials (The Supply Chain)
- [ ] Define Material Sectors.
- [ ] Update `Firm.produce()` to accept `input_materials` constraint.
- [ ] Create B2B Demand Logic (Firms bidding in Market).

### Step 3: Real Estate (The Asset Class)
- [ ] Create `RealEstate` class.
- [ ] Implement Rent Generation logic.
- [ ] Implement Shelter Need for Households.

---

## 4. Verification Criteria
1.  **Service Market**: Unsold services must disappear. Prices should fluctuate more (high elasticity).
2.  **Supply Chain**: A shortage in Iron must cause a drop in Car production (Correlation check).
3.  **Real Estate**: Households must pay rent. Landlords must earn passive income.
