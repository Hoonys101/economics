# Insight: TD-150 Ledger Automation

## Technical Debt & Observations

### 1. Fragile Markdown Parsing
The current implementation of `scripts/ledger_manager.py` relies on regex (`re`) and manual string manipulation to parse the Markdown table. This is fragile to format changes (e.g., missing pipes, different spacing).
*   **Insight**: A dedicated Markdown library or a switch to structured data (YAML/JSON) for the ledger source of truth would be more robust. The Markdown file could then be generated from that source.
*   **Mitigation**: Tests were added (`test_parser_resilience`) to cover common formatting issues.

### 2. Manual "RESOLVED DEBTS" Section
The `TECH_DEBT_LEDGER.md` contains a `RESOLVED DEBTS` section at the bottom which has a different schema (Status column missing, separate Resolution Date). The `archive` command moves resolved items from *active* sections to a separate archive file, but it ignores this legacy `RESOLVED DEBTS` section.
*   **Insight**: There is a split between "recently resolved" (in active tables) and "historically resolved" (in the bottom section or archive files). The automation standardizes on "Archive Files".
*   **Action**: Future cleanup might be needed to move the `RESOLVED DEBTS` section into an archive file to fully clean the ledger.

### 3. Placeholder Management
The ledger uses placeholders like `(No Active Items)` and `(Empty)` in the ID column. These require special handling in the parser and sync logic to avoid treating them as valid Debt IDs.
*   **Fix**: The `sync` command was updated to explicitly ignore these placeholders.

### 4. ID Generation
The ID generation strategy is "Max ID + 1". This requires parsing the entire file to find the max ID.
*   **Risk**: Race conditions if two branches add IDs simultaneously. The file lock mitigates this for local operations, but merge conflicts on the ledger file are still likely if IDs collide.

## Implementation Details
*   **`ledger_manager.py`**: Refined to support `next-id` command and robust `register` fallback.
*   **`pre-commit` hook**: Implemented to auto-register new audit files.
*   **Tests**: Comprehensive unit tests added in `tests/test_ledger_manager.py`.
