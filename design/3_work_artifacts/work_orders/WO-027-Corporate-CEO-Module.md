# Work Order: (The Corporate CEO Module)

**Phase**: 16-B (Corporate Intelligence)
**Assignee**: Jules (Implementation Lead)
**Status**: Draft

## 1. Goal
Upgrade Firms from "Production Machines" to "Strategic Entities". Firms must now manage **Retained Earnings** and decide between **Dividends**, **CAPEX (Expansion)**, and **R&D (Innovation)** based on market competitiveness.

## 2. Structural Hierarchy (Agent AI Architecture)

We maintain the established two-layer architecture:

## 2. Structural Hierarchy (The CEO Intelligence)

We implement a three-layer brain for Firms:

### A. The Personality Layer (Fixed Trait)
* **Categories**: `BALANCED`, `GROWTH_HACKER` (Market Share Focus), `CASH_COW` (Profit/Dividend Focus).
* **Role**: Determines the **Reward Weights** for the RL agent.

### B. The RL Layer (Top-Down Intention: `FirmAI`)
* **State Features (What the CEO sees)**:
 1. **Competitive Quality Gap**: `(Market_Avg_Quality - My_Quality)`.
 2. **Inventory Runway**: `Inventory / Sales_Volume_Avg`.
 3. **Liquidity Buffer**: `Cash / Daily_Expenses`.
* **Action Channels (The 5 Strategic Levers)**:
 1. `q_rd_agg`: Innovation Aggressiveness.
 2. `q_cap_agg`: Expansion Aggressiveness.
 3. `q_div_agg`: Dividend Aggressiveness.
 4. `q_hiring_agg`: Employment Aggressiveness (Talent War vs Layoffs).
 5. `q_debt_agg`: Leverage Aggressiveness (Loan vs Repayment).

### C. The Logic Layer (The Executioner: `CorporateManager`)
* **Role**: Translates Aggressiveness (0.0~1.0) into concrete $ actions based on market physics.
 * **Layoffs**: Triggered if `Liquidity < 10 days` AND `q_hiring_agg < 0.3`.
 * **Investment**: Allocated from `Retained Earnings`.

## 3. The Innovation Physics (The "Gamble")
* **R&D Success Chance**: $P = \min(1.0, \frac{\text{Budget}}{\text{Revenue} \times 0.2}) \times \text{Skill_Multiplier}$.
* **Success Effect**:
 * Quality: `+0.05` to base quality.
 * Process: `+5%` to output per unit of Labor/Capital.

## 3. Implementation Tasks

### Task 1: Core Attributes (`simulation/firms.py`)
* Add `retained_earnings` tracker.
* Add `research_history` (Total spent, success count).

### Task 2: AI Engine Updates (`simulation/ai/firm_ai.py`)
* Add `q_rd` QTableManager.
* Add `rd_aggressiveness` to `decide_action_vector`.

### Task 3: Corporate Manager (`simulation/decisions/corporate_manager.py`)
* **New Class**: `CorporateManager`
* **Method**: `realize_ceo_actions(firm, market_summary, action_vector)`
 * Translates `rd_aggressiveness` $\rightarrow$ $ Amount $\rightarrow$ R&D Success/Fail.
 * Translates `capital_aggressiveness` $\rightarrow$ $ Amount $\rightarrow$ `capital_stock` increase.
* Apply the results:
 * `R&D`: Trigger success check $\rightarrow$ Update `firm.productivity_factor`.
 * `CAPEX`: Update `firm.capital_stock`.
 * `DIVIDEND`: Execute dividend payment.

## 4. Verification (The Innovation War)
* **Script**: `scripts/verify_innovation.py`
* **Scenario**:
 1. Start 2 firms in the same sector.
 2. Firm A has high `risk_aversion` (Conservative).
 3. Firm B has low `risk_aversion` (Aggressive R&D).
 4. **Expectation**: Firm B should eventually dominate the market with higher quality/lower cost, even if it loses money initially on R&D.

## 5. Definition of Done
* Firms' `productivity_factor` evolves over time.
* Market shows a spread of quality between different firms.
* Firms with low quality relative to market spend more on R&D.
