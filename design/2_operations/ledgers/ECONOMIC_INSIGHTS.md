# Economic Insights Ledger: The Knowledge Base

> **"Knowledge survives, artifacts perish."**
> This ledger is the permanent repository for systemic, behavioral, and monetary wisdom derived from the simulation.

---

## 🏗️ [System] Simulation Rules & Innovation
*Rules of physics, innovation dynamics, and governance mechanics.*

- **[2026-01-25] R&D Investment and Endogenous Innovation**
    - Transition from time-based to probabilistic unlock models driven by firm activity.
- **[2026-02-13] Cockpit's Direct State Injection (Divine Intervention)**
    - Implementation of a real-time policy control layer. Identified the need for "Divine Intervention" event types to avoid side-effect isolation and state inconsistencies.
    - [Insight Report](../_archive/insights/2026-02-09_Cockpit_Direct_State_Intervention.md)
- **[2026-02-13] Baseline M2 Accountability in Mixed-Intervention Models**
    - Established that external state changes (e.g., injecting stimulus) must be mathematically reconciled with the 'Baseline M2'. In a mixed-intervention tick (automatic policy + manual injection), the audit system now distinguishes between legitimate credit expansion and corrupting "Magic Money," ensuring the simulation remains a valid environment for economic hypothesis testing.
    - [Insight Report](../../communications/insights/mission-data-01.md)
- **[2026-02-14] GlobalRegistry Architecture & Origin Priority**
    - Established a formal parameter hierarchy: `SYSTEM (0)` < `CONFIG (10)` < `GOD_MODE (20)`. This ensures user configuration properly overrides system defaults while God Mode interventions maintain absolute authority via a locking mechanism.
    - [Insight Report](../_archive/insights/2026-02-14_GlobalRegistry_Architecture.md)
- **[2026-02-14] Orchestrator-Engine Decomposition**
    - Transitioned complex Agents (Household, Firm) from Monolithic "God Classes" to the Orchestrator-Engine pattern. Decision logic (Beliefs, Crisis) is now handled by stateless, swappable components, while the Agent class focuses on state retention and routing.
    - [Insight Report](../_archive/insights/2026-02-14_Household_Decomposition.md)
- **[2026-02-14] Phase 0 Intercept & Command Atomicity**
    - Formalized the "Phase 0" slot in the Tick Orchestrator for handling external interventions. Implemented "Immediate Batch Execution" where commands are drained and executed atomically *before* simulation causality begins, preventing race conditions and double-execution bugs.
    - [Insight Report](../_archive/insights/2026-02-13_Phase0_Intercept_M2_Integrity.md)
- **[2026-02-19] Lifecycle-Settlement Atomicity**
    - **Insight**: Economic continuity requires that legal existence (Registration) strictly precedes financial existence (Capitalization). Reversing this order creates "Ghost Destinations" that crash the settlement layer.
    - [Insight Report](../_archive/insights/2026-02-19_Agent_Lifecycle_Atomicity.md)

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
- **[2026-02-19] The Penny Standard vs. Valuation Math**
    - **Insight**: While valuation models (M&A, Stock Pricing) naturally use floating-point math, the Settlement Boundary must act as a hard "Quantization Gate." Passing raw floats from valuation to settlement causes system-wide integrity failures.
    - [Insight Report](../_archive/insights/2026-02-19_MA_Penny_Migration.md)
- **[2026-02-13] Solvency & Asset Liquidation Discounting**
    - Established the principle of conservative valuation for solvency checks. Inventory and illiquid assets should be valued at a "liquidation discount" (e.g., 50%) to prevent over-leveraging and systemic collapse.
    - [Insight Report](../_archive/insights/2026-02-13_Solvency_Aggregation_Challenges.md)
- **[2026-02-13] M2 Integrity in God Mode**
    - Defined strict rules for "God Mode" injections. `INJECT_MONEY` must use the Central Bank as the counter-party (minting) and is subject to an immediate `audit_total_m2` check. The Central Bank's holdings are explicitly excluded from the M2 calculation to ensure correct fractional reserve modeling.
    - [Insight Report](../_archive/insights/2026-02-13_GodCommand_Protocol_M2_Audit.md)
- **[2026-02-14] Zero-Sum Bank Runs**
    - Validated that `FORCE_WITHDRAW_ALL` events must strictly follow a two-step process: 1) Liability Reduction (Deposit write-down), 2) Asset Transfer (Cash payout). This prevents "Magic Money" creation where agent cash increases without a corresponding bank liability decrease.
    - [Insight Report](../_archive/insights/2026-02-14_Macro_Shock_Stress_Test.md)

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
