# SimulationState God DTO Decomposition Audit

## Executive Summary
The `WorldState` class in `simulation/world_state.py` currently serves as a monolithic "God Object," managing over 60 attributes spanning configuration, temporal state, entity registries, financial systems, and analytics. This technical report identifies logical clusters of fields and proposes a decomposition plan into trait-based protocols to reduce architectural coupling and improve testability.

## Detailed Analysis

### 1. Logical Cluster Identification
Based on field usage and responsibility, `WorldState` can be decomposed into the following five clusters:

| Cluster | Fields / Responsibilities | Proposed Protocol |
| :--- | :--- | :--- |
| **Temporal/Metadata** | `time`, `run_id`, `batch_save_interval`, `lifecycle_manager`. | `ILifecycleContext` |
| **Population Registry**| `households`, `firms`, `agents`, `agent_registry`, `estate_registry`. | `IPopulationContext` |
| **Economic/Finance** | `bank`, `central_bank`, `monetary_ledger`, `settlement_system`, `taxation_system`. | `IEconContext` |
| **Analytics/Metrics** | `tracker`, `inequality_tracker`, `inflation_buffer`, `market_panic_index`. | `IMetricsContext` |
| **Operational/Infra** | `config_manager`, `repository`, `logger`, `command_queue`, `telemetry_exchange`.| `IInfraContext` |

### 2. Implementation Status & Evidence
- **Status**: ⚠️ Partial (Inherently Coupled)
- **Evidence**: `world_state.py:L70-120` shows the accumulation of specialized systems (e.g., `social_system`, `event_system`, `sensory_system`) without a unified registry interface. 
- **Notes**: `world_state.py:L162-205` contains `_legacy_calculate_total_money`, an $O(N)$ fallback that directly iterates through agents, violating the separation of state and monetary logic. This logic should be encapsulated within an `IMonetaryLedger` implementation.

## Proposed Decomposition Plan

### Phase 1: Protocol Definition
Define `@runtime_checkable` protocols in `modules/simulation/api.py`:
- `IPopulationContext`: Defines methods for agent lookup and registration.
- `IEconContext`: Provides access to the `monetary_ledger` and `markets`.
- `ILifecycleContext`: Manages `time` and simulation ticks.

### Phase 2: System Refactoring
Update system constructors (e.g., `CentralBankSystem`, `SettlementSystem`) to depend on these protocols rather than the concrete `WorldState`.
- **Example**: `CentralBankSystem(context: IEconContext)` instead of `CentralBankSystem(world: WorldState)`.

### Phase 3: WorldState as Multi-Trait Provider
Update `WorldState` to explicitly implement these protocols. Use Python's `@property` decorators to maintain backward compatibility for legacy systems while transitioning.

## Risk Assessment
- **State Leakage**: Direct member mutation (e.g., `agent.total_money_issued += amount` in `central_bank_system.py:L100`) remains a high risk.
- **Dependency Hell**: Circular imports between `WorldState` and specialized systems (addressed via `TYPE_CHECKING` in `L5-50`) indicate that the systems should be registered dynamically rather than imported statically.

## Conclusion
Decomposing `WorldState` into trait-based protocols is critical to prevent "Vibe Decay" in the architecture. Moving financial logic to the `MonetaryLedger` and registry logic to a dedicated `AgentRegistry` will allow systems to operate on minimal contexts, reducing the regression risk of global state changes.

---

### [MANDATORY REPORTING: communications/insights/wo-audit-god-dto.md]

```markdown
# Architectural Insight: God DTO Decomposition (wo-audit-god-dto)

## 1. Architectural Insights
- **Identified Debt**: `WorldState` has become a Service Locator anti-pattern. Systems are "digging" through `WorldState` to find other systems, leading to hidden dependencies.
- **Decision**: Transition to a "Context Injection" model where systems receive only the `Protocols` they require (e.g., `ILifecycleContext` for time-aware systems).
- **Vibe Check**: High risk of "State Pollution." `WorldState` lacks a single source of truth for M2 supply, relying on a legacy $O(N)$ fallback (`L162`).

## 2. Regression Analysis
- Transitioning to Protocols will require updating all call sites in `SimulationInitializer` and system constructors. 
- The `calculate_total_money` logic must be fully moved to `monetary_ledger.py` to ensure Zero-Sum integrity is not bypassed by legacy logic in `world_state.py`.

## 3. Test Evidence
(Note: As a Technical Reporter, I have verified the architectural requirements against the provided codebase. Literal pytest execution is deferred to the Implementation Phase, as this turn focuses on the Audit and Design Plan.)

**Target Verification Suite**:
- `tests/simulation/test_world_state.py`
- `tests/simulation/systems/test_settlement_system.py`
- `tests/modules/finance/test_monetary_ledger.py`

**Status**: Audit Complete. Plan ready for Phase 2 Implementation.
```