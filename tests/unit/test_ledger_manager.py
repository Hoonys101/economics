import pytest
import shutil
import os
from scripts.ledger_manager import LedgerManager, TableBlock

@pytest.fixture
def mock_ledger_env(tmp_path):
    # Setup
    ledger_content = """# Header
## 🏛️ 1. AGENTS
| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-001 | 2026-01-01 | Test | Low | **ACTIVE** |
| TD-002 | 2026-01-01 | Done | Low | **RESOLVED** |

## 📜 8. OPERATIONS & DOCUMENTATION
| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |
"""
    ledger_path = tmp_path / "TECH_DEBT_LEDGER.md"
    ledger_path.write_text(ledger_content, encoding="utf-8")

    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()

    return ledger_path, archive_dir

def test_archive_resolved_items(mock_ledger_env):
    ledger_path, archive_dir = mock_ledger_env
    manager = LedgerManager(str(ledger_path), str(archive_dir))

    manager.archive_resolved_items()

    # Verify ledger content
    content = ledger_path.read_text(encoding="utf-8")
    assert "TD-001" in content
    assert "TD-002" not in content

    # Verify archive content
    archive_files = list(archive_dir.glob("*.md"))
    assert len(archive_files) == 1
    archive_content = archive_files[0].read_text(encoding="utf-8")
    assert "TD-002" in archive_content

def test_register_new_item(mock_ledger_env):
    ledger_path, archive_dir = mock_ledger_env
    manager = LedgerManager(str(ledger_path), str(archive_dir))

    new_item = {
        'id': 'TD-NEW',
        'description': 'New Thing',
        'impact': 'High',
        'status': 'ACTIVE'
    }

    manager.register_new_item(new_item)

    content = ledger_path.read_text(encoding="utf-8")
    assert "TD-NEW" in content
    assert "New Thing" in content
    # Should be in OPERATIONS section if fallback logic works, or last table
    # My mock has OPERATIONS as last table.

    blocks = manager._parse_ledger()
    # Find the block with TD-NEW
    found = False
    for block in blocks:
        if isinstance(block, TableBlock):
            for row in block.rows:
                if row['id'] == 'TD-NEW':
                    found = True
                    assert "OPERATIONS" in block.section_title
    assert found

def test_sync_with_codebase(mock_ledger_env, capsys, mocker):
    ledger_path, archive_dir = mock_ledger_env
    manager = LedgerManager(str(ledger_path), str(archive_dir))

    # Mock scan_code
    mocker.patch.object(manager, '_scan_code_for_todos', return_value={
        'TD-001': ['file.py:10'], # TD-001 is active
        'TD-999': ['file.py:20']  # TD-999 is orphan
    })

    manager.sync_with_codebase()

    captured = capsys.readouterr()
    assert "[ORPHANED TODOs]" in captured.out
    assert "TD-999" in captured.out
    assert "TD-001" not in captured.out # Should be matched, not reported as orphan or untracked

    # TD-001 is active in ledger AND in code -> Synced.
    # TD-002 was RESOLVED in setup, but if we didn't archive it yet, it's NOT ACTIVE for sync logic?
    # Sync logic: status not in (RESOLVED, COMPLETED) -> Active.
    # TD-002 is RESOLVED, so it is skipped.

    # Add an active item in ledger that is missing in code
    # We need to modify ledger first
    blocks = manager._parse_ledger()
    blocks[1].rows.append({ # Add to AGENTS
        'id': 'TD-MISSING',
        'date': '', 'description': '', 'impact': '', 'status': 'ACTIVE',
        'section': 'AGENTS', 'extra_columns': {}
    })
    manager._write_ledger(blocks)

    manager.sync_with_codebase()
    captured = capsys.readouterr()
    assert "TD-MISSING" in captured.out
    assert "[UNTRACKED DEBT]" in captured.out


def test_pipe_escaping_in_ledger(mock_ledger_env):
    ledger_path, archive_dir = mock_ledger_env
    manager = LedgerManager(str(ledger_path), str(archive_dir))

    # Register item with pipe
    new_item = {
        'id': 'TD-PIPE',
        'description': 'Description with | pipe',
        'impact': 'Low',
        'status': 'ACTIVE'
    }

    manager.register_new_item(new_item)

    # Verify file content has escaped pipe
    content = ledger_path.read_text(encoding="utf-8")
    assert r"Description with \| pipe" in content

    # Verify parsing handles it correctly
    blocks = manager._parse_ledger()
    found = False
    for block in blocks:
        if isinstance(block, TableBlock):
            for row in block.rows:
                if row['id'] == 'TD-PIPE':
                    found = True
                    assert row['description'] == 'Description with | pipe'
    assert found
