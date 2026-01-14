# System Architecture & Economic Cycle (Architectural Audit)

**Date**: 2026-01-02
**Version**: 3.0 (Post-Audit)

---

## 1. The Macro-Economic Machine

```mermaid
graph TD
    %% Core Entities
    HH[Households (Consumers/Workers)]
    Firm[Firms (Producers/Employers)]
    Gov[Government (Fiscal Policy)]
    CB[Central Bank (Monetary Policy)]
    
    %% Markets
    GM[Goods Market]
    LM[Labor Market]
    BM[Loan Market (Banks)]
    SM[Stock Market]

    %% Interactions
    HH -->|Labor| LM
    LM -->|Wages| HH
    
    Firm -->|Wages| LM
    Firm -->|Goods| GM
    
    HH -->|Consumption Payment| GM
    GM -->|Goods| HH
    GM -->|Revenue| Firm
    
    %% Fiscal Policy (Phase 4.5)
    HH -->|Income Tax| Gov
    Firm -->|Corporate Tax| Gov
    Gov -->|Infrastructure Invest (TFP)| Firm
    Gov -->|Welfare/Subsidy| HH
    
    %% Monetary Policy (Phase 10 & Audit)
    CB -->|Base Rate (Taylor Rule)| BM
    BM -->|Deposit Rate| HH
    BM -->|Loan Rate| Firm
    
    %% Capital Markets (Phase 25)
    SM -->|Dividends| HH
    HH -->|Investment (Orders)| SM
    Firm -->|SEO (Treasury Shares)| SM
    SM -->|Capital Injection| Firm
    
    %% The Missing Link (Restored)
    HH -- High Rates --> |Increases| Savings(Deposits)
    HH -- Low Rates --> |Increases| Consumption
    
    %% Corporate Metabolism (Phase 9/25)
    Firm -- M&A --> Firm
    Firm -- Bankruptcy --> Liquidation
    Firm -- IPO/SEO --> SM
```

## 2. Logic Flow (The Pulse)

### A. The Real Economy (Goods & Labor)
1.  **Production**: Firms produce goods using Capital ($K$) and Labor ($L$).
2.  **Income**: Firms pay Wages ($W$) to Households.
3.  **Consumption**: Households spend Income on Goods ($C$).
    *   *Logic*: $C = f(\text{Needs}, \text{Assets}, \text{Prices}, \text{Inflation Expectation}, \text{Interest Rate})$.
4.  **Profit**: Firms earn Revenue ($P \times Q$).

### B. The Financial Loop (Money, Rates & Equity)
1.  **Inflation Sensing**: `Tracker` detects Price ($P$) changes.
2.  **Monetary Reaction**: `CentralBank` adjusts `Base Rate` ($i$) via Taylor Rule.
    *   $i = r^* + \pi + 0.5(\pi - \pi^*) + 0.5(y)$
3.  **Transmission**:
    *   `Bank` updates `Deposit Rate` and `Loan Rate`.
    *   **Equity Market**: Households allocate to `StockMarket` based on Merton's optimal weight.
    *   **Portfolio Management**: Assets move across Cash <-> Deposit <-> Equities.
4.  **Capital Reallocation**: Firms raise cash via `Secondary Offerings` of Treasury shares when liquidity is low.

### C. The Life Cycle & Ownership (Birth, death & IPO)
1.  **Households**:
    *   **Mitosis**: If Assets > Threshold, split (reproduce).
    *   **Death**: If Assets < 0 for too long (Starvation).
2.  **Firms**:
    *   **Startup & IPO**: Rich Households start new Firms with automatic IPO.
    *   **Treasury Management**: Firm AI decides whether to sell or buy back shares.
    *   **M&A**: Rich Firms buy Poor Firms via market transactions.
    *   **Bankruptcy**: Insolvent Firms are liquidated; shareholders lose value.

---

## 3. Current Integrity Status
- **Blue**: Implemented & Verified.
- **Red**: Missing or Broken.

1.  [Blue] Market Clearing (Order Book)
2.  [Blue] Fiscal Loop (Tax/Spend)
3.  [Blue] Inflation Psychology (Adaptive Expectations)
4.  [Blue] M&A (Predator/Prey)
5.  [Blue] **Interest Rate Channel** (Restored via `AIDrivenHouseholdDecisionEngine` heuristic)

**System is now aligned with the Blueprint.**
