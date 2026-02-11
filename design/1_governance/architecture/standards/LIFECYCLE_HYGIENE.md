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
- **Severity: Medium**: Resetting state counters too early, leading to blind spots in analytics.
- **Severity: High**: "Ghost Agents" remaining in the Registry after death.
