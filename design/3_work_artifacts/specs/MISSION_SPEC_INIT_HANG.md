# Forensic Audit Mission: Initialization Hangs (WO-AUDIT-INIT-HANG)

## 1. Executive Summary
**Target**: `operation_forensics.py` and `test_scenario_runner.py`
**Symptom**: The simulation hangs infinitely (requiring `KeyboardInterrupt`) during Phase 4 (Population) Initialization, specifically when executing `sim.settlement_system.register_account(sim.bank.id, hh.id)`.
**Context**: Heavy log interleaving is observed just before the hang (`DemographicManager initialized` mixed with thread logs), and the traceback always ends inside `Simulation.__getattr__`.

## 2. Mission Objective
Conduct a deep code audit to identify the exact root cause of the initialization hang and propose a definitive fix. You *must* evaluate the 9 hypotheses listed below.

## 3. The 9 Hypotheses to Evaluate

1.  **Thread Deadlock (GIL/Logging / RLock)**: AI initializations (`AIDrivenHouseholdDecisionEngine`, `FirmAI`) might be using multi-threading/processing. A nested `logger.info` inside a thread could be deadlocking Python's `logging` internal `RLock` exactly when `register_account` is called.
2.  **Infinite Recursion on `__getattr__`**: `Simulation.__getattr__("bank")` fetches `world_state.bank`. If `WorldState.bank` is an uninitialized property that calls `sim.settlement_system`, it loops infinitely. Check if `sim.bank` resolution in `initializer.py` triggers this.
3.  **Massive Over-allocation / Memory Thrashing (OOM Hang)**: "GC Hang due to Mocks" was fixed in tests, but in a real run, instantiating 10,000s of agents with AI Engines might hit Swap Memory (disk thrashing), which looks like a hang where the program barely progresses but doesn't crash.
4.  **Database Lock Contest / SQLite Synchronous Wait**: `SimulationLogger` or `EventBus` might be trying to flush to SQLite from a different thread while the main thread is inside `register_account`. 
5.  **Mock Resolution Hang (Test Leak in Forensics)**: `operation_forensics.py` might inadvertently import a test utility or a mock that replaces the global `Bank` or `SettlementSystem`. Mocks with infinite depth (`MagicMock().id.something`) can cause hang-like slowdowns when evaluated in tight loops.
6.  **Stale Lock Wait Strategy**: The log shows `[WARNING] modules.platform.infrastructure.lock_manager: Stale lock detected...`. If the `lock_manager`'s `acquire()` method enters an infinite retry loop instead of returning successfully after clearing, it would swallow the thread.
7.  **Descriptor / Property Blocking**: If `Bank.id` or `Agent.id` is a `@property` that dynamically resolves using a heavy synchronous call (like an HTTP proxy or a massive DB query).
8.  **Test Setup Leak**: `test_scenario_runner.py` hangs at the exact same place as `operation_forensics.py`. This points to a systemic lifecycle bug introduced recently in `initializer.py` or `AccountRegistry`, independent of the runner.
9.  **EventBus Synchronous Hang**: `register_account` does `_bank_depositors[bank_id].add(agent_id)`. If `AccountRegistry` is observed by an `EventBus` that synchronously passes the event to a stalled listener, it will hang the main thread.

## 4. Auditor Instructions
1. Analyze `simulation/engine.py` (`Simulation.__getattr__`).
2. Analyze `simulation/initialization/initializer.py` (Focus on `_init_phase4_population` and `sim.bank.id` resolution).
3. Analyze `modules/finance/registry/account_registry.py`.
4. Identify which of the 9 hypotheses is the actual root cause (or if it's a 10th unknown cause).
5. Output a definitive `diagnostic_refined.md` report outlining the fix.
