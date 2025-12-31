# W-1 Specification: Phase 6 - The Brand Economy (Concrete Engineering Spec)

> **Citation**: Based on Architect Prime's "Invisible Asset Architecture" and refined based on Team Leader's "Abstractness Review".

## 1. Overview & Objectives
**Goal**: Transition market dynamics from **Price-Blind Matching** to **Utility-Based Selection**.
**Core Change**:
*   **Old**: Market matches Highest Bid ↔ Lowest Ask.
*   **New**: Consumer picks specific Seller based on Price, Quality, and Brand.

---

## 2. Market Mechanic: The "Targeted Order" Protocol

### 2.1 Problem
`OrderBookMarket` currently matches anonymously sorted by price. Brand loyalty requires a specific buyer to trade with a specific seller.

### 2.2 Solution: Targeted Buy Orders
We will NOT replace the `OrderBookMarket`. We will extend it.

1.  **Household Side**:
    *   Instead of blindly placing a Buy Order at `reservation_price`, the Household first **scans the market**.
    *   `choose_best_seller(market, good_id)`:
        *   Get all `SellOrders` (Asks) from `market`.
        *   For each Ask (Seller $j$), calculate Utility $U_j$.
        *   Select Seller $j^*$ with $\max(U)$.
    *   Place `BuyOrder` with `target_agent_id = j^*` and `price = AskPrice_{j^*}`.

2.  **Market Side (`simulation/markets/order_book_market.py`)**:
    *   Modify `match_orders`:
        *   **Step 1: Targeted Matching**. Iterate through Buy Orders with `target_agent_id`.
        *   Find corresponding Sell Order from `target_agent_id`.
        *   If match found: Execute Transaction immediately. Remove both orders.
        *   If match NOT found (Sold out?): Buy Order **Expires/Fails** (Consumer leaves empty-handed, simulating stockout).
        *   **Step 2: Residual Matching**. Match remaining "Any Seller" Buy Orders (if any) using old Price Priority logic.

---

## 3. Mathematical Models

### 3.1 Firm: The Brand Engine (`simulation/brands/brand_manager.py`)
Encapsulate logic in a helper class.

*   **Adstock Update**:
    $$Adstock_t = (Adstock_{t-1} \times 0.8) + (MarketingSpend_t \times 0.01)$$
*   **Awareness S-Curve**:
    $$Awareness = \frac{1}{1 + e^{-Adstock}}$$
    *   (Simple Sigmoid scaled to 0.0~1.0)
*   **Perceived Quality (EMA)**:
    $$Q_{perc, t} = (Q_{actual, t} \times 0.2) + (Q_{perc, t-1} \times 0.8)$$
    *   *Note*: $Q_{actual}$ is defined as `Firm.productivity_factor / 10.0`.

### 3.2 Household: The Utility Function
When evaluating Seller $j$:

$$U_j = \frac{Q_{perc, j} \cdot (1 + Awareness_j \cdot Pref_{quality}) \cdot Loyalty_{j}}{Price_j} + \alpha \ln(SalesVolume_j + 1)$$

*   `Pref_quality`: Household's innate trait (0.0=Miser, 1.0=Snob).
*   `Loyalty_j`: Dynamic multiplier (Starts 1.0, increases on purchase, decays over time).
*   `SalesVolume_j`: Network Effect (Last tick's sales count of Firm $j$).

---

## 4. AI Training: Solving "Marketing is Cost"

### 4.1 The Problem
RL Agents optimize for `Asset Growth`. Marketing Spend reduces Assets immediately, while benefits (Brand) come later. Without guidance, AI will learn to set Marketing=0.

### 4.2 The Fix: Intangible Asset Valuation
We must "pay" the AI for building Brand.

**Modified Reward Function (`simulation/ai_model.py` or Firm wrapper)**:
$$Reward = \Delta Assets + (\Delta BrandAwareness \times ValuationMultiplier)$$

*   `ValuationMultiplier`: How much is 100% Awareness worth?
    *   Estimate: `Avg_Profit_Per_Tick * 50 ticks`.
    *   Value: `1000.0` (Configurable).

---

## 5. Implementation Roadmap (Jules' Tasks)

### Step 1: Schema & Config
1.  **`config.py`**: Add `MARKETING_DECAY`, `LOYALTY_DECAY`, `NETWORK_WEIGHT`.
2.  **`dtos.py`**: Update `Order` to include `target_agent_id` (Optional[int]).

### Step 2: The Brand Engine
1.  Create `simulation/brands/brand_manager.py`.
2.  Implement `update(spend, quality)`.
3.  Integrate into `Firm`. Firms now have `marketing_budget` decision.

### Step 3: Market Upgrade
1.  Modify `OrderBookMarket.match_orders` to handle `target_agent_id`.
    *   *Critical*: Ensure targeted trades happen *before* general sorting.
2.  Update `OrderBookMarket.get_all_asks` to return agent_id clearly.

### Step 4: Household Choice Logic
1.  Implement `Household.choose_seller(good_id)` using the Utility Formula.
    *   Needs access to `Firm.brand_awareness` & `Firm.perceived_quality`.
    *   *Access Pattern*: `Market` should publish a "Catalog" or `Household` queries `Firm` public state?
    *   *Simplification*: `OrderBookMarket` Asks can carry metadata? Or `Firm` adds metadata to `SellOrder`.
    *   **Decision**: Add `brand_info` dict to `SellOrder`. When Firm places order, it stamps current Brand/Quality on it.

### Step 5: Network Effect Pipeline
1.  `Firm` tracks `sales_last_tick`.
2.  `SellOrder` includes `sales_last_tick` in metadata.

---

## 6. Verification Checklist
1.  **Adstock Test**: Spend 100 -> Adstock goes up. Stop -> Adstock decays.
2.  **Targeting Test**: H1 targets F1. F1 price is 12, F2 is 10. H1 buys from F1 (because U(F1) > U(F2)).
3.  **AI Test**: Run simulation. Does Firm set `marketing_budget > 0`? (If 0, Reward shaping failed).
