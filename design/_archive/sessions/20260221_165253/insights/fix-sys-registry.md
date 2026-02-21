# Fix System Agent Registration & Standardize IDs

## Architectural Insights
1.  **Standardized System IDs**: Moved away from mixed string/int IDs (`"government"` vs `0`). All system agents (Central Bank, Government, Bank, Escrow, Public Manager) now have reserved integer IDs in the range 0-99 defined in `modules/system/constants.py`.
    *   `ID_CENTRAL_BANK = 0`
    *   `ID_GOVERNMENT = 1`
    *   `ID_BANK = 2`
    *   `ID_ESCROW = 3`
    *   `ID_PUBLIC_MANAGER = 4`
    *   `ID_SYSTEM = 5`
2.  **Unified Registration**: Updated `SimulationInitializer` to explicitly register ALL system agents in `sim.agents` (the Single Source of Truth). This eliminates the need for `AgentRegistry` to have hardcoded fallback logic for finding "government" or "bank".
3.  **Registry Purity**: Refactored `AgentRegistry` to simply look up agents in `state.agents`. This decouples the registry from knowledge of specific agent roles.
4.  **Initialization Order**: Fixed a critical bug where `AgentRegistry` state was initialized AFTER the `Bootstrapper` ran. `Bootstrapper` relies on `SettlementSystem`, which relies on `AgentRegistry`. Moved state initialization to immediately after `Simulation` creation.
5.  **Technical Debt Resolution**: Addressed `TD-ARCH-DI-SETTLE` by removing hardcoded string dependencies in `SettlementSystem` and `TransactionProcessor`, enforcing a clean Dependency Injection pattern via `AgentRegistry` and standardized Integer IDs.

## Peripheral Impact Analysis
*   **Analytics & Dashboard**: A global search of `modules/analytics/`, `dashboard/`, and `modules/system/telemetry.py` confirmed no lingering dependencies on the literal strings `"GOVERNMENT"`, `"CENTRAL_BANK"`, or `"BANK"`. The system now relies purely on the agent objects resolved via the registry.
*   **Persistence**: Database schema verification confirmed that `agent_states` and `transactions` tables use `INTEGER` for agent IDs, ensuring seamless compatibility with the new integer constants. `verify_persistence.py` demonstrated successful save/load operations for system agents.

## Economic Integrity Verification
*   **M2 Integrity**: A 50-tick simulation (`verify_m2_integrity.py`) confirmed that the M2 calculation logic remains functional with the new IDs. The system correctly tracked money supply changes (driven by credit creation/spending), validating that the `SettlementSystem` and `TransactionProcessor` are correctly routing funds to/from the integer-ID system agents.

## Regression Analysis
*   **Legacy String IDs**: Several tests and components used `id="government"`. These were updated to use `ID_GOVERNMENT` (1).
    *   `tests/unit/finance/test_finance_system_refactor.py`
    *   `tests/unit/modules/finance/test_system.py`
    *   `tests/unit/systems/handlers/test_housing_handler.py`
*   **Public Manager ID**: `PublicManager` had a hardcoded ID `999999`. Updated to `ID_PUBLIC_MANAGER` (4). Updated corresponding compliance tests.
*   **Test Environment**: `tests/system/test_engine.py` had outdated assumptions about agent presence (missing CentralBank/PublicManager in assertion). Updated `test_simulation_initialization` to reflect the new standardized registration.

## Test Evidence
`verify_sys_registry.py` output:
```
Verifying System Agent Registration...
sim.agents keys: [2, 1, 0, 3, 4]
All System Agents present in sim.agents.
All System Agents have correct types.
Financial Agent IDs: [2, 1, 0, 3, 4]
AgentRegistry verification passed.
SUCCESS: System Agent Registration Verified.
```

Unit Tests Passed:
*   `pytest tests/unit/finance/test_finance_system_refactor.py`
*   `pytest tests/unit/modules/finance/test_system.py`
*   `pytest tests/unit/systems/handlers/test_housing_handler.py`
*   `pytest tests/unit/modules/system/execution/test_public_manager.py`
*   `pytest tests/unit/modules/system/execution/test_public_manager_compliance.py`

Persistence Verification (`verify_persistence.py`):
```
Loaded rows: [(1, 'government'), (0, 'central_bank')]
Transaction rows: [(0, 1)]
SUCCESS: Persistence Verification Passed.
```
