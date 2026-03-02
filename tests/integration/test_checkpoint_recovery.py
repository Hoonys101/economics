import pytest
import sqlite3
import json
from unittest.mock import MagicMock
from simulation.systems.persistence_manager import PersistenceManager
from simulation.db.repository import SimulationRepository
from simulation.db.migration import SchemaMigrator

def test_checkpoint_recovery():
    # 1. Setup in-memory DB and Repository
    repo = SimulationRepository()
    # Force memory db for testing
    conn = sqlite3.connect(":memory:")
    repo.conn = conn
    repo.runs.conn = conn
    repo.runs.cursor = conn.cursor()

    migrator = SchemaMigrator(conn)
    migrator.migrate()

    # Create a dummy run
    cursor = conn.cursor()
    cursor.execute("INSERT INTO simulation_runs (start_time, config_hash) VALUES ('2023-01-01', 'hash')")
    run_id = cursor.lastrowid
    conn.commit()

    repo.runs.run_id = run_id

    # Mock Config / GlobalRegistry
    mock_registry = MagicMock()
    # Let's mock the snapshot dictionary
    mock_entry = MagicMock()
    mock_entry.value = "test_value"
    mock_registry.snapshot.return_value = {"test_key": mock_entry}

    # 2. Setup PersistenceManager
    pm = PersistenceManager(run_id=run_id, config_module=MagicMock(), repository=repo)

    # 3. Trigger Checkpoint
    target_tick = 20
    pm.checkpoint_state(target_tick, mock_registry)

    # 4. Verify DB state (simulate recovery)
    last_safe_tick = repo.runs.get_last_safe_tick(run_id)
    assert last_safe_tick == target_tick, f"Expected last_safe_tick to be {target_tick}, got {last_safe_tick}"

    cursor.execute("SELECT data FROM registry_snapshots WHERE run_id = ? AND time = ?", (run_id, target_tick))
    row = cursor.fetchone()
    assert row is not None, "Snapshot data not found in DB"

    snapshot_data = json.loads(row[0])
    assert snapshot_data["test_key"] == "test_value", "Snapshot data did not correctly serialize the registry"

    repo.close()
