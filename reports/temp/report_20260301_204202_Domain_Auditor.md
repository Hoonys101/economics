# ⚖️ Domain Auditor Report: Systems, Persistence & LifeCycles

## Executive Summary
The simulation infrastructure is currently in a state of **Structural Transition**. While critical financial integrity issues like "Ghost Money" and "Float Incursions" have been resolved, the core lifecycle and state management layers suffer from high coupling (God DTO) and race conditions during agent initialization. The persistence layer lacks a robust checkpointing mechanism, posing a risk of data loss upon system failure.

---

## Detailed Analysis

### 1. Lifecycle Suture
- **Status**: ⚠️ **Partial**
- **Evidence**: `TECH_DEBT_LEDGER.md:TD-LIFECYCLE-GHOST-FIRM` and `TD-ARCH-ORPHAN-SAGA`.
- **Notes**: There is a verified race condition where capital injection (Settlement) is attempted before agent registration is complete. Additionally, `SimulationState` (`simulation/dtos/api.py:L316`) manages `currency_holders` as an optional list, but the ledger resolution is currently "duck-typed" (`TD-SYS-IMPLICIT-REGISTRY-LOOKUP`), which creates a fragile link between the lifecycle of an agent and its financial visibility.

### 2. Persistence Purity
- **Status**: ✅ **Implemented (Interface Level)** / ❌ **Missing (Mechanism Level)**
- **Evidence**: `simulation/dtos/api.py:L70` (`AgentStateData`) and `TECH_DEBT_LEDGER.md:TD-REBIRTH-BUFFER-LOSS`.
- **Notes**: The DTOs for persistence are well-defined and strictly typed (e.g., `assets` hardened to `int` in `AgentStateData`). However, the `PersistenceManager` (implied by ledger notes) lacks a periodic flush/checkpointing strategy, meaning a crash results in a total loss of unbuffered ticks.

### 3. Tick Orchestration
- **Status**: ⚠️ **Structural Drift**
- **Evidence**: `simulation/dtos/api.py:L316` (`SimulationState`) and `TECH_DEBT_LEDGER.md:TD-ARCH-GOD-DTO`.
- **Notes**: The `SimulationState` has evolved into a "God DTO" with 40+ fields, violating the Interface Segregation Principle. This creates a monolithic dependency where any system (Birth, Death, or Market) must depend on the entire engine state, leading to "Structural Rigidity."

### 4. Resource Management
- **Status**: ⚠️ **Warning**
- **Evidence**: `TECH_DEBT_LEDGER.md:TD-REBIRTH-BUFFER-LOSS`.
- **Notes**: The primary resource risk is data volatility. While `IDatabaseMigrator` (`modules/system/api.py:L334`) ensures schema health, the lack of atomic buffer flushes remains the most significant infrastructure threat.

---

### 🚥 Domain Grade: **WARNING**

### ❌ Violations
| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
| `simulation/dtos/api.py` | L316-410 | **TD-ARCH-GOD-DTO**: Monolithic `SimulationState` violating Interface Segregation. | **High** |
| `TECH_DEBT_LEDGER.md` | TD-LIFECYCLE-GHOST-FIRM | **Race Condition**: Capital injection occurs before Agent registration is finalized. | **High** |
| `TECH_DEBT_LEDGER.md` | TD-ARCH-PROTOCOL-EVASION | **Protocol Evasion**: Widespread use of `hasattr()` instead of strict Protocol checks. | **Medium** |
| `modules/system/api.py` | L268 | **Type Weakness**: `IAgentRegistry.register` uses `Any` instead of `IAgent`. | **Low** |

### 💡 Abstracted Feedback (For Management)
1. **Segregate the "God DTO"**: The `SimulationState` must be decomposed into domain-specific contexts (e.g., `ILifecycleContext`, `IMonetaryContext`) to prevent a single change from breaking all decoupled systems.
2. **Enforce Atomic Birth**: Implement a `FirmFactory` or similar pattern to ensure that "Registration -> Account Opening -> Capitalization" is a single atomic transaction to prevent "Ghost Firms."
3. **Implement Persistence Checkpointing**: Transition from a single end-of-run save to a periodic checkpointing mechanism to mitigate the risk identified in `TD-REBIRTH-BUFFER-LOSS`.

## Conclusion
The simulation's plumbing is functional but **rigid and leaky at the edges**. The transition to integer-based math and injected transactions has stabilized the "Physics" of the world, but the "Biology" (Lifecycle) and "Memory" (Persistence) require immediate architectural decoupling to support long-term scaling.