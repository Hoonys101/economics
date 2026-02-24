# WO-WAVE-A-MODULE-DECOMPOSITION: Wave A Module Decomposition Log

## Wave A.2: 5-Phase Atomic Initialization Sequence

### Timeline Anomalies
*   **Environment Mismatch**: During verification of `tests/initialization/test_atomic_startup.py`, `typing_extensions` was reported as missing by pytest despite being installed in the environment. This was resolved by running pytest via `python -m pytest` to ensure the correct environment context.
*   **Initialization Dependency Fix**: The `AITrainingManager` (Phase 3) depended on `sim.households` which was not set until Phase 4. This was resolved by passing `self.households` directly to the manager. Additionally, Phase 4 was modified to use `sim.agents.update()` to preserve system agents added in Phase 2.

### Dependency Graph Updates
*   **Strict Layering**: `SimulationInitializer` now enforces a strict dependency layers:
    1.  **Infrastructure Layer**: `PlatformLockManager`, `GlobalRegistry`, `AgentRegistry`, `SettlementSystem`.
    2.  **Sovereign Layer**: `Government`, `Bank`, `CentralBank`, `PublicManager`.
    3.  **Market & Systems Layer**: `OrderBookMarket`, `LoanMarket`, `LaborMarket`, `TaxationSystem`, etc.
    4.  **Agent Layer**: `Household`, `Firm`.
*   **Cycle Resolution**: The `Government` <-> `FinanceSystem` <-> `Bank` circular dependency is now explicitly resolved in Phase 2 using property setter injection, removing constructor-level cycles.
*   **Agent Registry Merging**: System Agents (ID 0, 1, etc.) are explicitly re-merged into the `sim.agents` registry in Phase 4 via `.update()` to ensure they are discoverable by population agents during the Genesis phase (Phase 5).
