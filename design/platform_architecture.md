# Platform Architecture & Design Patterns

## 3. Core Architectural Patterns

### 3.1 Data-Driven Purity (DTOs for Decisions)

- **Phenomenon**: Decision logic (Decision Engines) directly accessing mutable `Market` or `Government` objects, leading to side effects and unpredictable behavior.
- **Principle**: All decision logic must rely on immutable data snapshots (`DTOs`, e.g., `MarketSnapshotDTO`) captured at a specific point in time. Direct injection of live state objects like `Market` is forbidden.
- **Benefits**:
    - **Purity**: Decision functions produce no side effects and are deterministic for the same input.
    - **Testability**: Unit tests can easily constructed by synthesizing DTOs.
    - **Debugging**: Logging the `MarketSnapshotDTO` allows exact reproduction of decision logic.

### 3.2 Two-Phase State Transition (Plan & Finalize)

- **Phenomenon**: Complex logic mixing state reading, decision making, and state mutation in a single function (e.g., deciding consumption and immediately deducting inventory).
- **Principle**: Separate complex state transitions into **Plan** and **Finalize** phases.
    1.  **Phase 1 (Plan)**: Generate Intents or Transactions based on current state. No state mutation allowed.
    2.  **Phase 2 (Finalize/Process)**: Execute generated Transactions/Intents in a batch to update state.
- **Benefits**:
    - **Atomicity**: State updates happen atomically after all decisions are made.
    - **Visibility**: The list of generated transactions provides a clear audit trail of what will happen.

### 3.3 Financial Calculation Integrity (Zero-Sum Distribution)

- **Phenomenon**: Asset leakage or creation due to floating-point precision errors when distributing funds (e.g., Inheritance).
- **Principle**: When distributing assets to N recipients:
    - Distribute `floor(total / N)` to N-1 recipients.
    - Distribute `total - (N-1) * distributed_amount` to the last recipient.
- **Effect**: Guarantees strict Zero-Sum conservation of assets within the system.
