# SPEC-150: Technical Debt Ledger Automation

- **Version**: 1.0
- **Status**: Proposed
- **Author**: Gemini (Scribe)
- **Addresses**: `TD-150` - Ledger Management Process leading to context loss.

---

## 1. Overview

This document specifies the design for a Python script, `scripts/ledger_manager.py`, and associated hooks to automate the management of the `TECH_DEBT_LEDGER.md`. The goal is to enforce consistency, reduce manual effort, and mitigate the risk of context loss identified in `TD-150`. This automation directly addresses the critical findings of the pre-flight audit, prioritizing safety, atomicity, and clear conventions.

### 1.1. Core Features
1.  **Automated Archiving**: A routine to move resolved entries from the active ledger to a dedicated archive location.
2.  **Auto-Registration Hook**: A mechanism to automatically register new technical debt items when relevant audit files are created.
3.  **Code-Ledger Synchronization**: A verification routine to ensure consistency between `ACTIVE` ledger items and `TODO` comments in the codebase.

## 2. System Architecture & Principles

This system is designed around the architectural constraints identified in the pre-flight audit.

- **Principle 1: Atomicity and Safety (Addresses TD-160)**
    - All write operations on `TECH_DEBT_LEDGER.md` **MUST** be atomic. The process is: Read -> Modify in Memory -> Write.
    - A file-based locking mechanism (`.ledger.lock`) **MUST** be implemented to prevent race conditions during concurrent access (Addresses TD-187).
    - Before every write, a backup (`TECH_DEBT_LEDGER.md.bak`) **MUST** be created. On failure, the script must attempt to restore from this backup.

- **Principle 2: Single Responsibility (Follows `cmd_ops.py` precedent)**
    - The `ledger_manager.py` script is exclusively responsible for operations on the `TECH_DEBT_LEDGER.md` file. It will not contain unrelated business logic.

- **Principle 3: Convention over Configuration**
    - The link between code and ledger items relies on a strict, enforceable comment format: `# TODO(TD-XXX): Details...` (for Python) or `// TODO(TD-XXX): Details...` (for other languages). This format is non-negotiable for the `sync` feature to function.

## 3. Detailed Design: `scripts/ledger_manager.py`

This script will be the central tool for all automated ledger operations.

### 3.1. DTO (Data Transfer Object)

A `TypedDict` will be used to represent a ledger entry in memory, ensuring type safety.

```python
# Location: scripts/ledger_manager.py

from typing import TypedDict, List

class LedgerItemDTO(TypedDict):
    id: str
    date: str
    description: str
    impact: str
    status: str

LedgerData = List[LedgerItemDTO]
```

### 3.2. CLI Interface

The script will expose a command-line interface using `argparse`.

```bash
# 1. Archive resolved entries
python scripts/ledger_manager.py archive

# 2. Synchronize ledger with codebase TODOs
python scripts/ledger_manager.py sync

# 3. Register a new entry (for use by hooks)
python scripts/ledger_manager.py register --id TD-199 --desc "New audit report" --impact "Medium" --status "ACTIVE"
```

### 3.3. Core Components (Pseudo-code)

```python
# Location: scripts/ledger_manager.py

class LedgerManager:
    def __init__(self, ledger_path, archive_dir):
        # ... paths

    def _acquire_lock(self):
        # Create .ledger.lock file
        # Raise exception if lock exists

    def _release_lock(self):
        # Remove .ledger.lock file

    def _backup(self):
        # Copy ledger_path to ledger_path.bak

    def _restore(self):
        # Copy ledger_path.bak to ledger_path

    def _parse_ledger(self) -> LedgerData:
        # 1. Read ledger markdown file.
        # 2. Use a robust markdown table parser to extract rows.
        # 3. For each row, create and validate a LedgerItemDTO.
        # 4. Return list of DTOs.
        # 5. This method MUST be resilient to empty lines or minor formatting deviations.
        pass

    def _write_ledger(self, data: LedgerData):
        # 1. Generate markdown table header.
        # 2. For each DTO in data, create a markdown table row.
        # 3. Write the complete string to the ledger file.
        pass

    def archive_resolved_items(self):
        # with self._lock():
        #   self._backup()
        #   try:
        #       all_items = self._parse_ledger()
        #       resolved_items = [item for item in all_items if item['status'] in ('RESOLVED', 'COMPLETED')]
        #       active_items = [item for item in all_items if item not in resolved_items]
        #
        #       if not resolved_items:
        #           print("No items to archive.")
        #           return
        #
        #       self._write_ledger(active_items)
        #       self._append_to_archive(resolved_items)
        #
        #   except Exception as e:
        #       self._restore()
        #       raise e
        pass

    def sync_with_codebase(self):
        # (Read-only operation, no lock needed)
        # active_ids = {item['id'] for item in self._parse_ledger() if item['status'] == 'ACTIVE'}
        #
        # # Use ripgrep/rg to find all TODOs
        # code_todos = self._scan_code_for_todos() # returns dict {td_id: [locations]}
        #
        # # Find mismatches
        # orphaned_todos = {td_id for td_id in code_todos if td_id not in active_ids}
        # missing_from_code = {td_id for td_id in active_ids if td_id not in code_todos}
        #
        # # Print a structured report to the console.
        pass

    def register_new_item(self, new_item: LedgerItemDTO):
        # with self._lock():
        #    ... (standard backup, parse, append, write, restore-on-fail logic)
        pass
```

## 4. Feature 1: Automated Archiving

- **Trigger**: Manual execution via `python scripts/ledger_manager.py archive`. Recommended for inclusion in a weekly cleanup cron job or post-release script.
- **Logic**:
    1.  The script identifies all entries with `status` of `RESOLVED` or `COMPLETED`.
    2.  These entries are removed from `TECH_DEBT_LEDGER.md`.
    3.  The removed entries are appended to an archive file: `design/_archive/ledgers/TD_ARCHIVE_{YYYY-MM}.md`. A new file is created for each month to keep archives manageable.
- **Risk Mitigation**: The entire operation is performed under a file lock and with a backup, ensuring atomicity.

## 5. Feature 2: Auto-Registration Hook

- **Trigger Mechanism**: A Git `pre-commit` hook. This ensures that new audit files are registered before they are committed to the repository.
- **"Audit File" Definition**: Any new file staged for commit that matches the glob patterns:
    - `analysis_report/WO-*.md`
    - `reports/audits/AUDIT-*.md`
- **Hook Implementation (Pseudo-code for `.git/hooks/pre-commit`)**:
    ```bash
    #!/bin/sh
    
    # Find staged files matching the pattern
    for file in $(git diff --cached --name-only --diff-filter=A | grep -E "analysis_report/WO-.*\.md|reports/audits/AUDIT-.*\.md"); do
      echo "New audit file detected: $file"
      
      # Generate a new TD-ID (e.g., by incrementing the max ID in the ledger)
      NEW_ID=$(python -c "...") # Logic to get next TD-ID
      DESCRIPTION="New audit file created: $file"
      
      # Register the new item
      python scripts/ledger_manager.py register --id $NEW_ID --desc "$DESCRIPTION" --impact "TBD" --status "ACTIVE"
      
      # Add the modified ledger to the commit
      git add design/2_operations/ledgers/TECH_DEBT_LEDGER.md
    done
    ```

## 6. Feature 3: Code-Ledger Synchronization

- **Trigger**: Manual execution via `python scripts/ledger_manager.py sync`. Intended for use by developers locally and in CI pipelines.
- **Convention**: The script will scan for the exact pattern `TODO(TD-XXX)` in all source code files.
- **Logic**: This is a **read-only** operation.
    1.  It gets all `ACTIVE` IDs from the ledger.
    2.  It scans the codebase for all `TODO(TD-XXX)` comments.
    3.  It generates a console report detailing:
        - **Orphaned TODOs**: `TODO`s found in the code whose `TD-ID` is not `ACTIVE` in the ledger. These are likely resolved debts that were not removed from the code.
        - **Untracked Debts**: `ACTIVE` ledger items that have no corresponding `TODO` comment in the codebase. This indicates a missing implementation link.

---

## 7. Risk & Impact Audit (Addressing Pre-flight Check)

- **Data Format Fragility**:
    - **Mitigation**: The `_parse_ledger` function will use a dedicated, well-tested Python library for Markdown table parsing. The design mandates that parsing logic be robust and accompanied by unit tests for malformed rows.
    - **Long-Term Recommendation**: A future initiative (`TD-XXX-RefactorLedgerFormat`) should be created to migrate the ledger from `.md` to a structured format like `YAML` or `JSON` to eliminate parsing risks entirely.

- **Concurrency / Race Conditions**:
    - **Mitigation**: All write operations (`archive`, `register`) are protected by a file lock (`.ledger.lock`). The script will fail immediately if it cannot acquire the lock, preventing race conditions.

- **Synchronization Complexity & Coupling**:
    - **Mitigation**: The `sync` operation is read-only, preventing it from causing direct harm. The dependency on the `TODO` format is explicitly documented as a strict convention. The performance impact of the full-code scan is acknowledged; therefore, it is recommended for CI checks, not for every local commit.

## 8. Verification Plan

The `scripts/ledger_manager.py` script will be accompanied by unit tests.

- **Test Fixtures**: A set of mock `TECH_DEBT_LEDGER.md` files will be created in `tests/fixtures/` to simulate various states (e.g., with resolved items, with malformed rows).
- **Test Cases**:
    - `test_archive_moves_resolved_items`: Verifies that `archive` correctly moves only the completed items.
    - `test_archive_is_atomic_on_failure`: Verifies that the ledger is restored from backup if an error occurs mid-operation.
    - `test_register_adds_new_item`: Verifies `register` correctly adds a new row.
    - `test_sync_identifies_orphaned_and_untracked_items`: Verifies the `sync` report is accurate.
    - `test_parser_resilience`: Verifies the parser can handle common formatting mistakes without crashing.
