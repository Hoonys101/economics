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
- **Float Incursion Guard**: Never pass `float` values to the `SettlementSystem`. Use explicit quantization: `amount = int(calculated_float_value)`. This prevents floating-point drift from contaminating the integer-based ledger.

---

## 🚨 Violations
- **Severity: Critical**: Any "Money Leak" found in `trace_leak.py`.
- **Severity: High**: Use of `float` types in core financial engines.
