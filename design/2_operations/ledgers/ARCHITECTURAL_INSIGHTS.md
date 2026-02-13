# Architectural Insights Ledger: The Engineering Handbook

> **"Code represents the model; Structure ensures its survival."**
> This ledger documents the software engineering patterns, testing strategies, and structural decisions that underpin the simulation engine.

---

## 🏗️ [Patterns] Structural Design & Refactoring

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
- **[2026-02-13] Stateless Engine vs Stateful Service (Tax Refactor)**
    - Refactored `TaxService` (God Object) into a pure `TaxEngine`. Enforced separation between calculation (pure) and collection (side-effecting orchestrator). Pushed state preparation to DTOs.
    - [Insight Report](../_archive/insights/2026-02-13_Stateless_Tax_Engine_Refactor.md)
- **[2026-02-13] The Sovereign Slot (Phase 0 Intercept)**
    - Established 'Phase 0' in the `TickOrchestrator` to process external God-mode commands *before* the simulation's causal chain (Phase 1 Perception) begins. This protects causality and ensures all agents perceive a consistent "Divine Intervention" state within the same tick.
    - [Insight Report](../../communications/insights/mission-found-03.md)
- **[2026-02-13] Global Registry & Origin Priority (SSoT)**
    - Implemented a priority-based registry system (SYSTEM < CONFIG < GOD_MODE) to manage simulation parameters. Used `__getattr__` on the `config` module to proxy attributes to the registry, ensuring that all consumers fetch the most recent, potentially hot-swapped values.
    - [Insight Report](../../communications/insights/mission-found-01.md)
- **[2026-02-13] Explicit Financial Settlement for Government Bonds**
    - Transitioned government bond issuance from an internal state mutation in `FinanceSystem` to an explicit `SettlementSystem.transfer` orchestrated by the `Government` agent. This enforces zero-sum integrity and ensures that Quantitative Easing (QE) or standard bond purchases are explicitly audited and debited against actual account balances.
    - [Insight Report](../../communications/insights/mission-found-02.md)
- **[2026-02-13] Atomic Intervention with Mandatory Rollback (DATA-01)**
    - Implemented `CommandService` with an `UndoStack` to manage 'God Mode' interventions. Every command batch (SET_PARAM, INJECT_ASSET) follows a strict Validation -> Snapshot -> Execute -> Audit cycle. Any failure at the Audit step (Monetary Integrity) triggers a full batch reversal, ensuring the simulation never enters an invalid state from external actions.
    - [Insight Report](../../communications/insights/mission-data-01.md)
- **[2026-02-13] On-Demand Path Resolution & Pre-Validation (DATA-02)**
    - Developed `TelemetryCollector` using dot-notation path resolution (e.g., `economy.m2`). Introduced a 'Subscription Purity' principle where paths are validated at registration time to reduce runtime overhead and handle missing data points gracefully via error flags in the DTO instead of crashing the engine.
    - [Insight Report](../../communications/insights/mission-data-02.md)
- **[2026-02-13] Strategy-Based Scenario Verification (DATA-03)**
    - Adopted the Strategy pattern (`IScenarioJudge`) for real-time verification of economic hypotheses. This decouples the core simulation engine from complex social judging criteria, allowing for extensible "Scenario Cards" that can be evaluated in Phase 8 without side effects on agent logic.
    - [Insight Report](../../communications/insights/mission-data-03.md)
- **[2026-02-13] Lazy Dependency Resolution Pattern**
    - Implemented lazy initialization in `DemographicManager` to resolve internal factories from the simulation context if not explicitly injected. Prevents silent failures while maintaining flexible testing.
    - [Insight Report](../_archive/insights/2026-02-13_Lazy_Dependency_Resolution_Demographics.md)
- **[2026-02-10] Decoupled Decision Engines via DTOs**
    - **Principle**: An agent's decision-making logic (the "how") should be decoupled from its state (the "what"). Stateless "Engines" (e.g., `SurvivalEngine`, `ProductionEngine`) should operate on input Data Transfer Objects (DTOs) and return output DTOs, without directly modifying the agent's internal state.
    - **Implementation**: The agent Orchestrator is responsible for preparing the input DTOs, invoking the appropriate Engine, and then integrating the resulting output DTO back into its state. This promotes testability, modularity, and prevents spaghetti-like dependencies.      
    - [Insight Report](../_archive/insights/2026-02-10_Ecosystem_Health_and_Agent_Decisions.md)
- **[2026-01-20] Data Contract Mismatch (AttributeError)**
    - Lessons on TypedDict vs Object access patterns in API layers.
- **[2026-02-10] DTOs as the Universal Medium of Exchange**
    - **Insight**: 파편화된 데이터 구조는 모듈 간 소통 오류를 만들고 방어적 로직을 강요함. DTO는 시스템 내에서 정보가 흐르는 "통화"이며, 이 통화가 단일화될 때 거래 비용(버그)이 최소화됨.
    - **Principle**: **"DTO는 시스템의 기축 통화이다."** 표준화된 DTO(`AgentCoreConfigDTO`, `CanonicalOrderDTO`)를 인터페이스 표준으로 사용하여 모듈 간 결합을 제거하고 시스템적 확장성을 확보함.
    - [Insight Report](../_archive/insights/fix-test-systems.md)

---

## 🧪 [Testing] Quality Assurance & Stability

- **[2026-02-09] Protocol Purity and Mock Spec Enforcement**
    - When testing components that adhere to strict protocols, `unittest.mock.MagicMock` must be created with the `spec` argument (e.g., `MagicMock(spec=IProtocol)`). This ensures the mock itself conforms to the interface, preventing tests from masking protocol violations.
    - [Insight Report](../_archive/insights/2026-02-09_Protocol_Purity_and_Mock_Specs.md)
- **[2026-02-09] DTO Contract Stability and Regression Testing**
    - Data Transfer Objects (DTOs) act as a strict contract between system components. Any change to a DTO is a breaking change that requires auditing all consumers. Automated smoke/integration tests are critical for detecting regressions caused by such contract violations.
    - [Insight Report](../_archive/insights/2026-02-09_DTO_Contract_Stability.md)
- **[2026-02-10] Protocol-Driven Architecture & Test Resilience**
    - **Insight**: 컴포넌트 내부 구현(private state, hasattr)에 의존하는 테스트는 리팩토링 시 비효율적인 연쇄 파열을 유발함. 이는 계약이 지켜지지 않는 시장의 부실함과 같음.
    - **Principle**: **"구현이 아닌 계약(Contract)을 테스트하라."** `typing.Protocol`과 엄격한 Mock Spec(`MagicMock(spec=...)`)을 사용하여 아키텍처 경계를 강화하면, 구현 변경 시에도 테스트는 안정적으로 유지됨.
    - [Insight Report](../_archive/insights/fix-residual-test-errors.md)
- **[2026-02-11] Mock/Protocol Drift & DTO Purity**
    - **Insight**: Test suites are highly vulnerable to architectural refactoring. The primary cause is "Mock Drift," where test doubles (`MagicMock`) diverge from production code contracts (`Protocols`, DTOs). This leads to three main failure classes: (1) Protocol Violation (outdated signatures), (2) DTO Impurity (returning mocks instead of primitives), and (3) Encapsulation Violation (direct state access).
    - **Principle**: Tests must treat architectural protocols and data contracts as first-class citizens. Mocks must be strictly configured (`spec=...`), return primitives to ensure DTO purity, and interact with objects via their public interfaces.
    - [Insight Report](../_archive/insights/2026-02-11_Mock_Drift_Root_Cause_Analysis.md)
- **[2026-02-11] Test Scoping and Pattern Enforcement**
    - **Insight**: Test failures can arise from incorrect mocking scope (patching definition vs consumption) or bypassing established instantiation patterns (direct constructor calls).
    - **Principle**: Enforce the use of established Factories (e.g., `create_household`) in tests to ensure correct dependency injection. Mocks and patches must be applied with careful attention to module import paths.
    - [Insight Report](../_archive/insights/2026-02-11_Final_Test_Failures_And_Patch_Scoping.md)
- **[2026-02-11] Multi-Currency Representation in Tests**
    - **Insight**: A architectural shift from representing financial balances as a simple `float` to a `Dict[CurrencyCode, float]` caused widespread test failures. Tests, especially those using mocks, continued to assert against or provide float values.
    - **Principle**: All financial state, including in tests and mocks, must strictly adhere to the multi-currency dictionary format (e.g., `{DEFAULT_CURRENCY: 100.0}`).
    - [Insight Report](../_archive/insights/2026-02-11_Multi-Currency_Test_Awareness.md)
- **[2026-02-11] Aligning Test Data with Domain Logic**
    - **Insight**: Agent logic can fail if test data violates domain constraints (e.g., death probability > 1.0). Newborn agents were being created with random adult ages because `initial_age` was not explicitly passed in tests.
    - **Principle**: Test configurations and mock data must accurately reflect the domain constraints and data types expected by the system under test.
    - [Insight Report](../_archive/insights/2026-02-11_Legacy_Test_Refactor_Summary.md)

---

## ⚡ [Performance] Optimization & Efficiency

- **[2026-02-09] Tick-Level State Reset Best Practices**
    - **Problem**: Tick-level state variables (e.g., `expenses_this_tick`) were being reset mid-lifecycle, causing data loss for later-stage processes like learning and analysis.
    - **Principle**: All agent tick-level state resets must occur uniformly at the end of the simulation cycle (e.g., a "Post-Sequence" phase). This ensures that all phases within the tick have access to a consistent, complete dataset.
    - **Implementation**: Enforce a standardized `reset()` method on agents, to be called exclusively by the orchestrator during the final phase.
    - [Insight Report](../_archive/insights/2026-02-09_System_Tick_Level_State_Reset_Best_Practices.md)
- **[2026-02-10] Tick-Level State Reset Integrity**
    - **Principle**: To ensure data availability for all simulation phases (e.g., learning, analysis), agent state variables relevant for an entire tick (`expenses_this_tick`) must only be reset at the very end of the simulation cycle (i.e., in the Post-Sequence phase). Resetting state mid-cycle leads to data loss for later-stage processes.
    - **Implementation**: Enforce a standardized `reset()` method on agents, to be called exclusively by the orchestrator during the final phase of a tick.
- **[2026-02-13] Iterator Efficiency in Transaction Streams**
    - Migrated high-volume transaction combinations from list concatenation to `itertools.chain`. Achieved ~40% reduction in execution time and eliminated intermediate memory allocations.
    - [Insight Report](../_archive/insights/2026-02-13_Transaction_List_Optimization.md)
