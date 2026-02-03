import argparse
import os
import re
import sys
import time
import datetime
from typing import List, Dict, Optional, TypedDict, Union, Tuple, Set
from pathlib import Path
import shutil
import subprocess

# --- DTOs ---

class LedgerItemDTO(TypedDict):
    id: str
    date: str
    description: str
    impact: str
    status: str
    section: str  # For internal tracking
    extra_columns: Dict[str, str] # For handling extra columns like "Reason for Abort"

# --- Blocks ---

class Block:
    pass

class TextBlock(Block):
    def __init__(self, content: str):
        self.content = content # Raw content including newlines

    def __repr__(self):
        return f"TextBlock(len={len(self.content)})"

class TableBlock(Block):
    def __init__(self, section_title: str, headers: List[str], rows: List[LedgerItemDTO]):
        self.section_title = section_title
        self.headers = headers
        self.rows = rows

    def __repr__(self):
        return f"TableBlock(section='{self.section_title}', rows={len(self.rows)})"

# --- Ledger Manager ---

class LedgerManager:
    def __init__(self, ledger_path: str, archive_dir: str):
        self.ledger_path = Path(ledger_path)
        self.archive_dir = Path(archive_dir)
        self.lock_file = self.ledger_path.with_suffix('.lock')
        self.backup_file = self.ledger_path.with_suffix('.md.bak')

    def _acquire_lock(self):
        try:
            # Atomic creation. Fails if file exists.
            with open(self.lock_file, 'x'):
                pass
        except FileExistsError:
            raise RuntimeError(f"Lock file exists: {self.lock_file}. Manual intervention required.")

    def _release_lock(self):
        if self.lock_file.exists():
            self.lock_file.unlink()

    def _backup(self):
        if self.ledger_path.exists():
            shutil.copy2(self.ledger_path, self.backup_file)

    def _restore(self):
        if self.backup_file.exists():
            shutil.copy2(self.backup_file, self.ledger_path)
            print("Restored from backup.")

    def _parse_ledger(self) -> List[Block]:
        if not self.ledger_path.exists():
            raise FileNotFoundError(f"Ledger not found: {self.ledger_path}")

        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        blocks: List[Block] = []
        current_text_lines = []
        current_section = "General"

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check for Section Header in text
            section_match = re.match(r'^##\s+(.*)', line)
            if section_match:
                current_section = section_match.group(1).strip()

            # Check if line looks like start of a table
            # Must start with | and have at least one | inside
            if stripped.startswith('|') and stripped.count('|') >= 2:
                # Flush text block
                if current_text_lines:
                    blocks.append(TextBlock("".join(current_text_lines)))
                    current_text_lines = []

                # Parse Table
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i])
                    i += 1

                table_block = self._parse_table_lines(table_lines, current_section)
                blocks.append(table_block)
                continue

            # Text line
            current_text_lines.append(line)
            i += 1

        if current_text_lines:
            blocks.append(TextBlock("".join(current_text_lines)))

        return blocks

    def _parse_table_lines(self, lines: List[str], section: str) -> TableBlock:
        if len(lines) < 2:
            return TableBlock(section, [], [])

        # Parse Header
        header_line = lines[0]
        # Use regex to split by pipe only if not escaped
        header_parts = re.split(r'(?<!\\)\|', header_line.strip())
        headers = [h.strip().replace(r'\|', '|') for h in header_parts if h.strip()]

        # Parse Separator (skip lines[1])

        rows = []
        for line in lines[2:]:
            raw_cols = re.split(r'(?<!\\)\|', line.strip())

            # Remove empty first/last elements if they exist (due to leading/trailing pipes)
            if raw_cols and raw_cols[0].strip() == '': raw_cols.pop(0)
            if raw_cols and raw_cols[-1].strip() == '': raw_cols.pop(-1)

            clean_cols = [c.strip().replace(r'\|', '|') for c in raw_cols]

            if not clean_cols:
                continue

            item: LedgerItemDTO = {
                'id': '', 'date': '', 'description': '', 'impact': '', 'status': '',
                'section': section, 'extra_columns': {}
            }

            # Map by index using headers
            for idx, col_val in enumerate(clean_cols):
                if idx < len(headers):
                    header_name = headers[idx].lower()
                    if header_name == 'id': item['id'] = col_val
                    elif header_name == 'date': item['date'] = col_val
                    elif header_name == 'description': item['description'] = col_val
                    elif header_name == 'impact': item['impact'] = col_val
                    elif header_name == 'status': item['status'] = col_val
                    else:
                        item['extra_columns'][headers[idx]] = col_val

            rows.append(item)

        return TableBlock(section, headers, rows)

    def _write_ledger(self, blocks: List[Block]):
        with open(self.ledger_path, 'w', encoding='utf-8') as f:
            for block in blocks:
                if isinstance(block, TextBlock):
                    f.write(block.content)
                elif isinstance(block, TableBlock):
                    f.write(self._render_table(block))

    def _render_table(self, block: TableBlock) -> str:
        if not block.headers:
            return ""

        lines = []

        # Header
        header_row = "| " + " | ".join(block.headers) + " |"
        lines.append(header_row)

        # Separator
        separator = "| " + " | ".join(["---"] * len(block.headers)) + " |"
        lines.append(separator)

        # Rows
        for row in block.rows:
            cols = []
            for h in block.headers:
                h_lower = h.lower()
                val = ""
                if h_lower == 'id': val = row.get('id', '')
                elif h_lower == 'date': val = row.get('date', '')
                elif h_lower == 'description': val = row.get('description', '')
                elif h_lower == 'impact': val = row.get('impact', '')
                elif h_lower == 'status': val = row.get('status', '')
                else:
                    val = row.get('extra_columns', {}).get(h, '')

                # Escape pipes
                val = str(val).replace('|', r'\|')
                cols.append(val)

            line = "| " + " | ".join(cols) + " |"
            lines.append(line)

        return "\n".join(lines) + "\n"

    def archive_resolved_items(self):
        print(f"Archiving resolved items from {self.ledger_path}...")
        self._acquire_lock()
        self._backup()
        try:
            blocks = self._parse_ledger()
            resolved_items = []

            for block in blocks:
                if isinstance(block, TableBlock):
                    new_rows = []
                    for row in block.rows:
                        status = row['status'].upper().replace('*', '').strip()
                        if status in ('RESOLVED', 'COMPLETED'):
                            resolved_items.append(row)
                        else:
                            new_rows.append(row)
                    block.rows = new_rows

            if not resolved_items:
                print("No resolved items found.")
                self._release_lock()
                return

            self._write_ledger(blocks)
            self._append_to_archive(resolved_items)
            print(f"Archived {len(resolved_items)} items.")

        except Exception as e:
            print(f"Error during archive: {e}")
            self._restore()
            raise e
        finally:
            self._release_lock()

    def _append_to_archive(self, items: List[LedgerItemDTO]):
        current_month = datetime.datetime.now().strftime("%Y-%m")
        archive_file = self.archive_dir / f"TD_ARCHIVE_{current_month}.md"

        self.archive_dir.mkdir(parents=True, exist_ok=True)

        exists = archive_file.exists()

        with open(archive_file, 'a', encoding='utf-8') as f:
            if not exists:
                f.write(f"# Technical Debt Archive - {current_month}\n\n")
                f.write("| ID | Date | Description | Impact | Status | Section |\n")
                f.write("|---|---|---|---|---|---|\n")

            for item in items:
                # Assuming standard columns for archive + Section
                line = f"| {item['id']} | {item['date']} | {item['description']} | {item['impact']} | {item['status']} | {item['section']} |\n"
                f.write(line)

        print(f"Appended to {archive_file}")

    def register_new_item(self, new_item_data: Dict[str, str]):
        print(f"Registering new item: {new_item_data['id']}")
        self._acquire_lock()
        self._backup()
        try:
            blocks = self._parse_ledger()

            # Find target section
            target_section = "8. OPERATIONS & DOCUMENTATION" # Default
            # Ideally try to find section from input or default

            # Find the TableBlock matching the section
            target_block = None
            for block in blocks:
                if isinstance(block, TableBlock):
                    if target_section in block.section_title:
                        target_block = block
                        break

            if not target_block:
                # Fallback to the last table block if not found, or first?
                # Or "General" if we created one?
                # Let's fallback to any table that isn't ABORTED
                for block in blocks:
                    if isinstance(block, TableBlock) and "ABORTED" not in block.section_title.upper():
                         target_block = block
                         # break? maybe prefer explicit match

            if not target_block:
                raise ValueError(f"Could not find a suitable table section to insert {new_item_data['id']}")

            # Create DTO
            item: LedgerItemDTO = {
                'id': new_item_data['id'],
                'date': datetime.datetime.now().strftime("%Y-%m-%d"),
                'description': new_item_data['description'],
                'impact': new_item_data['impact'],
                'status': new_item_data['status'],
                'section': target_block.section_title,
                'extra_columns': {}
            }

            target_block.rows.append(item)

            self._write_ledger(blocks)
            print("Item registered successfully.")

        except Exception as e:
            print(f"Error during registration: {e}")
            self._restore()
            raise e
        finally:
            self._release_lock()

    def sync_with_codebase(self):
        print("Syncing ledger with codebase...")
        blocks = self._parse_ledger()
        active_ids = set()

        for block in blocks:
            if isinstance(block, TableBlock):
                if "ABORTED" in block.section_title.upper():
                    continue # Skip aborted items for sync
                for row in block.rows:
                    status = row['status'].upper().replace('*', '').strip()
                    item_id = row['id'].strip()
                    if item_id == "(Empty)":
                        continue
                    if status not in ('RESOLVED', 'COMPLETED'):
                        active_ids.add(item_id)

        print(f"Found {len(active_ids)} active items in ledger.")

        # Scan code
        code_todos = self._scan_code_for_todos()

        orphaned_todos = {td_id: locs for td_id, locs in code_todos.items() if td_id not in active_ids}
        missing_from_code = {td_id for td_id in active_ids if td_id not in code_todos}

        print("\n--- Sync Report ---")

        if orphaned_todos:
            print(f"\n[ORPHANED TODOs] (In code, but not ACTIVE in ledger): {len(orphaned_todos)}")
            for td_id, locs in orphaned_todos.items():
                print(f"  - {td_id}: {', '.join(locs[:3])}...")
        else:
            print("\n[ORPHANED TODOs]: None")

        if missing_from_code:
            print(f"\n[UNTRACKED DEBT] (Active in ledger, missing TODO in code): {len(missing_from_code)}")
            for td_id in missing_from_code:
                print(f"  - {td_id}")
        else:
            print("\n[UNTRACKED DEBT]: None")

        if not orphaned_todos and not missing_from_code:
            print("\nLedger and Codebase are in sync.")

    def _scan_code_for_todos(self) -> Dict[str, List[str]]:
        # Returns { 'TD-123': ['file:line', ...] }
        # Pattern: TODO(TD-XXX)
        pattern = r"TODO\(TD-[a-zA-Z0-9_-]+\)"

        # Use grep for speed
        # grep -r "TODO(TD-" .

        results = {}

        try:
            # Explicitly exclude .git, __pycache__, and other ignored dirs if needed
            # But grep -r . usually respects ignore? No, standard grep doesn't.
            # We can use git grep if inside a git repo.

            cmd = ["grep", "-rn", "TODO(TD-", "."]

            # If git is available and we are in a repo, git grep is better.
            if os.path.exists(".git"):
                 cmd = ["git", "grep", "-n", "TODO(TD-"]

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode != 0 and process.returncode != 1:
                # 1 means not found, which is fine
                print(f"Error running grep: {stderr}")
                return {}

            for line in stdout.splitlines():
                # Format: file:line:content
                parts = line.split(':', 2)
                if len(parts) < 3:
                    continue

                filename, lineno, content = parts

                # Extract TD-ID
                match = re.search(r"TODO\((TD-[a-zA-Z0-9_-]+)\)", content)
                if match:
                    td_id = match.group(1)
                    if td_id not in results:
                        results[td_id] = []
                    results[td_id].append(f"{filename}:{lineno}")

        except Exception as e:
            print(f"Failed to scan code: {e}")

        return results

def main():
    parser = argparse.ArgumentParser(description="Ledger Automation Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Archive
    subparsers.add_parser("archive", help="Archive resolved entries")

    # Sync
    subparsers.add_parser("sync", help="Synchronize ledger with codebase TODOs")

    # Register
    reg_parser = subparsers.add_parser("register", help="Register a new entry")
    reg_parser.add_argument("--id", required=True, help="Technical Debt ID (e.g. TD-199)")
    reg_parser.add_argument("--desc", required=True, help="Description")
    reg_parser.add_argument("--impact", required=True, help="Impact")
    reg_parser.add_argument("--status", required=True, help="Status (ACTIVE, etc)")

    args = parser.parse_args()

    # Paths
    # Assuming script is in scripts/ and ledger is in design/2_operations/ledgers/
    # Or relative to repo root.

    # Check if we are in repo root
    repo_root = os.getcwd()
    ledger_path = os.path.join(repo_root, "design/2_operations/ledgers/TECH_DEBT_LEDGER.md")
    archive_dir = os.path.join(repo_root, "design/_archive/ledgers")

    # If running tests, we might want to override.
    if "PYTEST_CURRENT_TEST" in os.environ:
         # let tests instantiate manager directly
         pass

    manager = LedgerManager(ledger_path, archive_dir)

    if args.command == "archive":
        manager.archive_resolved_items()
    elif args.command == "sync":
        manager.sync_with_codebase()
    elif args.command == "register":
        manager.register_new_item({
            'id': args.id,
            'description': args.desc,
            'impact': args.impact,
            'status': args.status
        })
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
