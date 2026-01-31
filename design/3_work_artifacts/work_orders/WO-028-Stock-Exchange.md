# Work Order: - The Stock Exchange (Phase 14-4)

## 1. Objective
Implement a fully functional **Secondary Stock Market** (Stock Exchange) where Households and Firms can trade equity.
Transition from "Book Value" pricing to "Market Price" determined by Supply and Demand via a **Call Auction (Batch)** mechanism.

## 2. Core Concepts

### 2.1 Information Asymmetry (The "Fog of War")
* **Public Data (`Market` Level)**: Available to all traders.
 * `last_price`: Recent transaction price.
 * `dividend_yield`: Last dividend / Price.
 * `earnings_per_share` (EPS): Published net profit.
* **Private Data (`Firm` Level)**: Only known to the Firm (CEO).
 * `liquidity_crisis`: Imminent bankruptcy risk.
 * `rd_progress`: Internal R&D success probability.
 * `true_book_value`: Exact asset liquidation value.

### 2.2 Valuation Models (The "Mindset")
Traders (Households) will use a mix of two strategies based on their `risk_aversion`:

1. **Fundamentalist (Value Investor)**
 * **Logic**: Price = PV(Future Dividends).
 * **Target Price**: `Dividend / (RiskFreeRate + RiskPremium - GrowthRate)`
 * **Action**: Buy if `Price < Target * 0.8`, Sell if `Price > Target * 1.2`.

2. **Chartist (Momentum Trader)**
 * **Logic**: "Trend is your friend."
 * **Target Price**: `LastPrice + (LastPrice - PrevPrice) * MomentumFactor`
 * **Action**: Buy if Trend > 0, Sell if Trend < 0.

3. **Panic Seller (Liquidity Crisis)**
 * **Condition**: `Cash < Liquidity_Need * 0.5`.
 * **Action**: **Market Sell** (Dump) existing shares regardless of price until liquidity is restored.

### 2.3 Treasury Stock Buyback (The "Corporate Action")
* **Actor**: `CorporateManager` (CEO).
* **Condition**:
 * Firm has Excess Cash (`Cash > SafetyBuffer * 2.0`).
 * Stock is Undervalued (`MarketPrice < BookValue * 0.8`).
 * **OR** Firm wants to boost ROE/EPS.
* **Effect**: Firm buys its own stock from the market and **retires (burns)** it, reducing total shares outstanding.

## 3. Mechanism: Batch Auction (Call Market)

To ensure stability and performance, trading occurs in **batches**, not real-time continuous double auction.

* **Frequency**: Once per day (e.g., every 24 ticks or specific `market_open` tick).
* **Order Book**:
 * Collects all `Limit Orders` (Price, Qty) and `Market Orders` (Qty).
* **Matching Logic**:
 1. Construct Cumulative Demand and Supply curves.
 2. Find **Equilibrium Price ($P^*$)**: The price that maximizes trade volume.
 3. Execute all matching orders at $P^*$.
* **Price Limits**: Daily Circuit Breakers (±30%) to prevent flash crashes.

## 4. Implementation Steps

### 4.1 Data Structures (`simulation/models.py`, `simulation/schemas.py`)
* **`StockOrder`**: Add `order_type` (LIMIT, MARKET), `expiration`.
* **`OrderBook`**: New class to handle batch matching.

### 4.2 Stock Exchange System (`simulation/markets/stock_exchange.py`)
* **`StockExchange` Class**:
 * `match_orders(firm_id)`: Implementation of Batch Auction algorithm.
 * `get_public_info(firm_id)`: Returns sanitized public data.

### 4.3 Agent Updates
* **Household (`PortfolioManager`)**: Include `invest_style` (Value vs Momentum) and logic to generate Limit/Market orders.
* **Firm (`CorporateManager`)**: Add `buyback_logic` to `realize_ceo_actions`.

## 5. Success Criteria
1. **Price Dissociation**: Market Price diverges from Book Value.
2. **Volume Generation**: Trading occurs between different agent types (Value vs Momentum).
3. **Bubbles & Crashes**: Observe price run-ups followed by corrections (or crashes on earnings shock).
4. **Buybacks**: Firms successfully retire shares when cash-rich/undervalued.

## 6. Verification Plan
* **Script**: `scripts/verify_stock_market.py`
 * Simulate a "Bubble" scenario:
 1. High Dividends -> Value Investors Buy.
 2. Price Rise -> Momentum Traders Join.
 3. Dividend Cut (Shock) -> Crash.
