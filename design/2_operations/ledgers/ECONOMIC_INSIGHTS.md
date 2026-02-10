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
- **[2026-02-10] Protocol-Driven Architecture & Test Resilience**
    - **Insight**: 컴포넌트 내부 구현(private state, hasattr)에 의존하는 테스트는 리팩토링 시 비효율적인 연쇄 파열을 유발함. 이는 계약이 지켜지지 않는 시장의 부실함과 같음.
    - **Principle**: **"구현이 아닌 계약(Contract)을 테스트하라."** `typing.Protocol`과 엄격한 Mock Spec(`MagicMock(spec=...)`)을 사용하여 아키텍처 경계를 강화하면, 구현 변경 시에도 테스트는 안정적으로 유지됨.
    - [Insight Report](../_archive/insights/fix-residual-test-errors.md)
- **[2026-02-10] DTOs as the Universal Medium of Exchange**
    - **Insight**: 파편화된 데이터 구조는 모듈 간 소통 오류를 만들고 방어적 로직을 강요함. DTO는 시스템 내에서 정보가 흐르는 "통화"이며, 이 통화가 단일화될 때 거래 비용(버그)이 최소화됨.
    - **Principle**: **"DTO는 시스템의 기축 통화이다."** 표준화된 DTO(`AgentCoreConfigDTO`, `CanonicalOrderDTO`)를 인터페이스 표준으로 사용하여 모듈 간 결합을 제거하고 시스템적 확장성을 확보함.
    - [Insight Report](../_archive/insights/fix-test-systems.md)
- **[2026-02-11] Mock/Protocol Drift & DTO Purity**
    - **Insight**: Test suites are highly vulnerable to architectural refactoring. The primary cause is "Mock Drift," where test doubles (`MagicMock`) diverge from production code contracts (`Protocols`, DTOs). This leads to three main failure classes: (1) Protocol Violation (outdated signatures), (2) DTO Impurity (returning mocks instead of primitives), and (3) Encapsulation Violation (direct state access).
    - **Principle**: Tests must treat architectural protocols and data contracts as first-class citizens. Mocks must be strictly configured (`spec=...`), return primitives to ensure DTO purity, and interact with objects via their public interfaces.
    - [Insight Report](../_archive/insights/2026-02-11_Mock_Drift_Root_Cause_Analysis.md)
- **[2026-02-11] Test Scoping and Pattern Enforcement**
    - **Insight**: Test failures can arise from incorrect mocking scope (patching definition vs consumption) or bypassing established instantiation patterns (direct constructor calls).
    - **Principle**: Enforce the use of established Factories (e.g., `create_household`) in tests to ensure correct dependency injection. Mocks and patches must be applied with careful attention to module import paths.
    - [Insight Report](../_archive/insights/2026-02-11_Final_Test_Failures_And_Patch_Scoping.md)

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
- **[2026-02-11] Multi-Currency Representation in Tests**
    - **Insight**: A architectural shift from representing financial balances as a simple `float` to a `Dict[CurrencyCode, float]` caused widespread test failures. Tests, especially those using mocks, continued to assert against or provide float values.
    - **Principle**: All financial state, including in tests and mocks, must strictly adhere to the multi-currency dictionary format (e.g., `{DEFAULT_CURRENCY: 100.0}`).
    - [Insight Report](../_archive/insights/2026-02-11_Multi-Currency_Test_Awareness.md)

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
- **[2026-02-11] Aligning Test Data with Domain Logic**
    - **Insight**: Agent logic can fail if test data violates domain constraints (e.g., death probability > 1.0). Newborn agents were being created with random adult ages because `initial_age` was not explicitly passed in tests.
    - **Principle**: Test configurations and mock data must accurately reflect the domain constraints and data types expected by the system under test.
    - [Insight Report](../_archive/insights/2026-02-11_Legacy_Test_Refactor_Summary.md)
