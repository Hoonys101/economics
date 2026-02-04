import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
from pathlib import Path
import shutil

# Add scripts directory to path to import ledger_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from ledger_manager import LedgerManager, LedgerItemDTO, TableBlock, TextBlock

# Test data
SAMPLE_LEDGER_CONTENT = """# Technical Debt Ledger

## 1. AGENTS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-100 | 2026-01-01 | Test Item 1 | Low | ACTIVE |
| TD-101 | 2026-01-02 | Test Item 2 | High | RESOLVED |

## 2. SYSTEMS

| ID | Date | Description | Impact | Refs | Status |
|---|---|---|---|---|---|
| TD-102 | 2026-01-03 | Test Item 3 | Medium | [Ref] | ACTIVE |
"""

@pytest.fixture
def mock_ledger_manager(tmp_path):
    ledger_file = tmp_path / "TECH_DEBT_LEDGER.md"
    archive_dir = tmp_path / "archive"
    ledger_file.write_text(SAMPLE_LEDGER_CONTENT, encoding="utf-8")
    return LedgerManager(str(ledger_file), str(archive_dir))

def test_parse_ledger_standard(mock_ledger_manager):
    blocks = mock_ledger_manager._parse_ledger()
    assert len(blocks) >= 2

    # Find table blocks
    tables = [b for b in blocks if isinstance(b, TableBlock)]
    assert len(tables) == 2

    t1 = tables[0]
    assert t1.section_title == "1. AGENTS"
    assert len(t1.rows) == 2
    assert t1.rows[0]['id'] == 'TD-100'
    assert t1.rows[0]['status'] == 'ACTIVE'
    assert t1.rows[1]['id'] == 'TD-101'
    assert t1.rows[1]['status'] == 'RESOLVED'

    t2 = tables[1]
    assert t2.section_title == "2. SYSTEMS"
    assert len(t2.rows) == 1
    assert t2.rows[0]['id'] == 'TD-102'
    # Check extra column
    assert t2.rows[0]['extra_columns']['Refs'] == '[Ref]'

def test_archive_resolved_items(mock_ledger_manager):
    mock_ledger_manager.archive_resolved_items()

    # Reload
    blocks = mock_ledger_manager._parse_ledger()
    tables = [b for b in blocks if isinstance(b, TableBlock)]

    # TD-101 should be gone
    t1 = tables[0]
    ids = [row['id'] for row in t1.rows]
    assert 'TD-101' not in ids
    assert 'TD-100' in ids

    # Check archive file creation
    archive_files = list(mock_ledger_manager.archive_dir.glob("*.md"))
    assert len(archive_files) == 1
    content = archive_files[0].read_text(encoding='utf-8')
    assert "TD-101" in content
    assert "RESOLVED" in content

def test_register_new_item(mock_ledger_manager):
    new_item = {
        'id': 'TD-999',
        'description': 'New Issue',
        'impact': 'Critical',
        'status': 'ACTIVE'
    }

    # In our sample, we don't have Section 8. It should fallback to the last valid table.
    mock_ledger_manager.register_new_item(new_item)

    blocks = mock_ledger_manager._parse_ledger()
    tables = [b for b in blocks if isinstance(b, TableBlock)]

    # Should attach to "2. SYSTEMS" as it is the last table
    t2 = tables[1]
    ids = [row['id'] for row in t2.rows]
    assert 'TD-999' in ids

    row = t2.rows[-1]
    assert row['id'] == 'TD-999'
    assert row['description'] == 'New Issue'

def test_sync_with_codebase(mock_ledger_manager):
    # Mock _scan_code_for_todos
    with patch.object(mock_ledger_manager, '_scan_code_for_todos') as mock_scan:
        mock_scan.return_value = {
            'TD-100': ['file.py:10'],
            'TD-999': ['file.py:20'] # Orphaned (not in ledger)
        }

        # Capture stdout
        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output

        mock_ledger_manager.sync_with_codebase()

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        # TD-100 is ACTIVE in ledger and exists in code -> OK
        # TD-101 is RESOLVED -> Not active -> Ignored
        # TD-102 is ACTIVE but missing from code -> UNTRACKED DEBT
        # TD-999 is in code but not in ledger -> ORPHANED TODO

        assert "ORPHANED TODOs" in output
        assert "TD-999" in output

        assert "UNTRACKED DEBT" in output
        assert "TD-102" in output

def test_parser_resilience(mock_ledger_manager, tmp_path):
    # Malformed content
    bad_content = """# Header

| ID | Date | Description | Status |
|---|---|---|---|
| TD-200 | 2026-01-01 | Missing pipes | ACTIVE
| TD-201 | 2026-01-01 | Extra | Pipes | | | ACTIVE |
"""
    ledger_file = tmp_path / "BAD_LEDGER.md"
    ledger_file.write_text(bad_content, encoding="utf-8")
    mock_ledger_manager.ledger_path = ledger_file

    blocks = mock_ledger_manager._parse_ledger()
    tables = [b for b in blocks if isinstance(b, TableBlock)]
    assert len(tables) == 1
    t = tables[0]

    assert len(t.rows) >= 1
    row0 = t.rows[0]
    assert row0['id'] == 'TD-200'
    assert row0['status'] == 'ACTIVE'

def test_archive_atomicity_failure(mock_ledger_manager):
    # Mock write to fail
    with patch.object(mock_ledger_manager, '_write_ledger', side_effect=RuntimeError("Disk full")):
        with pytest.raises(RuntimeError):
            mock_ledger_manager.archive_resolved_items()

    # Check if backup exists
    assert mock_ledger_manager.backup_file.exists()

    # Ensure lock is released (or would be in real scenario)
    # The finally block calls _release_lock
    assert not mock_ledger_manager.lock_file.exists()

def test_get_next_id(mock_ledger_manager):
    # IDs in sample are TD-100, TD-101, TD-102. Max is 102.
    next_id = mock_ledger_manager.get_next_id()
    assert next_id == 'TD-103'
