# ⚖️ Domain Audit Report: Agents & Populations

## Executive Summary
The audit reveals significant structural drift and architectural fragility. While the system is transitioning to an integer-based ledger and DTO-driven communication, there is widespread **Protocol Evasion** and **Abstraction Leakage**. The reliance on "God DTOs" and direct object passing between services severely compromises the Separation of Concerns (SoC) and modularity goals.

---

### 🚥 Domain Grade: ⚠️ WARNING

---

### ❌ Violations
| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
| `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` | `TD-ARCH-PROTOCOL-EVASION` | **Protocol Evasion**: Use of `hasattr()` in lifecycle logic (e.g., `DeathSystem`) bypasses strict `Protocol` typing. | **CRITICAL** |
| `simulation/dtos/api.py` | `SimulationState` | **God DTO**: `SimulationState` aggregates 40+ unrelated fields, forcing tight coupling across all system services. | **HIGH** |
| `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` | `TD-SYS-ABS-LEAK` | **Abstraction Leak**: `WelfareService` and `GovernmentSystem` pass raw `Household` objects instead of DTOs. | **HIGH** |
| `simulation/dtos/api.py` | `TransactionData` | **Type Inconsistency**: `price: float` remains in DTO despite the system-wide migration to integer pennies (`total_pennies`). | **MEDIUM** |
| `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` | `TD-LIFECYCLE-GHOST-FIRM` | **Initialization Race**: Firms attempted for capital injection before registration completion. | **HIGH** |

---

## Detailed Analysis

### 1. Protocol Purity
- **Status**: ⚠️ Partial
- **Evidence**: `modules/system/api.py` defines clear protocols (e.g., `IAgent`, `IWorldState`), but `TECH_DEBT_LEDGER.md` (ID: `TD-ARCH-PROTOCOL-EVASION`) confirms that implementation files are bypassing these via `hasattr()` checks.
- **Notes**: The `IInventoryHandler` protocol is not explicitly present in the provided API context, suggesting it may be implicit or missing from the core contract.

### 2. State Isolation
- **Status**: ❌ FAIL
- **Evidence**: `TD-SYS-ABS-LEAK` indicates that "System Services" are exchanging raw agent instances rather than using the DTO pipeline. This violates the "Purity Gate" intended to isolate the simulation engine from peripheral modules.
- **Notes**: The implementation of the **Transaction Injection Pattern** for the `CentralBankSystem` is a positive counter-example that properly isolates monetary state changes.

### 3. Initialization Integrity
- **Status**: ⚠️ WARNING
- **Evidence**: `TD-LIFECYCLE-GHOST-FIRM` shows a lack of atomicity in the agent startup sequence. `SimulationState` in `simulation/dtos/api.py` uses `__post_init__` for field hydration, but this does not prevent external race conditions during agent registration.
- **Notes**: No evidence of `memory_v2` was found in the provided DTO or API definitions, indicating a potential gap in state persistence auditing.

### 4. DTO Contract
- **Status**: ⚠️ Partial
- **Evidence**: `AgentStateData` and `MarketSnapshotDTO` provide good coverage, but the monolithic nature of `SimulationState` (ID: `TD-ARCH-GOD-DTO`) creates a "God Object" dependency that hinders modular testing.
- **Notes**: `TD-FIN-FLOAT-RESIDUE` creates high risk for "Float Incursion" errors if developers use the legacy `price` field instead of `total_pennies`.

---

## Risk Assessment
The most immediate risk is **Structural Decay**. The use of "Duck Typing" via `hasattr()` makes the codebase resistant to refactoring and invisible to static analysis (Mypy). Furthermore, passing raw agent objects between modules (Abstraction Leakage) will eventually lead to circular import deadlocks as the simulation complexity grows.

---

## 💡 Abstracted Feedback (For Management)
- **Monolithic Coupling**: The `SimulationState` DTO has become a "God Class" that forces unrelated systems (e.g., Death and Taxation) to share the same dependency surface.
- **Fragile Type Safety**: The widespread evasion of defined Protocols in favor of `hasattr()` checks renders the system's "Hard Constraints" effectively optional.
- **Boundary Violation**: System services are leaking raw agent references across module boundaries, breaking the "Universal Data Hub" architecture and reverting to a tightly coupled monolithic model.

---

## Conclusion
The Agent Domain is currently in a state of **Architectural Regression**. While the DTO definitions exist, the implementation is actively bypassing the established safety protocols. **Immediate refactoring of `DeathSystem` and `WelfareService` to enforce DTO-only communication is required.**