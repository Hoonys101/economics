# 🏗️ Pattern Standard: SEO (Stateless Engine & Orchestrator)

## 🔍 Context
To ensure logical purity and testability, we strictly decouple business logic (Engines) from persistent state management (Agents).

---

## 🛡️ Hard Rules

### 1. Engine Purity
- **No `self` mutation**: Engines MUST NOT have instance variables (`self.xxx`) that represent business state.
- **No Agent Handles**: Engines MUST NOT receive Agent instances (`self`) as parameters.
- **DTO Input/Output**: Engines operate exclusively on DTOs.
  - **GOOD**: `def execute(state: MyStateDTO) -> MyStateUpdateDTO`
  - **BAD**: `def execute(agent: Household)`

### 2. Orchestrator Duty
- **State SSoT**: Only the Orchestrator (`Agent` or `System`) is allowed to update persistent state.
- **Side-Effect Management**: The Orchestrator receives the Engine's results and performs transactions (via `SettlementSystem`) or updates internal `_econ_state`.

### 3. Engine Isolation
- **Domain Focus**: Engines MUST be specialized (e.g., `ProductionEngine`, `ConsumptionEngine`).
- **Dependency Flow**: Engines MAY call other utility engines but MUST NOT create circular dependencies between domains.

---

## 🚨 Violations
- **Severity: High**: If an engine is found mutating a passed DTO directly instead of returning a copy or update DTO.
- **Severity: Critical**: If an engine is found accessing private agent state via bypasses.
