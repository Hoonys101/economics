# Insight Report: Phase 1 - Market Infrastructure & Signals

**ID**: `SPEC_ANIMAL_PHASE1_MARKET`
**Date**: 2026-05-22
**Author**: Jules (AI Agent)
**Status**: **ACTIVE** (Breaking Changes Introduced)

## 1. Context
This report documents the architectural shift and technical debt introduced during Phase 1 of the 'Animal Spirits' initiative. The goal was to establish clean, reliable market signals by introducing a `MarketSignalObserver` and redefining the `MarketSnapshotDTO`.

## 2. Technical Debt Introduced (Intentional)

### 2.1. Breaking Change: `MarketSnapshotDTO`
- **What**: The `MarketSnapshotDTO` has been converted from a `@dataclass` (containing `prices`, `volumes`, etc.) to a `TypedDict` (containing `market_signals` and legacy `market_data`).
- **Impact**: This change **invalidates all existing agent decision engines** that rely on the old `MarketSnapshotDTO` structure (e.g., `agent.make_decision(market_snapshot=...)`).
- **Remediation**: All agent decision logic must be updated to parse the new `market_signals` structure. This is scheduled for subsequent implementation phases.

### 2.2. Golden Fixture Invalidation
- **What**: The relaxation of the circuit breaker mechanism (`get_dynamic_price_bounds` returning infinite bounds for sparse history) alters the fundamental price discovery dynamics at the start of the simulation.
- **Impact**: **All existing economic outcome tests and golden fixtures are invalid.** They rely on the previous, stricter circuit breaker logic.
- **Remediation**: A dedicated task must be created to perform a full review and regeneration of all golden fixtures using `scripts/fixture_harvester.py` after the full feature set is implemented.

## 3. Architectural Insights

### 3.1. System-Level Observation
- The introduction of `MarketSignalObserver` (DTOs implemented) represents a shift towards a "System Observer" pattern.
- **Lesson**: Isolating signal calculation prevents circular dependencies and ensures data purity for agents. Agents now consume pre-calculated signals rather than raw market state.

### 3.2. Configuration Dependency
- `OrderBookMarket` now relies on `config_module.CIRCUIT_BREAKER_MIN_HISTORY`.
- **Insight**: This dependency on the global config module within the market entity suggests a need for stricter configuration injection or a dedicated `MarketConfigDTO` to avoid tight coupling with the monolithic config.

## 4. Verification Status
- **DTO Definitions**: Verified via static analysis.
- **Market Logic**: Verified via unit tests (`tests/unit/markets/test_circuit_breaker_relaxation.py`).
- **Simulation Integrity**: **BROKEN** (Known State). The simulation will not run until Phase 2 updates the agents.
