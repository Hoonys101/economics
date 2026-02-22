# Blueprint: Social & Health Dynamics (Marriage & Disease)

## 💍 1. The Marriage Market (Household M&A)

### 1.1 Conceptual Goal
Shift from "Parthenogenesis/Individual Spawning" to a social model where households merge to achieve **Economies of Scale**.

### 1.2 Matching Mechanics (Matching Engine)
*   **Engine:** Re-use the `Search & Bargaining` engine logic.
*   **Valuation Factors:**
    - **Age Alignment:** Preference for similar age brackets.
    - **Wealth Match:** Sorting by asset classes (Hypergamy/Assortative Mating).
    - **Education Signal:** The "Halo Effect" also applies to social status.
*   **Result:** Two `Household` agents form a `Family` bond.

### 1.3 Economic Merge (Wallet Merge)
*   **Joint Assets:** Balances are pooled into a single financial steering unit.
*   **Cost Efficiency (Scale):** 
    - `Cost_2_Person = Cost_1_Person * 1.5` (not 2.0).
    - Reduced overhead for housing and essentials.
*   **Shared Resilience:** One partner's unemployment can be buffered by the other's income.

### 1.4 Reproduction (Generational Continuity)
*   **Trigger:** `is_married == True` + `Tick` + `Age-based Prob`.
*   **Dependency:** Children are dependants (`consumer` only) until graduation.

---

## 🦠 2. The "Health Shock" Engine (Baseline Model)

### 2.1 Conceptual Goal
Introduce a destructive exogenous shock that forces agents to prioritize survival over discretionary spending, triggering **Precautionary Saving (예비적 저축)**.

### 2.2 Sickness Propensity (The Multiplier)
$P(sickness) = \beta_0 + \beta_{age}(Age) + \beta_{pov}(Hunger)$
*   **Aging:** Probability increases exponentially with agent age.
*   **Poverty Link:** Cumulative ticks of starvation (unmet bread needs) severely degrade the `health_factor`, making the poor much more susceptible to shocks.

### 2.3 Economic Penalties (The "Health Trap")
1.  **Lost Labor:** Immediate `Productivity = 0` and `Wage = 0`. The agent cannot earn money while sick.
2.  **Inelastic Demand:** The agent's AI switches to "Survival Mode." They will spend up to their **Total Wealth** to purchase `MEDICAL_SERVICE`. Prices for this service are naturally high due to the high-skill requirements for Doctors (High Education/Talent).
3.  **The Deadly Spiral:** If an agent is unemployed and sick, they bleed assets for medical care until they are cured or reach **Liquidation (Death)**.

### 2.4 Emergence: Precautionary Saving
The mere *possibility* of a health shock drives agents to hoard cash in banks instead of consuming 100% of their income. This increases total bank deposits and credit liquidity in the macro-economy.

---

## 🏛️ Policy Holding Note (PHASE 8+)
The following are **ON HOLD** to avoid premature complexity:
- **Public Healthcare (NHI):** Government monopsony and price ceilings.
- **Private Insurance:** Monthly premiums and risk-pooling products.
- **Doctor's Strike:** High-insight doctors fleeing to non-essential services (Cosmetic) due to price controls.

---

## 🛠️ Implementation Strategy

| Component | Target System | Change Description |
| :--- | :--- | :--- |
| **Lifecycle** | `LifecycleManager` | Replace individual spawn logic with Marriage + Child birth. |
| **Portfolio** | `SettlementSystem` | Implement `Agent_Merge` functionality for shared wallets. |
| **Scheduler** | `WorldState` | Add random `Sickness_Roll` per tick based on age/wealth. |
| **Market** | `CommerceSystem` | Add `Medical_Service` as a non-optional commodity. |
