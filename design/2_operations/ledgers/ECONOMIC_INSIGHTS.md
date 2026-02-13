# Economic Insights Ledger: The Knowledge Base

> **"Knowledge survives, artifacts perish."**
> This ledger is the permanent repository for systemic, behavioral, and monetary wisdom derived from the simulation.

---

## 🏗️ [System] Simulation Rules & Innovation
*Rules of physics, innovation dynamics, and governance mechanics.*

- **[2026-01-25] R&D Investment and Endogenous Innovation**
    - Transition from time-based to probabilistic unlock models driven by firm activity.
- **[2026-02-09] Cockpit's Direct State Injection (Divine Intervention)**
    - Implementation of a real-time policy control layer. Identified the need for "Divine Intervention" event types to avoid side-effect isolation and state inconsistencies.
    - [Insight Report](../_archive/insights/2026-02-09_Cockpit_Direct_State_Intervention.md)

---

## 💰 [Monetary] Circulation & Integrity
*M2 integrity, zero-sum principles, and financial market logic.*

- **[2026-02-13] Quantitative Easing & Bond Yield Feedback**
    - Implemented a dynamic sovereign risk premium mechanism. Government bond yields now fluctuate based on the Debt-to-GDP ratio. In scenarios where market liquidity is insufficient to absorb new debt (High Debt/GDP > 1.5), the Central Bank acts as the "Buyer of Last Resort" (Quantitative Easing), ensuring fiscal continuity at the cost of potential inflationary pressure (to be modeled in future phases).
    - [Insight Report](../../communications/insights/mission-found-02.md)
- **[2026-02-09] Judicial Decoupling & Event-Driven Consequence**
    - Separation of bank credit destruction from punitive governance actions.
    - [Insight Report](../_archive/insights/TD-261_Judicial_Decoupling.md)
- **[2026-02-09] Protocoled Liquidation (TD-269)**
    - Decoupling LiquidationManager from concrete Firm internals via `ILiquidatable`.
    - [Insight Report](../_archive/insights/TD-269_Liquidation_Refactor_Insight.md)
- **[2026-02-09] Settlement System Purity (Track A)**
    - Consolidating financial agent interactions through centralized settlement.
    - [Insight Report](../_archive/insights/PH9.2_TrackA.md)
- **[2026-02-09] Market DTO Unification**
    - Standardizing order flow through Canonical DTOs to ensure market integrity.
    - [Insight Report](../_archive/insights/PH9.2_Market_DTO_Unification.md)
- **[2026-02-09] Structural Integrity: Seizure Waterfall & Finance Commands (PH10.3)**
    - Implementation of hierarchical asset recovery (Cash->Stock->Inventory) and stateless Finance system command pattern.
    - [Insight Report](../_archive/insights/2026-02-09_PH10.3_Structural_Integrity.md)
- **[2026-02-09] Protocol Purification: IConfigurable (TD-LIQ-INV)**
    - Decoupling configuration access from agent internals via formal protocols and DTOs.
    - [Insight Report](../_archive/insights/2026-02-09_TD-LIQ-INV_Protocol_Purification.md)
- **[2026-02-12] The Penny Standard: Integer Enforcement**
    - Identified critical system failures caused by floating-point drift in financial transfers. Mandated explicit `int()` casting at all `SettlementSystem` boundaries. Money in this simulation is discrete, not continuous.
    - [Insight Report](../_archive/insights/2026-02-12_Penny_Standard_Integer_Enforcement.md)
- **[2026-02-13] Solvency & Asset Liquidation Discounting**
    - Established the principle of conservative valuation for solvency checks. Inventory and illiquid assets should be valued at a "liquidation discount" (e.g., 50%) to prevent over-leveraging and systemic collapse.
    - [Insight Report](../_archive/insights/2026-02-13_Solvency_Aggregation_Challenges.md)

---

## 🧠 [Behavior] Agent Logic & Animal Spirits
*Economic psychology, survival instincts, and population dynamics.*

- **[2026-01-25] Grace Protocol for Agent Solvency**
    - Distinguishing Liquidity from Solvency through Fire Sale mechanisms.
- **[2026-02-10] Ecosystem Health Affects Survival Decisions**
    - **Insight**: Individual agent decisions (e.g., survival spending, production choices) are directly influenced by their perception of the broader ecosystem's health. A declining economy triggers more conservative, survival-focused behaviors, whereas a booming economy encourages risk-taking and investment.
    - **Mechanism**: The `health_factor` in the `SurvivalEngine` acts as a key psychological input, modulating an agent's willingness to spend versus save, creating a feedback loop between macro conditions and micro behavior.
    - [Insight Report](../_archive/insights/2026-02-10_Ecosystem_Health_and_Agent_Decisions.md)
- **[2026-01-15] Population Dynamics & Birth Rate (r/K Selection)**
    - Analysis of expectation mismatch and childcare time constraints on population.
