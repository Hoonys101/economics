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
- **[2026-02-09] Role-Specific Interface Naming (Interface Purity)**
    - When an object plays multiple roles (e.g., `Bank` as agent and service provider), method names must be specific to the role (`get_customer_balance`) to avoid ambiguity with generic names (`get_balance`) and prevent interface collisions.
    - [Insight Report](../_archive/insights/2026-02-09_Role_Specific_Interface_Naming.md)
- **[2026-02-09] Adapter Pattern for Legacy DTOs**
    - The Adapter pattern is an effective strategy for migrating legacy data structures (e.g., `StockOrder`) to a canonical format (`CanonicalOrderDTO`) by providing a translation layer. This allows for gradual, system-wide refactoring without halting development.
    - [Insight Report](../_archive/insights/2026-02-09_Adapter_Pattern_for_Legacy_DTOs.md)
- **[2026-02-09] Protocol Purity and Mock Spec Enforcement**
    - When testing components that adhere to strict protocols, `unittest.mock.MagicMock` must be created with the `spec` argument (e.g., `MagicMock(spec=IProtocol)`). This ensures the mock itself conforms to the interface, preventing tests from masking protocol violations.
    - [Insight Report](../_archive/insights/2026-02-09_Protocol_Purity_and_Mock_Specs.md)
- **[2026-02-09] DTO Contract Stability and Regression Testing**
    - Data Transfer Objects (DTOs) act as a strict contract between system components. Any change to a DTO is a breaking change that requires auditing all consumers. Automated smoke/integration tests are critical for detecting regressions caused by such contract violations.
    - [Insight Report](../_archive/insights/2026-02-09_DTO_Contract_Stability.md)
- **[2026-02-09] Cockpit's Direct State Injection (Divine Intervention)**
    - Implementation of a real-time policy control layer. Identified the need for "Divine Intervention" event types to avoid side-effect isolation and state inconsistencies.
    - [Insight Report](../_archive/insights/2026-02-09_Cockpit_Direct_State_Intervention.md)
- **[2026-02-09] Tick-Level State Reset Best Practices**
    - **Problem**: Tick-level state variables (e.g., `expenses_this_tick`) were being reset mid-lifecycle, causing data loss for later-stage processes like learning and analysis.
    - **Principle**: All agent tick-level state resets must occur uniformly at the end of the simulation cycle (e.g., a "Post-Sequence" phase). This ensures that all phases within the tick have access to a consistent, complete dataset.
    - **Implementation**: Enforce a standardized `reset()` method on agents, to be called exclusively by the orchestrator during the final phase.
    - [Insight Report](../_archive/insights/2026-02-09_System_Tick_Level_State_Reset_Best_Practices.md)
- **[2026-02-09] Protocol Composition for Contextual Interfaces**
    - **Problem**: A component (e.g., `HousingTransactionHandler`) required agents to satisfy multiple distinct capabilities (owning property, having a financial balance, earning a wage), leading to complex and fragile `isinstance` or `hasattr` checks.
    - **Principle**: Instead of creating a single, monolithic "God Interface," combine multiple small, role-based protocols (e.g., `IPropertyOwner`, `IFinancialAgent`) into a new, context-specific protocol (e.g., `IHousingTransactionParticipant`).
    - **Implementation**: The new composite protocol is used for a single `isinstance` check, guaranteeing the object fulfills all required contracts for that specific interaction.
    - [Insight Report](../_archive/insights/2026-02-09_System_Protocol_Composition_Pattern.md)
- **[2026-02-09] API Contract Preservation During Internal Refactoring**
    - **Problem**: Refactoring an agent's internal state management (e.g., moving data into internal DTOs) by removing properties and methods from the main class caused cascading system-wide `AttributeError` failures.
    - **Principle**: An object's public API is a contract that must be maintained even when its internal implementation changes. Abruptly removing or changing the API breaks consumers.
    - **Implementation**: When refactoring internals, preserve the public API by implementing proxy properties and methods on the main class that delegate calls to the new internal structures. This allows consumers to migrate to a new API gradually.
    - [Insight Report](../_archive/insights/2026-02-09_System_API_Contract_Preservation.md)
- **[2026-01-25] R&D Investment and Endogenous Innovation**
    - Transition from time-based to probabilistic unlock models driven by firm activity.
- **[2026-02-10] Decoupled Decision Engines via DTOs**
    - **Principle**: An agent's decision-making logic (the "how") should be decoupled from its state (the "what"). Stateless "Engines" (e.g., `SurvivalEngine`, `ProductionEngine`) should operate on input Data Transfer Objects (DTOs) and return output DTOs, without directly modifying the agent's internal state.
    - **Implementation**: The agent Orchestrator is responsible for preparing the input DTOs, invoking the appropriate Engine, and then integrating the resulting output DTO back into its state. This promotes testability, modularity, and prevents spaghetti-like dependencies.      
    - [Insight Report](../_archive/insights/2026-02-10_Ecosystem_Health_and_Agent_Decisions.md)
- **[2026-01-20] Data Contract Mismatch (AttributeError)**
    - Lessons on TypedDict vs Object access patterns in API layers.
- **[2026-02-10] Tick-Level State Reset Integrity**
    - **Principle**: To ensure data availability for all simulation phases (e.g., learning, analysis), agent state variables relevant for an entire tick (`expenses_this_tick`) must only be reset at the very end of the simulation cycle (i.e., in the Post-Sequence phase). Resetting state mid-cycle leads to data loss for later-stage processes.
    - **Implementation**: Enforce a standardized `reset()` method on agents, to be called exclusively by the orchestrator during the final phase of a tick.
    - [Insight Report](../_archive/insights/2026-02-10_Tick_Level_State_Reset_Integrity.md)

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
- **[2026-02-09] Structural Integrity: Seizure Waterfall & Finance Commands (PH10.3)**
    - Implementation of hierarchical asset recovery (Cash->Stock->Inventory) and stateless Finance system command pattern.
    - [Insight Report](../_archive/insights/2026-02-09_PH10.3_Structural_Integrity.md)
- **[2026-02-09] Protocol Purification: IConfigurable (TD-LIQ-INV)**
    - Decoupling configuration access from agent internals via formal protocols and DTOs.
    - [Insight Report](../_archive/insights/2026-02-09_TD-LIQ-INV_Protocol_Purification.md)

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
