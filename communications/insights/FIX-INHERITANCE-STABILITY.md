# Fix Inheritance Manager and Restore Simulation Stability

## Phenomenon
During the 100-tick stress test (`scenarios/scenario_stress_100.py`), the simulation crashed with an `AttributeError: 'NoneType' object has no attribute 'get_balance'`. This occurred in `SettlementSystem.settle_atomic` -> `_execute_withdrawal`. Debugging revealed that the `agent` passed to `_execute_withdrawal` (specifically an `EscrowAgent` or similar system agent) had a `wallet` attribute that was `None`, causing the crash when `agent.wallet.get_balance` was called.

Additionally, a `TypeError` and `sqlite3.ProgrammingError` were observed related to multi-currency asset handling. `EscheatmentHandler` failed when `buyer.assets` returned a `defaultdict` (multi-currency) instead of a float during comparison. Similarly, `AgentRepository` failed to persist agent states because `assets` was a dictionary, which SQLite bindings could not handle directly.

## Root Cause
1.  **InheritanceManager API Mismatch:** The `AgentLifecycleManager` passed a `SimulationState` DTO to `InheritanceManager.process_death`, but `InheritanceManager` attempted to access `.world_state` on it, which does not exist on the DTO. This was a legacy artifact where `InheritanceManager` expected the full Engine object.
2.  **Unsafe Wallet Access:** `SettlementSystem` checked `hasattr(agent, 'wallet')` but did not check if `agent.wallet` was actually `None`. `EscrowAgent` (and potentially others) might declare the property but return `None` or be initialized without it in certain contexts.
3.  **Multi-Currency Incompatibility:** Recent updates to support multi-currency (Phase 33) changed `agent.assets` to return a dictionary (`Dict[CurrencyCode, float]`).
    *   `EscheatmentHandler` treated `assets` as a scalar float.
    *   `AgentRepository` attempted to save the raw dictionary to a SQLite `REAL` (float) column.

## Solution
1.  **Refactor InheritanceManager:** Updated `process_death` to accept `SimulationState` DTO and pass it directly to `TransactionProcessor`. Removed incorrect usage of `simulation.world_state`.
2.  **Defensive Wallet Check:** Updated `SettlementSystem._execute_withdrawal` to explicitly check `if hasattr(agent, 'wallet') and agent.wallet is not None`.
3.  **Multi-Currency Handling:**
    *   Updated `EscheatmentHandler` to detect if `buyer.assets` is a dictionary and extract `DEFAULT_CURRENCY` (defaulting to 0.0) before scalar comparison.
    *   Updated `AgentRepository.save_agent_state` and `save_agent_states_batch` to extract `DEFAULT_CURRENCY` from the `assets` dictionary before DB insertion, preserving schema compatibility.

## Lessons Learned
*   **DTO vs. Engine Confusion:** Explicit typing (`SimulationState` vs `Simulation`) is crucial in "God Class" decomposition. Legacy systems often assume they have access to the full engine (`world_state`), which violates the new decoupled architecture.
*   **Property Safety:** `hasattr` is insufficient for properties that might return `None`. Always check for existence *and* nullity for optional components.
*   **Migration Backward Compatibility:** When introducing complex types (like Multi-Currency dictionaries) into fields that were previously scalars (Assets), all consumers (DB, Logic, Handlers) must be audited. Implementing "smart extractors" that handle both types during the transition period is a robust strategy.
