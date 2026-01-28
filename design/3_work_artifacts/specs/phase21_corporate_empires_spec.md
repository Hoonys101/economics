# Phase 21: Corporate Empires - Technical Specification

## 1. Overview
Phase 21 introduces "System 2" thinking to Firms, transforming them from reactive profit-seekers into strategic "Corporate Empires". This phase addresses the labor shortage (from Phase 20) via Automation and enables aggressive market consolidation via Hostile Takeovers.

## 2. Architecture: The AI CEO
The Firm's decision-making architecture is split into Strategy (System 2) and Execution (System 1/Corporate Manager), mirroring the Household architecture.

### 2.1 Component Responsibilities
| Component | Role | Responsibility |
|-----------|------|----------------|
| **FirmSystem2Planner** | **Strategy** | Long-term NPV projection, setting `target_automation`, `rd_intensity`, and `expansion_mode`. |
| **CorporateManager** | **Execution** | Translating strategy into orders (CAPEX, Hiring, Pricing, M&A Bid). |
| **FirmAI (DecisionEngine)** | **Controller** | Orchestrating the flow: Input -> System 2 -> Strategy -> Manager -> Action. |

## 3. Automation Mechanics
To solve the "Labor Crisis", firms can invest in Automation to reduce labor dependency.

### 3.1 The "Iron Army" Production Function
We modify the standard Cobb-Douglas function to shift weight from Labor ($L$) to Capital ($K$) as Automation ($A$) increases.

$$ \alpha_{base} = \text{LABOR\_ALPHA (Config, e.g., 0.7)} $$
$$ \alpha_{adjusted} = \alpha_{base} \cdot (1 - A \cdot \text{AUTOMATION\_LABOR\_REDUCTION}) $$

$$ Y = TFP \cdot L^{\alpha_{adjusted}} \cdot K^{(1 - \alpha_{adjusted})} $$

*   **$A$ (Automation Level)**: 0.0 to 1.0 (float).
*   **Effect**: As $A \to 1.0$, Labor Exponent $\to 0.35$ (assuming 50% reduction). Production becomes Capital-dominant.
*   **Constraint**: $L_{minimum} = \lceil Y / \text{MAX\_OUTPUT\_PER\_ROBOT} \rceil$. Even fully automated factories need maintenance crews.

### 3.2 Investment Cost
Automation is treated as a special asset class or an upgrade to Capital Stock.
*   **Cost**: `AUTOMATION_COST_MULTIPLIER` * Target Increment * Firm Size (Assets).
*   **Depreciation**: Automation level decays slightly over time (software rot/obsolescence), requiring maintenance investment.

## 4. Firm System 2 Planner
### 4.1 Project Future (NPV)
The planner projects cash flows for $T=100$ ticks.
1.  **Revenue**: Forecast based on current market share and demand growth.
2.  **Costs**:
    *   Labor Cost: $L_{req} \times \text{Expected Wage}$.
    *   Automation Cost: Investment required to reach/maintain Target $A$.
3.  **NPV**: $\sum \frac{Revenue - Cost}{(1 + r)^t}$.

### 4.2 Personality Weights
Personalities dictate the "Preferred Strategy" when NPVs are close.

| Personality | Automation Weight | R&D Weight | M&A Aggressiveness |
|-------------|-------------------|------------|--------------------|
| **CASH_COW** | **High (1.5)**<br>Focus: Cost Cutting | Low (0.5) | Low (Defensive) |
| **GROWTH_HACKER** | Low (0.8) | **High (1.5)**<br>Focus: Innovation | **High (Predator)** |
| **BALANCED** | Normal (1.0) | Normal (1.0) | Opportunistic |

## 5. M&A Expansion: Hostile Takeovers
Existing M&A is purely valuation-based. We add "Hostile" logic for undervalued public firms.

### 5.1 Criteria
A firm is a target for Hostile Takeover if:
1.  **Undervalued**: `Market Cap < Intrinsic Value * 0.7` (30% discount to Book Value + Inventory).
2.  **Predator Capacity**: `Predator Assets > Target Market Cap * 1.5`.

### 5.2 Execution
*   **Friendly**: Board approves (Target is struggling).
*   **Hostile**: Board rejects, but Predator bypasses (Tender Offer).
    *   **Success Probability**: 60% base. Adjusted by price premium offered.
    *   **Result**: If successful, Target is delisted and absorbed.

## 6. Configuration Updates (New Constants)
*   `AUTOMATION_LABOR_REDUCTION = 0.5` (Max 50% reduction in alpha)
*   `AUTOMATION_COST_PER_PCT = 1000.0` (Base cost scaling)
*   `HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD = 0.7`
