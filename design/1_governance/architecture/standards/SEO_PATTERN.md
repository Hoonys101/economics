# 🏗️ Pattern Standard: SEO (Stateless Engine & Orchestrator)

## 🔍 Context
To ensure logical purity and testability, we strictly decouple business logic (Engines) from persistent state management (Agents).

---

## 🛡️ Hard Rules

### 1. Engine Purity
- **No `self` mutation**: Engines MUST NOT have instance variables (`self.xxx`) that represent business state.
- **No Agent Handles**: Engines MUST NOT receive Agent instances (`self`) as parameters.
- **Pure Read-Only Functions**: Engines MUST be read-only. They receive state and context, and return an **Intent/Decision DTO**.
- **DTO Input/Output**: Engines operate exclusively on DTOs.
  - **GOOD**: `def decide(state: MyStateDTO) -> MyIntentDTO`
  - **BAD**: `def execute(agent: Household)`

### 2. Orchestrator Duty
- **State SSoT**: Only the Orchestrator (`Agent` or `System`) is allowed to update persistent state.
- **Side-Effect Management**: The Orchestrator receives the Engine's results and performs transactions (via `SettlementSystem`) or updates internal `_econ_state`.

### 3. Engine Isolation
- **Domain Focus**: Engines MUST be specialized (e.g., `ProductionEngine`, `ConsumptionEngine`).
- **Dependency Flow**: Engines MAY call other utility engines but MUST NOT create circular dependencies between domains.

---

- **Severity: High**: If an engine is found mutating a passed DTO directly instead of returning a copy or update DTO.
- **Severity: Critical**: If an engine is found accessing private agent state via bypasses.

---

## 🔬 Simulation Readiness: Brain Scan Protocol

The SEO pattern is building specifically to enable **"Brain Scan"** simulations in Cockpit 2.0.

- **Requirement**: We must be able to clone an agent's current `StateDTO`, pass it to an Engine with hypothetical `ContextDTO` (e.g., "What if interest rates are 10%?"), and receive the agent's hypothetical `Intent` WITHOUT affecting the live agent's state or bank balance.
- **Sequence Split**:
    1. **Intent (Think)**: Engine calculates intent (Pure Function).
    2. **Mutation (Act)**: Orchestrator/Market executes state change.
    3. **Learning (Adapt)**: Post-sequence updates (Q-Table, history).
