# Current Design Directory Structure

## Root Files
- INDEX.md
- QUICKSTART.md
- TECHNICAL_DEBT.md
- TECH_DEBT_LEDGER.md
- platform_architecture.md
- project_status.md
- project_structure.md

## Folders
- protocols/ (Contains PROTOCOL_*.md)
- ledgers/ (Contains SESSION_LEDGER.md, RELIABILITY_LEDGER.md, INBOUND_REPORTS.md)
- manuals/ (Contains worker manuals like spec_writer.md, git_reviewer.md...)
- handovers/ (Contains HANDOVER_*.md)
- work_orders/ (Contains WO-*.md)
- specs/ (Contains SPEC-*.md)
- drafts/
- gemini_output/
- audits/
- REPORTS/ (Contains verification logs)

## Goal
- Consolidate strictly.
- Root should only have Entry points (INDEX, QUICKSTART).
- Everything else in folders.
- Delete temp files.
- Link structure: Entry -> Layer 1 (Protocols/Status) -> Layer 2 (Manuals/Ledgers) -> Layer 3 (Specs/Details).
