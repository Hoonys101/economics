# Gemini Worker Manual: Roadmap & TO-DO Manager

## 1. Objective
Synchronize the high-level vision (`future_roadmap.md`), technical debt (`TECH_DEBT_LEDGER.md`), and architectural drifts into a unified, actionable `design/TODO.md`.

## 2. Input Context
- **Primary source**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Secondary source**: `design/2_operations/manuals/future_roadmap.md`
- **Context**: `design/1_governance/architecture/ARCH_*.md` (Scanning for TODO comments)

## 3. Output Requirements
- **Target**: `design/TODO.md`
- **Formatting**:
    - Use Markdown checkboxes `[ ]`.
    - Group by **Economic Impact Cluster** (e.g., M2 Stability, Market Efficiency, AI Sophistication).
    - Annotate each item with its source (e.g., `(TD-035)`, `(ARCH-Seq)`).

## 4. Execution Logic
1.  **Scan for Active Debt**: Extract all "Active" or "Critical" items from the Tech Debt Ledger.
2.  **Scan for Roadmap Milestones**: Identify the "Next Step" or "Current Focus" from the roadmap.
3.  **Cross-Reference Architecture**: Look for unresolved drifts identified in recent audit reports or explicit `TODO` tags in architecture docs.
4.  **Cluster and Prioritize**:
    - High priority: Items affecting monetary integrity or engine stability.
    - Medium priority: Feature roadmap items.
    - Low priority: Long-term documentation or refactoring debt.
5.  **Write Results**: Overwrite or update `design/TODO.md` with the synchronized list.

## 5. Maintenance
This worker should be triggered before every new development sprint or after a major architectural audit.
