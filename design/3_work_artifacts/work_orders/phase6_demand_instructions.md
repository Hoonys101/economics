# W-2 Work Order: Phase 6 - The Smart Consumer (Demand Side)

> **Assignee**: Jules
> **Priority**: P1 (Feature)
> **Branch**: `feature/brand-economy-demand`
> **Base**: `main`

---

## 📋 Overview
> **Current Status**: **Supply Side (Firm, BrandManager, Market) is IMPLEMENTED.**
> **Missing Link**: Households are still "Price-Blind". They do not see Brands.
> **Goal**: Implement `Household` logic to select sellers based on **Utility** (Price + Quality + Awareness).

## 📄 References
- **Master Spec**: `design/specs/phase6_brand_economy_spec.md` (Updated with Architect Prime's formulas)

---

## ✅ Implementation Integration Tasks

### 1. Household Agent Update (`simulation/core_agents.py` or `household.py`)
- **Action**: Add `quality_preference` attribute in `__init__`.
- **Logic**:
    - **Snob**: `random.uniform(0.7, 1.0)` (Top 20% Initial Assets OR `Materialistic`)
    - **Miser**: `random.uniform(0.0, 0.3)` (Bottom 20% Initial Assets OR `Frugal`)
    - **Average**: `random.uniform(0.3, 0.7)` (Others)

### 2. Decision Engine Update (`simulation/decisions/ai_driven_household_engine.py`)
- **Action**: Implement independent `choose_best_seller(market_snapshot)` method.
- **Formula**:
    $$Utility = \frac{Q_{perc}^{\alpha} \cdot (1 + Awareness)^{\beta}}{P}$$
    - $\alpha$ (Alpha): `household.quality_preference`
    - $\beta$ (Beta): 0.5 (Default)
    - Metadata (`awareness`, `quality`) is available in `market_snapshot['sell_orders']` (injected by Firm).

- **Action**: Update `make_decisions` (Consumption Logic)
    - **Before**: Just create `BUY` order at `avg_price`.
    - **After**:
        1. Call `choose_best_seller()` for the item.
        2. If result found ($Firm^*$): Create `BUY` order with `target_agent_id = Firm^*`.
        3. If no result: Create `BUY` order without target (General Pool).

### 3. Config Update (`config.py`)
- `BRAND_SENSITIVITY_BETA = 0.5`
- `QUALITY_PREF_SNOB_MIN = 0.7`
- `QUALITY_PREF_MISER_MAX = 0.3`

---

## 🧪 Verification Plan
Create `scripts/verify_brand_economy.py`:

**Scenario A: The "Apple" Test (High Pref)**
- Setup: Firm A (High Price, High Brand) vs Firm B (Low Price, Low Brand).
- Check: Do Households with `quality_preference > 0.8` buy from Firm A?

**Scenario B: The "Daiso" Test (Low Pref)**
- Setup: Same Firms.
- Check: Do Households with `quality_preference < 0.2` buy from Firm B?

---

## 🚀 Execution Steps
1. Checkout `main` and pull latest.
2. Create branch `feature/brand-economy-demand`.
3. Implement `Household` preference logic.
4. Implement `choose_best_seller` and connect to `make_decisions`.
5. Run `verify_brand_economy.py`.
6. Submit PR.
