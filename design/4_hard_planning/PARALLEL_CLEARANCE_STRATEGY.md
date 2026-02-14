# Parallel Technical Debt Clearance Strategy

**Mission Key**: `plan-parallel-debt-clearance`
**Date**: 2026-02-14
**Status**: DRAFT (Pending Review)

## 1. Executive Summary

This document outlines the strategy for resolving five critical technical debt items in parallel. The objective is to harden the system's security, enforcing strict typing (Purity), and reducing component coupling without halting ongoing development.

### Targeted Debt Items

1.  **TD-ARCH-SEC-GOD**: Security Risk (God Mode Auth).
2.  **TD-INT-PENNIES-FRAGILITY**: Logic Fragility (Penny-Float Duality).
3.  **TD-DATA-01-MOCK**: Test Drift (Settlement Protocol Mismatch).
4.  **TD-STR-GOD-DECOMP**: Maintainability (Agent God Classes).
5.  **TD-UI-DTO-PURITY**: Code Quality (UI DTO Serialization).

---

## 2. Architectural Standards & Constraints

-   **SEO Pattern**: strictly separate State (DTOs), Engines (Logic), and Orchestrators (Agents).
-   **Strict Typing**: All financial interactions must use `int` (pennies). Float usage in financial logic is deprecated.
-   **Interface Segregation**: Clients should depend on `Protocol` definitions (e.g., `ISettlementSystem`), not concrete implementations.
-   **Zero-Trust Networking**: All external commands (WebSocket) must be authenticated.

---

## 3. Detailed Resolution Specifications

### 3.1. [Group A] System Security & Networking
**Target**: `TD-ARCH-SEC-GOD` & `TD-UI-DTO-PURITY`

#### 3.1.1. God Mode Authentication (`TD-ARCH-SEC-GOD`)
*   **Component**: `modules/system/server.py`
*   **Requirement**:
    *   Implement header-based authentication: `X-GOD-MODE-TOKEN`.
    *   Bind `GodCommandDTO` processing to token validation.
*   **Implementation Plan**:
    1.  Inject `GOD_MODE_TOKEN` from `config/simulation.yaml` into `SimulationServer`.
    2.  In `_process_request` (handshake interceptor), validate the token using `secrets.compare_digest`.
    3.  Reject connections with `401 Unauthorized` if token is missing or invalid.

#### 3.1.2. UI Telemetry DTO Purity (`TD-UI-DTO-PURITY`)
*   **Component**: `modules/system/server_bridge.py`, `simulation/dtos/`
*   **Requirement**:
    *   Eliminate manual `dict` construction in telemetry broadcast.
    *   Ensure all data sent via WebSocket is serialized via Pydantic/Dataclass `asdict` or `model_dump`.
*   **Implementation Plan**:
    1.  Refactor `TelemetryExchange.push(snapshot)` to accept only `MarketSnapshotDTO` or `SimulationState` (typed objects).
    2.  Update `SimulationServer._send_snapshot` to handle Pydantic serialization natively using `model_dump(mode='json')`.
    3.  Audit `dashboard/services/telemetry_service.py` to ensure frontend receives consistent JSON structure.

---

### 3.2. [Group B] Core Finance & Protocol Hardening
**Target**: `TD-INT-PENNIES-FRAGILITY` & `TD-DATA-01-MOCK`

#### 3.2.1. Settlement Protocol Sync (`TD-DATA-01-MOCK`)
*   **Component**: `simulation/finance/api.py` (`ISettlementSystem`)
*   **Requirement**:
    *   Update `ISettlementSystem` protocol to include `audit_total_m2(expected_total: Optional[int] = None) -> bool`.
    *   Update all mocks in `tests/` to implement this method (or use `spec_set`).
*   **Implementation Plan**:
    1.  Modify `simulation/finance/api.py`: Add `audit_total_m2`.
    2.  Run `pytest` to identify broken mocks.
    3.  Update mocks to include `audit_total_m2`.

#### 3.2.2. Penny-Float Unification (`TD-INT-PENNIES-FRAGILITY`)
*   **Component**: `simulation/systems/settlement_system.py`, `modules/finance/api.py`
*   **Requirement**:
    *   Remove all `hasattr(agent, 'balance_pennies')` checks.
    *   Enforce `IFinancialEntity` (int-based) as the primary interface.
    *   Deprecate/Adapter support for legacy `IFinancialAgent` (float-based) only where strictly necessary, or migrate remaining agents.
*   **Implementation Plan**:
    1.  Ensure `IFinancialEntity` is the standard in `ISettlementSystem`.
    2.  Refactor `transfer`, `deposit`, `withdraw` in `SettlementSystem` to assume integer inputs.
    3.  **Critical**: Verify `Firm` and `Household` implement `IFinancialEntity` correctly (they appear to do so in context).

---

### 3.3. [Group C] Agent Architecture Decomposition
**Target**: `TD-STR-GOD-DECOMP`

#### 3.3.1. Firm/Household Logic Extraction
*   **Component**: `simulation/firms.py`, `simulation/core_agents.py`
*   **Requirement**:
    *   Reduce file size < 800 lines.
    *   Move remaining logic (e.g., specific decision handling, complex state updates) into helper services or existing engines.
*   **Implementation Plan (Firm)**:
    1.  Extract `liquidate_assets` logic fully into `AssetManagementEngine` (already largely done, ensure `Firm` is just a pass-through).
    2.  Move `generate_transactions` orchestration logic into a `FirmTransactionOrchestrator` helper if complex.
    3.  Ensure `Firm` acts purely as a router between `DecisionEngine`, `StatelessEngines`, and `StateDTOs`.
*   **Implementation Plan (Household)**:
    1.  Review `update_needs` and `make_decision`.
    2.  Ensure `Housing` logic (`_execute_housing_action`) is delegated to a `HousingConnector` or similar, rather than inline method.
    3.  Verify `Legacy Mixin Methods` are either removed or moved to a dedicated compatibility module.

---

## 4. Parallel Execution DAG (Direct Acyclic Graph)

To execute these tasks in parallel without merge conflicts, we assign them to distinct "lanes" based on file isolation.

| Lane | Focus Area | Debt Items | Key Files | Dependency |
| :--- | :--- | :--- | :--- | :--- |
| **Lane 1** | **System/Network** | `TD-ARCH-SEC-GOD`, `TD-UI-DTO-PURITY` | `modules/system/server.py`, `modules/system/server_bridge.py` | None |
| **Lane 2** | **Core Finance** | `TD-DATA-01-MOCK`, `TD-INT-PENNIES-FRAGILITY` | `simulation/finance/api.py`, `simulation/systems/settlement_system.py` | None (Interface change acts as contract) |
| **Lane 3** | **Agent Refactor** | `TD-STR-GOD-DECOMP` | `simulation/firms.py`, `simulation/core_agents.py` | Depends on Lane 2 Interface stability (loose) |

### Execution Strategy

1.  **Phase 1 (Setup)**:
    *   **Lane 2** updates `ISettlementSystem` definition (Protocol only) immediately. This unblocks mocks.
    *   **Lane 1** starts Server security updates.

2.  **Phase 2 (Implementation)**:
    *   **Lane 2** refactors `SettlementSystem` implementation (Penny unification).
    *   **Lane 3** starts Agent decomposition (treating `SettlementSystem` as black box interface).
    *   **Lane 1** completes DTO purity on Server.

3.  **Phase 3 (Integration)**:
    *   Merge Lane 2.
    *   Verify Agents (Lane 3) work with new Settlement logic.
    *   Verify UI (Lane 1) receives correct data.

---

## 5. Verification & Test Plan

### 5.1. Security Verification (Lane 1)
-   **Test**: `tests/system/test_server_auth.py` (New)
-   **Scenario**:
    1.  Connect via WS without header -> Expect 401.
    2.  Connect with invalid token -> Expect 401.
    3.  Connect with valid token -> Expect 200/101 Switching Protocols.

### 5.2. Financial Integrity Verification (Lane 2)
-   **Test**: `tests/simulation/systems/test_settlement_pennies.py`
-   **Scenario**:
    1.  Perform atomic transfer of `1` penny.
    2.  Verify `audit_total_m2` sums correctly.
    3.  Ensure no `AttributeError` regarding `hasattr` checks.
    4.  **Regression**: Run `tests/test_settlement_index.py`.

### 5.3. Agent Architecture Verification (Lane 3)
-   **Test**: `tests/simulation/agents/test_firm_decomposition.py`
-   **Scenario**:
    1.  Initialize `Firm`.
    2.  Run `make_decision` cycle.
    3.  Verify state transitions (Production -> Sales -> Finance).
    4.  Ensure no logic resides in `Firm` class (check cyclomatic complexity or manual inspection).

---

## 6. Pre-Implementation Risk Analysis

### Risk 1: Mock Hell (Lane 2)
*   **Description**: Changing `ISettlementSystem` will break every test that mocks it.
*   **Mitigation**: Create a `MockSettlementSystem` class in `tests/conftest.py` that implements the new interface and use it everywhere, rather than raw `MagicMock`.

### Risk 2: Serialization Overheads (Lane 1)
*   **Description**: `pydantic` serialization in `TD-UI-DTO-PURITY` might be slower than raw dicts, affecting 10Hz broadcast.
*   **Mitigation**: Use `model_dump(mode='json')` which is optimized in Pydantic V2. Benchmark if latency > 50ms.

### Risk 3: Agent State Persistence (Lane 3)
*   **Description**: Moving logic out of Agents might accidentally lose state if `get_current_state` / `load_state` are not updated to pull from the new engine/component locations.
*   **Mitigation**: Add a "Round-Trip" test: `Save State -> Load State -> Compare`.

---

## 7. Mandatory Reporting Instruction

**[INSTRUCTION FOR ASSIGNED AGENT]**
Upon completion of any task in this strategy, you MUST:
1.  Run the relevant verification tests.
2.  Create/Update the insight report at: `communications/insights/plan-parallel-debt-clearance.md`.
3.  Include:
    *   The specific Debt ID resolved.
    *   Verification Logs (Pytest output).
    *   Any deviations from this plan.