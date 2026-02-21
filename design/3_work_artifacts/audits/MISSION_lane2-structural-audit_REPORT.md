# Lane 2 Structural Audit: Lifecycle & Sagas (Mission: lane2-structural-audit)

## Executive Summary
This audit identifies a critical ordering bug in the firm creation sequence where capital transfers are attempted before agent registration. It also reveals a structural mismatch in Housing Saga participant identification across the DTO layer. These combined issues cause systemic transaction failures and contribute to the observed M2 money supply inversion (negative balance).

## Detailed Analysis

### 1. Firm Startup Race Condition
- **Status**: ❌ Missing (Critical Logic Error)
- **Component**: `simulation\systems\firm_management.py`
- **Root Cause**: In `spawn_firm()`, the `settlement_system.transfer()` call occurs at **L148**, but the firm is only registered in the global `simulation.agents` directory at **L157**.
- **Impact**: The `SettlementSystem` (and underlying banking engines) cannot resolve the firm's ID during the transfer because it is not yet present in the registry.
- **Evidence**: `reports\diagnostic_refined.md` logs: `Engine Error: Destination account does not exist: 124` followed by `STARTUP_FAILED`.

### 2. Saga DTO Participant Mismatch
- **Status**: ⚠️ Partial (Inconsistent Interface)
- **Component**: `modules\finance\sagas\orchestrator.py`
- **Root Cause**: Structural desync in ID accessors within `HousingTransactionSagaStateDTO`.
    - **Buyer Context**: Uses `HouseholdSnapshotDTO` which requires resolution via `.household_id`.
    - **Seller Context**: Uses `HousingSagaAgentContext` which requires resolution via `.id`.
- **Evidence**: `reports\diagnostic_refined.md`: `SAGA_SKIP | Saga ... missing participant IDs.`
- **Notes**: The orchestrator's fallback logic for dict-based sagas (`L65-83`) is failing to normalize these keys before the liveness check at `L93`.

### 3. Atomic Registration Sequence (Proposal)
- **Status**: 💡 Proposed Architecture
- **Logic**: To prevent "Ghost Firm" errors, registration must be decoupled from matching activation.
- **Proposed Spawning Sequence**:
    1. **Instantiate**: Create the agent object (Firm/Household).
    2. **Registry Injection**: `simulation.register_agent(agent)` -> Atomic update to `WorldState.agents` and banking ledgers.
    3. **Financial Funding**: Execute `settlement_system.transfer()` for startup capital.
    4. **Sim List Entry**: Append to `simulation.firms` to allow the agent to begin matching/production.

## [Architectural Insights]
- **Lifecycle Fragmentation**: Spawning logic is manually managed in `FirmSystem`, creating a high risk of ordering dependencies. A centralized `AgentFactory` or `Simulation.onboard_agent()` protocol is required.
- **DTO Desync**: The discrepancy between `household_id` and `id` across different context DTOs indicates a need for a unified `IAgentIDProvider` protocol.

## [Regression Analysis]
- **Symptom**: Massive `SETTLEMENT_FAIL` clusters during firm expansion phases.
- **Consequence**: Newly spawned firms start with zero capital, leading to immediate "Zombie" warnings (Tick 18) and fire-sale inventory dumping (Tick 20-24).
- **M2 Ripple**: Failed credits during startup capital transfers contribute to the `TD-ECON-M2-INV` (Negative Money Supply) identified in the ledger.

## [Test Evidence]
```text
- ERROR | Transaction Record: ID=105ae9a4-..., Status=FAILED, Message=Destination account does not exist: 124
- WARNING | STARTUP_FAILED | Failed to transfer capital from 101 to new firm 124. Aborting.
- WARNING | SAGA_SKIP | Saga 6db0783b-ed13-4095-a78e-2fefa2b2165c missing participant IDs.
- WARNING | MONEY_SUPPLY_CHECK | Current: -47712322.00, Expected: 50505570.00
```

## Risk Assessment
- **Economic Instability**: The high failure rate of startups prevents the simulation from reaching its target firm density, leading to labor market collapse.
- **Data Integrity**: Stalled sagas (due to `SAGA_SKIP`) leave properties permanently "under contract," effectively locking the housing market.

## Conclusion
The system requires a strict **Registration-before-Injection** mandate for all new agents. Normalizing the Saga DTO participant fields is essential to stop the leakage of financial transactions and property locks.