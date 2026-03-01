# MISSION_spec: Infrastructure & Persistence Reliability (Wave 4)

**Target Phase**: Wave 4 - Infrastructure & Persistence Reliability
**Status**: DRAFT / SPECIFYING
**Priority**: HIGH (Data Preservation)

## 1. Context & Objectives
The **Project Watchtower Audit** highlighted the risk of data loss during long simulation runs due to the lack of a robust checkpointing mechanism in the `PersistenceManager`. Additionally, the **Lifecycle Suture** between birth/death events and the persistence layer is susceptible to race conditions.

### Goals:
1. **Zero Data Loss**: Implement periodic buffer flushes and checkpoints.
2. **Atomic Recovery**: Ensure simulation can recover from the last checkpoint without state-drift.

---

## 2. Proposed Changes

### 2.1. [NEW] Checkpoint Suture
Implement periodic state snapshots in `PersistenceManager`.

- **File**: `simulation/systems/persistence_manager.py`
- **Logic**:
  - Add `checkpoint_state(tick)` method.
  - Flush all pending SQLite transactions.
  - Snapshot the `GlobalRegistry` (JSON or separate DB table).
  - Track `last_safe_tick` in the database.

### 2.2. [HARDEN] Lifecycle Manager Audit
Hardened the interaction between the `LifecycleManager` and the Persistence layer.

- **File**: `simulation/systems/lifecycle_manager.py`
- **Logic**:
  - Guarantee that `AGENT_BIRTH` events are flushed before the next consumption phase.
  - Ensure `AGENT_DEATH` events purge agent data from the active cache *only after* successful persistence.

---

## 3. Verification Plan

### 3.1. Automated Tests
- **Test Checkpoint Recovery**: 
  - Run simulation for 20 ticks.
  - Trigger a manual `PersistenceManager.checkpoint_state(20)`.
  - Simulate a crash (exit process).
  - Restart and verify `last_safe_tick == 20` and all balances are restored.

### 3.2. Evidence Requirements
- Log entry showing `PERSISTENCE | Checkpoint saved at Tick 50`.
- SQL query result showing correctly persisted agent counts post-recovery.
