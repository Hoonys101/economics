# Technical Report: Agent Lifecycle & Transaction Routing Atomicity Audit

## Executive Summary
The audit reveals critical gaps in atomic routing during agent startup, leading to "Ghost Destination" failures. While `TransactionProcessor` has a graceful failure mechanism for missing agents, the `FirmSystem` attempts financial initialization before registration, and no mechanism exists to scrub stale IDs from system-level queues after liquidation.

## Detailed Analysis

### 1. Firm Startup: Registration vs. Initialization
- **Status**: ❌ Missing (Out of Sequence)
- **Evidence**: `simulation/systems/firm_management.py:L148-160`
- **Notes**: The `spawn_firm` method executes `settlement_system.transfer` (L148) to provide startup capital *before* the firm is added to `simulation.agents` (L160). This results in the "Destination account does not exist" error observed in `runtime_audit.log:L1345`.
- **Recommendation**: Registration in `simulation.agents` and the `AgentRegistry` must occur before any financial transfers are attempted.

### 2. Stale ID Cleaning: `inter_tick_queue` & `effects_queue`
- **Status**: ❌ Missing
- **Evidence**: `simulation/systems/lifecycle_manager.py:L88-115`
- **Notes**: `AgentLifecycleManager` processes deaths and liquidations but lacks logic to filter `state.inter_tick_queue` or `state.effects_queue`. If an agent is liquidated, pending transactions or effects involving their ID remain in these queues, potentially causing logic errors in subsequent ticks.
- **Recommendation**: Implement a `ScrubbingPhase` in `AgentLifecycleManager` that filters all queues in `SimulationState` against the `inactive_agents` map.

### 3. Graceful Failure in `TransactionProcessor`
- **Status**: ✅ Implemented
- **Evidence**: `simulation/systems/transaction_processor.py:L204-216`
- **Notes**: The "Agent Existential Guard" successfully catches `None` buyers or sellers, logs an error, and returns a failed `SettlementResultDTO` instead of raising an unhandled exception. 
- **Caveat**: While it prevents crashes, it does not prevent "Money Leaks" if the transaction was intended to be atomic with other state changes.

## Risk Assessment
- **Critical Risk (Type Mismatch)**: `runtime_audit.log:L1585` shows a `TypeError` in `settlement_system.py` because M&A logic in `ma_manager.py` passed a `float` instead of an `int` for pennies. This violates the "Float Core" hardening mandate (TD-CRIT-FLOAT-CORE).
- **High Risk (Ghost IDs)**: Persistent failed transactions due to stale IDs in `inter_tick_queue` will bloat state size and pollute economic indicators over long runs.

## Conclusion
The current lifecycle management is not atomic. The "Registration-after-Transfer" bug in `FirmSystem` is the root cause of startup failures. Additionally, the system lacks a "Dead-Letter" or scrubbing mechanism for transactions involving liquidated agents. Immediate refactoring of the `spawn_firm` sequence and addition of a queue-scrubbing utility are required to maintain simulation integrity.