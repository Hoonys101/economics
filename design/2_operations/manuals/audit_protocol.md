# 🦅 Archive: Project Watchtower Audit Protocol

## 1. Objective
Ensure project-wide consistency through a modular, bottom-up audit process that respects Separation of Concerns (SoC).

## 2. The Feedback Loop (The "Big Picture")
The audit process follows a recursive structure:
1.  **Modular Audit**: A specialized Gemini worker audits a specific module (e.g., `firms.py`) against its architectural specification (`ARCH_FIRMS.md`).
2.  **Abstraction**: The worker generates a concise "Domain Snapshot" (Successes, Drifts, New Debt).
3.  **Management Aggregation**: A central Auditor reads all "Domain Snapshots" to update the global `PROJECT_STATUS.md` and `future_roadmap.md`.

## 3. Module Context Matrix (SoC Principle)
Do NOT provide the entire codebase. Inject ONLY relevant files for each audit domain.

| Domain | Source Code (Reality) | Architecture (Rules) | Debt (Ledger) |
| :--- | :--- | :--- | :--- |
| **AGENTS** | `simulation/base_agent.py` | `ARCH_AGENTS.md` | Section 1 |
| **FINANCE** | `simulation/finance/` | `ARCH_FINANCE.md` | Section 5 |
| **MARKETS** | `simulation/interfaces/` | `ARCH_MARKETS.md` | Section 4 |
| **SYSTEMS** | `simulation/systems/` | `ARCH_TRANSACTIONS.md`| Section 5 |

## 4. Audit Execution Instructions

### Phase 1: Modular Integrity
- **Command**: `python scripts/gemini_worker.py context <instruction> --context <relevant_files>`
- **Checklist**:
    - Does the code bypass defined Protocols (e.g., `IInventoryHandler`)?
    - Are the DTOs immutable and correctly typed?
    - Does the logic leak internal state to other modules?

### Phase 2: High-Level Synchronization
- **Input**: Abstracted reports from Phase 1.
- **Output**: Update to `PROJECT_STATUS.md` and `HANDOVER.md`.
- **Goal**: Highlight discrepancies between the roadmap vision and the code-level reality.

## 5. Automation Strategy
- **Session-End**: Triggered via `checkpoint.py`.
- **Drift Detection**: If a Modular Audit fails (Grade: FAIL), the Management Auditor creates a critical entry in `TECH_DEBT_LEDGER.md`.
