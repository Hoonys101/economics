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

## 3.2 Household: The Utility Function (The "Smart Consumer")

### 3.2.1 Preference Initialization (`Household.__init__`)
Each household has a unique "taste" based on wealth and personality.
*   **Attribute**: `self.quality_preference` (float 0.0 ~ 1.0)
*   **Logic**:
    *   **Snob** (Top 20% Wealth OR 'Materialistic'): `Random(0.7, 1.0)`
    *   **Miser** (Bottom 20% Wealth OR 'Frugal'): `Random(0.0, 0.3)`
    *   **Average**: `Random(0.3, 0.7)`

### 3.2.2 Seller Selection Logic (`choose_best_seller`)
When buying a good, the Household evaluates all available Asks (Offers) in the market.

**Utility Score Formula**:
$$Utility_{ij} = \frac{Q_{perceived, j}^{\alpha} \cdot (1 + Awareness_j)^{\beta}}{Price_j}$$

*   $\alpha$ (Alpha): Buyer's `quality_preference`.
*   $\beta$ (Beta): Brand sensitivity (Default 0.5 or tied to preference).
*   *Interpretation*:
    *   If $\alpha \approx 0$ (Miser), Numerator $\approx 1$, so $Utility \approx 1/Price$. (Minimizes Price).
    *   If $\alpha \approx 1$ (Snob), Quality and Awareness significantly boost Utility.

### 3.2.3 Pseudocode (for Jules)
```python
def choose_best_seller(self, market_snapshot):
    best_seller_id = None
    max_score = -1.0
    alpha = self.quality_preference
    beta = 0.5  # Fixed or Configurable

    for offer in market_snapshot['asks']:
        # Extract metadata (injected by Firm)
        awareness = offer.get('brand_awareness', 0.0)
        quality = offer.get('perceived_quality', 1.0) # Default 1.0 to avoid div by zero if formula changes
        price = offer.get('price', 999.0)

        # Utility Calculation (Cobb-Douglas-ish)
        numerator = (quality ** alpha) * ((1.0 + awareness) ** beta)
        score = numerator / max(price, 0.01)

        if score > max_score:
            max_score = score
            best_seller_id = offer.agent_id

    return best_seller_id
```

## 4. Market Interaction (The Loop)
1.  **Firm**: Places Sell Order with `brand_info` (`awareness`, `quality`).
2.  **Household**:
    *   Calls `choose_best_seller()` to find $Firm^*$.
    *   Places Buy Order with `target_agent_id = Firm^*`.
3.  **Market**: `OrderBookMarket` executes **Targeted Matching** first.

---

## 5. Verification Scenarios
### Scenario A: The "Apple" Test (Snob Appeal)
*   Firm A: Price 15, Awareness 0.9, Quality 1.0
*   Firm B: Price 10, Awareness 0.1, Quality 0.5
*   **Expectation**: High `quality_preference` households buy from **Firm A** despite higher price.

### Scenario B: The "Daiso" Test (Miser Necessity)
*   Same Firms.
*   **Expectation**: Low `quality_preference` households buy from **Firm B** (Lowest Price).
