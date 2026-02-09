# Economic Insights Ledger: The Knowledge Base

> **"Knowledge survives, artifacts perish."**
> This ledger is the permanent repository for systemic, behavioral, and monetary wisdom derived from the simulation.

---

## 🏛️ [System] Architecture & Infrastructure
*Systemic rules, protocol purity, and structural patterns.*

- **[2026-02-09] Household Agent Decomposition (TD-260)**
    - Refactored the monolithic `Household` "God Object" into a modular Orchestrator-Engine architecture. Replaced fragile Mixin inheritance with stateless, pure Engines (Lifecycle, Needs, Budget, etc.) and explicit DTO-based communication.
    - [Insight Report](../_archive/insights/2026-02-09_Household_Decomposition.md)
- **[2026-02-09] Government Orchestrator Refactor (TD-259)**
    - Analysis of decomposition from monolith to Stateless Engines.
    - [Insight Report](../_archive/insights/TD-259_Government_Refactor.md)
- **[2026-02-09] Interface Purity Enforcement (Sensory)**
    - Transitioning agents to strict DTO-based sensory input to prevent state leakage.
    - [Insight Report](../_archive/insights/PH9.2_TrackB_SensoryPurity.md)
- **[2026-02-09] Command & Order Purity**
    - Handling regression and contract mismatches during structural refactors.
    - [Insight Report](../_archive/insights/bundle_purity_regression.md)
- **[2026-01-25] R&D Investment and Endogenous Innovation**
    - Transition from time-based to probabilistic unlock models driven by firm activity.
- **[2026-01-20] Data Contract Mismatch (AttributeError)**
    - Lessons on TypedDict vs Object access patterns in API layers.

---

## 💰 [Monetary] Circulation & Integrity
*M2 integrity, zero-sum principles, and financial market logic.*

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

---

## 🧠 [Behavior] Agent Logic & Animal Spirits
*Economic psychology, survival instincts, and population dynamics.*

- **[2026-01-25] Grace Protocol for Agent Solvency**
    - Distinguishing Liquidity from Solvency through Fire Sale mechanisms.
- **[2026-01-15] Population Dynamics & Birth Rate (r/K Selection)**
    - Analysis of expectation mismatch and childcare time constraints on population.
