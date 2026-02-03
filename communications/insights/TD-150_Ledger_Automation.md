# TD-150 Ledger Automation Insights

## Overview
Implementation of `scripts/ledger_manager.py` to automate Ledger management (Archive, Sync, Register).

## Technical Decisions

### 1. Preserving Ledger Structure
The `TECH_DEBT_LEDGER.md` file contains semantic sections (e.g., "AGENTS & POPULATIONS", "FIRMS & CORPORATE") which provide architectural context. The proposed spec implied a potentially flatter structure or didn't explicitly address how to preserve these sections during read/write operations.
**Decision**: Implemented a Block-based parser (`TextBlock`, `TableBlock`) to preserve all content, including comments and section headers, exactly as is. The `LedgerItemDTO` was extended to include `section` context.

### 2. Handling Placeholder Rows
The ledger uses `(Empty)` rows to indicate empty sections. The initial parsing logic treated these as valid debt items with ID "(Empty)".
**Fix**: `sync` and `archive` logic was updated to explicitly ignore items with ID "(Empty)".

### 3. Test Isolation & Environment
During verification, `pytest` failed to load the global `tests/conftest.py` due to missing dependencies (`numpy`, `simulation` modules) in the sandbox environment.
**Workaround**: ran tests with `python -m pytest -c /dev/null tests/unit/test_ledger_manager.py` to isolate the unit tests from the global configuration.
**Insight**: This highlights a need for better separation between unit tests (which shouldn't require the full app environment) and integration tests.

## Findings from Initial Sync
Running `python scripts/ledger_manager.py sync` revealed:
- **Untracked Debt**: Several items in the ledger (e.g., TD-160, TD-183) do not have corresponding `TODO(TD-XXX)` markers in the codebase (or at least not found by the scanner).
- **Orphaned TODOs**: Found references to `TD-XXX` in the spec file itself, which is expected but verifies the scanner works.

## Future Improvements
- **Format Standardization**: Consider moving the ledger to a structured data format (YAML/JSON) and generating the Markdown as a view. This would eliminate parsing fragility.
- **Hook Integration**: The git hooks need to be installed manually or via a setup script.
