# 🛑 Vibe Review Manual: Reclaiming Control from LLMs

This manual defines the "Cognition-Correction" pipeline required to prevent **Vibe Coding**—the loss of architectural control due to over-reliance on LLM-generated code.

---

## 1. Defensive Auditing Patterns

### 🔴 Red Flags (Antipatterns)
- **Duct-Tape Debugging**: Repeatedly feeding error logs to the LLM without understanding the root cause, leading to bloated `try-except` blocks.
- **State Pollution**: Direct mutation of private members (e.g., `.cash`, `.inventory`) bypassing the `SettlementSystem` or `InventoryHandler`.
- **Hallucinated Logic**: Uncritical acceptance of $O(N^2)$ algorithm suggestions for large-scale backtesting.

### 🟢 Meta-Cognitive Checks
- **The Two-Sentence Test**: If you cannot explain exactly what a generated function does in two sentences, it is an **"Audit Target"**.
- **The Ping-Pong Limit**: If a bug isn't fixed after 3 prompt iterations, stop. The area is **"Contaminated"** and requires **[Step 2: Deconstruction]**.

---

## 2. The Cognition-Correction Pipeline

### Phase 1: Deconstruction (Logic Extraction)
Do not ask the LLM to "fix the code." Instead, ask:
*   *"Extract the step-by-step pseudocode for this logic and identify the invariant conditions."*
*   Verify if the logic violates **[SEO_PATTERN.md](./SEO_PATTERN.md)** (Statelessness) or **[FINANCIAL_INTEGRITY.md](./FINANCIAL_INTEGRITY.md)** (Zero-Sum).

### Phase 2: Isolation (Context Cleaning)
- **Dependency Severing**: Isolate the failing logic into a standalone script.
- **Mock Purity**: Ensure tests use real DTOs/Protocols instead of "Magic" mocks that mask failures.

### Phase 3: Restructuring (TDD Prompting)
- **Test-First**: Write the unit test *before* asking for the fix.
- **Explicit Constraints**: Always inject complexity requirements ($O(N)$) and side-effect bans (e.g., "Must NOT modify `GlobalRegistry` directly").

---

## 🚀 Application in Audits
Every **Watchtower Audit** should now flag high-vibe areas where explainability is low and state leakage is high. (Referenced in [INDEX.md](./INDEX.md)).
