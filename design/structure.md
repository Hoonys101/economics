# System Architecture & Economic Cycle (Living Documentation)

**Date**: 2026-01-15
**Version**: 4.0 (The Living World Update)
**Audit Status**: Verified by Gemini (Reflects `simulation/` codebase)

---

## 1. The Macro-Economic Machine (Updated)

```mermaid
graph TD
    %% Core Entities & Components
    subgraph Household_Sector [Household Sector]
        HH[Households]
        H_Comp[Components: Psychology, Labour, Consumption]
        H_Sys2[System 2: Planner (NPV)]
        HH --- H_Comp
        HH --- H_Sys2
    end

    subgraph Corporate_Sector [Corporate Sector]
        Firm[Firms]
        F_Dept[Departments: HR, Finance, Production]
        F_Sys2[System 2: Planner (Automation/Expansion)]
        MAManager[M&A Manager (Corporate Metabolism)]
        Firm --- F_Dept
        Firm --- F_Sys2
        Firm --- MAManager
    end

    %% Government & Policy
    subgraph Public_Sector [Public Sector]
        Gov[Government]
        Tax[Tax Agency]
        Edu[Ministry of Education]
        FinanceSys[Finance System (Debt/Bailouts)]
        CB[Central Bank (Monetary Policy)]
        Tech[Technology Manager (R&D Diffusion)]
        FirmMgmt[Firm Management (Entrepreneurship)]
        
        Gov --- Tax
        Gov --- Edu
        Gov --- FinanceSys
        Gov --- Tech
        Gov --- FirmMgmt
    end

    %% Markets
    GM[Goods Market]
    LM[Labor Market]
    BM[Loan Market (Banks)]
    SM[Stock Market]
    HM[Housing Market]

    %% Systems
    Reflux[Reflux System (Economic Recycling)]
    Life[Lifecycle System (Demo/Immig/Inherit)]

    %% Interactions - Real Economy
    HH -->|Labor| LM
    LM -->|Wages| Firm
    Firm -->|Goods| GM
    GM -->|Revenue| Firm
    HH -->|Consumption Payment| GM
    
    %% Interactions - Financial Economy
    CB -->|Base Rate| BM
    BM -->|Loans/Deposits| Firm
    BM -->|Loans/Deposits| HH
    SM -->|Capital/Dividends| Firm
    SM -->|Investment| HH
    FinanceSys -->|Bonds| CB
    FinanceSys -->|Bonds| BM
    FinanceSys -->|Bailouts| Firm

    %% Interactions - Asset Economy
    HM -->|Housing Services| HH
    HH -->|Rent/Mortgage| HM
    Gov -->|Property Tax| HM

    %% Interactions - Systemic
    Reflux -->|Recycled Capital| HH
    Tech -->|Productivity Boost (TFP)| Firm
    Life -->|Birth/Death/Migration| HH
```

## 2. Logic Flow & Systems (The Pulse)

### A. The Cognitive Architecture (Dual Process)
1.  **System 1 (Fast/Reactive)**:
    *   **RL Agents (Q-Learning)**: `GovernmentAI`, `FirmAI`, `HouseholdAI` optimize short-term rewards via mutation and selection.
    *   **Heuristics**: `ActionProposalEngine` suggests immediate actions based on `Aggressiveness` vectors.
2.  **System 2 (Slow/Deliberative)**:
    *   **Planners**: `HouseholdSystem2`, `FirmSystem2Planner` simulate future scenarios (NPV) to make long-term decisions (Housing, Automation, R&D).
    *   **Internal World Model**: Agents project cash flows to determine `Solvency` and `Liquidity` risks.

### B. The Real Economy (Supply Chain)
1.  **Production & Technology**:
    *   Firms produce goods using $K$ and $L$.
    *   **Technology Manager**: Unlocks S-Curve TFP boosts (e.g., Chemical Fertilizer) which diffuse through the sector.
2.  **Labor & Components**:
    *   `HRDepartment`: Manages hiring/firing based on `Marginal Revenue Product of Labor` (MRPL).
    *   `LeisureManager`: Households trade off labor vs leisure based on utility.
3.  **Consumption & Reflux**:
    *   `ConsumptionBehavior`: Needs-based spending (Maslow-lite).
    *   **Reflux System**: Captures leakage (Marketing, CAPEX) and recycles it as "Service Income" to households, preserving Money Supply (M2).

### C. The Financial Superstructure (Phase 25/26)
1.  **Banking & Credit**:
    *   `Fractional Reserve`: Banks create money via loans.
    *   `Central Bank`: Sets Base Rate via Taylor Rule; acts as Lender of Last Resort.
2.  **Capital Markets**:
    *   `Stock Market`: IPOs, SEOs, and Buybacks. Households optimize portfolios using Merton's Model.
    *   `Finance System`: **(New)** Sovereign Debt issuance (Bonds) and Corporate Bailouts (Senior Loans). Solvency checked via Altman Z-Score.
3.  **Real Estate**:
    *   `Housing System`: Manages Land supply, Rental logic, and Mortgage amortization.
    *   `Immigration`: Population inflows driven by Housing affordability and Wage premiums.

### D. Lifecycle & Evolution
1.  **Demographics**:
    *   `DemographicManager`: Handles Aging, Birth (Fertility Rate), and Death.
    *   `InheritanceManager`: Transfers assets from deceased to heirs (Zero-Leak).
2.  **Evolution**:
    *   Firms with low profitability face `Bankruptcy` (Liquidation).
    *   Households with high assets reproduce (Mitosis); poor ones starve (Death).

---

## 3. Current Integrity Status
- **Blue**: Implemented & Verified.
- **Red**: Missing or Broken.

1.  [Blue] **Zero-Leak Inheritance** (Verified)
2.  [Blue] **Economic Reflux** (Verified)
3.  [Blue] **Stock Market Sync** (Verified)
4.  [Blue] **Tech Diffusion** (Verified)
5.  [Blue] **Sovereign Debt Zero-Sum** (Verified: WO-072 Merged 2026-01-16)

**System is now aligned with the Codebase (simulation/).**
