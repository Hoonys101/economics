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
    
    %% The Missing Link (Restored)
    HH -- High Rates --> |Increases| Savings(Deposits)
    HH -- Low Rates --> |Increases| Consumption
    
    %% Corporate Metabolism (Phase 9)
    Firm -- M&A --> Firm
    Firm -- Bankruptcy --> Liquidation
```

## 2. Logic Flow (The Pulse)

### A. The Real Economy (Goods & Labor)
1.  **Production**: Firms produce goods using Capital ($K$) and Labor ($L$).
2.  **Income**: Firms pay Wages ($W$) to Households.
3.  **Consumption**: Households spend Income on Goods ($C$).
    *   *Logic*: $C = f(\text{Needs}, \text{Assets}, \text{Prices}, \text{Inflation Expectation}, \text{Interest Rate})$.
4.  **Profit**: Firms earn Revenue ($P \times Q$).

### B. The Financial Loop (Money & Rates)
1.  **Inflation Sensing**: `Tracker` detects Price ($P$) changes.
2.  **Monetary Reaction**: `CentralBank` adjusts `Base Rate` ($i$) via Taylor Rule.
    *   $i = r^* + \pi + 0.5(\pi - \pi^*) + 0.5(y)$
3.  **Transmission**:
    *   `Bank` updates `Deposit Rate` and `Loan Rate`.
    *   **Households**: If $i - \pi^e > 3\%$, reduce Consumption (Save).
    *   **Firms**: If Loan Cost > ROI, reduce Borrowing/Investment.

### C. The Life Cycle (Birth & Death)
1.  **Households**:
    *   **Mitosis**: If Assets > Threshold, split (reproduce).
    *   **Death**: If Assets < 0 for too long (Starvation).
2.  **Firms**:
    *   **Startup**: Rich Households start new Firms.
    *   **M&A**: Rich Firms buy Poor Firms.
    *   **Bankruptcy**: Insolvent Firms are liquidated.

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
