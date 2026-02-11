# ⚖️ Architectural Standards Index

Welcome to the central repository of architectural rules and coding patterns for the Economics simulation. These standards ensure the integrity, testability, and scalability of our "Living Digital Economy".

---

## 🏛️ 1. Design Patterns
- **[SEO_PATTERN.md](./SEO_PATTERN.md)**: Stateless Engine & Orchestrator. The foundational logic/state separation.
- **[FINANCIAL_INTEGRITY.md](./FINANCIAL_INTEGRITY.md)**: The Penny Standard, Double-Entry rules, and Zero-Sum enforcement.

## 🔌 2. Infrastructure & Lifecycle
- **[LIFECYCLE_HYGIENE.md](./LIFECYCLE_HYGIENE.md)**: Tick sequencing, Late-Reset principle, and state transition safety.
- **[TESTING_STABILITY.md](./TESTING_STABILITY.md)**: Mock Purity, Golden Fixtures, and library-less environment stability.

---

## 🚀 How to use these Standards
1. **In Specs**: Reference the specific standard file (e.g., "Must follow [SEO_PATTERN.md]") in the design principles section.
2. **In Reviews**: Use these files as criteria for checking `Hard-Fail` violations.
3. **In Audits**: Map violations back to the specific standard IDs defined in these documents.
# 💰 Domain Standard: Financial Integrity

## 🔍 Context
High-fidelity economic simulations require 100% precision. Floating-point errors and "ghost money" are systemic risks.

---

## 🛡️ Hard Rules

### 1. The Penny Standard
- **Integer Currency**: All internal financial representations MUST be **Integers (Pennies)**.
- **Boundary Conversion**: Floats from Config or UI MUST be converted to pennies *immediately* upon entry into the simulation core.
- **Scaling**: All monetary amounts are scaled by `100x` relative to their dollar value.

### 2. Double-Entry Enforcement
- **Residual Clearing**: No transaction can be one-sided. Every debit MUST have a corresponding credit.
- **Unattributed Funds**: Money destroyed (e.g., fees) or created (e.g., QE) MUST be registered as transfers to/from specific system accounts (e.g., `EscheatmentFund`, `CentralBank.Cash`).

### 3. Settlement SSoT (Single Source of Truth)
- **No Direct Mutation**: Agents, Engines, and other modules MUST NOT directly change `agent.cash` or equivalent wallet balances. This is a critical violation.
- **Mandatory System Call**: All monetary transfers MUST be executed by emitting a `SettlementOrder` or calling the `SettlementSystem` to execute the move.
- **Atomicity Pre-Check**: Business logic (Engines, Sagas) MUST verify all business rules (inventory availability, buyer eligibility) *before* the monetary leg is triggered via the `SettlementSystem`.

---

## 🚨 Violations
- **Severity: Critical**: Any "Money Leak" found in `trace_leak.py`.
- **Severity: Critical**: Any module other than `SettlementSystem` directly mutating an agent's cash balance.
- **Severity: High**: Use of `float` types in core financial engines.
# ⏱️ Infrastructure Standard: Lifecycle Hygiene

## 🔍 Context
Deterministic outcomes rely on strict sequencing of events within a simulation tick.

---

## 🛡️ Hard Rules

### 1. The Late-Reset Principle
- **Counter Persistence**: "Tick-Level" metrics (e.g., `revenue_this_tick`, `expenses_this_tick`) MUST persist through all active simulation phases (transaction generation, learning, etc.) until the end of the tick.
- **Designated Reset Phase**: Resetting of tick-level counters MUST only occur in a designated final phase, such as `Post-Sequence` or `EndOfTick`.
- **Anti-Pattern (Forbidden)**: Resetting counters inside the `generate_transactions` phase or any mid-tick agent logic is a CRITICAL violation. This leads to data loss for analytics, logging, and learning systems operating in later phases of the same tick.

### 2. Birth/Death Atomicity
- **Registry Sync**: When an agent is born or dies, the `AgentRepository`, `SettlementSystem`, and `DemographicManager` MUST be updated atomically within the same transaction or sequence.
- **Inheritance Cleanup**: Dying agents MUST have their assets completely liquidated or transferred via `InheritanceManager` before the object is purged to prevent monetary leaks.

---

## 🚨 Violations
- **Severity: High**: Resetting state counters too early, leading to blind spots in analytics and incorrect agent learning.
- **Severity: Critical**: "Ghost Agents" remaining in the Registry after death, or asset leaks from incomplete death procedures.
# 🧪 Testing Standard: Integrity & Stability

## 🔍 Context
Test failures in isolated/lean environments often stem from brittle mocks and library dependencies that drift from production code.

---

## 🛡️ Hard Rules

### 1. Mock Purity (Preventing MagicMock Poisoning)
- **Primitive Injection is Mandatory**: When mocking objects or their sub-states (e.g., `agent.social_state`), you MUST configure the mock to return primitive values (int, float, bool, str) for any attributes that will be accessed. By default, a `MagicMock` returns another `MagicMock`, which is not serializable.
  - **WRONG (CRITICAL VIOLATION)**: `h = MagicMock()` -> `h.social_state.conformity` returns another `MagicMock`. This will crash any system that creates a DTO from this agent.
  - **RIGHT**: `h.social_state.conformity = 0.5`.
- **Serialization Check**: Any mock that will be passed into a `get_state_dto()` call, logged, or persisted MUST be configured to respond with serializable types for all accessed attributes.

### 2. Golden Fixture Priority
- **Prefer Real State**: Test logic MUST prefer loading a "Golden Sample" (a serialized snapshot of a real agent state) over manual `MagicMock` construction for complex objects like `Firm` or `Household`. Manual mocks are brittle and cause "Test Mock Drift" as production code evolves.
- **Standard Fixtures**: Use the pre-defined fixtures `golden_households`, `golden_firms`, and `golden_ledger` from `conftest.py` whenever possible.
- **Mock Factories**: If a custom mock is unavoidable, it should be generated via a dedicated Factory function that ensures all necessary attributes and DTO-related fields are populated with correct primitive types.

### 3. External Dependency Faking
- **Fake Objects, Not Mocks**: For complex external libraries like `numpy` or `yaml`, use specialized "Fake" classes (e.g., `FakeNumpy`) that implement the minimal required interface with primitive return values, rather than patching with `MagicMock`.

---

## 🚨 Violations
- **Severity: Critical**: Tests failing with `TypeError: Object of type 'MagicMock' is not JSON serializable`. This indicates a fundamental violation of Mock Purity.
- **Severity: High**: Over-reliance on manual `MagicMock` construction instead of Golden Fixtures, leading to tests that pass but fail to catch real logic drift between Agents and DTOs.
