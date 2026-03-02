import sqlite3
import json
import pytest
from simulation.db.run_repository import RunRepository
from simulation.db.migration import SchemaMigrator

def test_run_repo():
    conn = sqlite3.connect(":memory:")
    migrator = SchemaMigrator(conn)
    migrator.migrate()

    repo = RunRepository(conn)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO simulation_runs (start_time, config_hash) VALUES ('2023-01-01', 'hash')")
    run_id = cursor.lastrowid
    conn.commit()

    repo.update_last_safe_tick(run_id, 42)
    assert repo.get_last_safe_tick(run_id) == 42

    repo.save_registry_snapshot(run_id, 42, json.dumps({"key": "value"}))
    cursor.execute("SELECT data FROM registry_snapshots WHERE run_id = ? AND time = ?", (run_id, 42))
    row = cursor.fetchone()
    assert json.loads(row[0])["key"] == "value"
