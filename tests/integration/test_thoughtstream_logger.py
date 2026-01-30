import pytest
import sqlite3
import json
import os
from simulation.db.logger import SimulationLogger
from simulation.db.schema import create_tables

@pytest.fixture
def db_connection(tmp_path):
    # Setup using tmp_path
    db_file = tmp_path / "test_thoughtstream.db"
    db_path = str(db_file)

    conn = sqlite3.connect(db_path)
    create_tables(conn)
    conn.close()

    yield db_path

    # Teardown handled by tmp_path cleanup automatically,
    # but specific file cleanup can be implicit.

def test_logger_functionality(db_connection):
    db_path = db_connection

    # Use Context Manager
    with SimulationLogger(db_path) as logger:
        logger.run_id = 999

        # Log Thoughts
        context1 = {"cash": 100, "price": 50}
        logger.log_thought(
            tick=1,
            agent_id="agent_001",
            action="BUY_FOOD",
            decision="APPROVE",
            reason="HUNGRY",
            context=context1
        )

        context2 = {"cash": 10, "price": 50}
        logger.log_thought(
            tick=1,
            agent_id="agent_002",
            action="BUY_FOOD",
            decision="REJECT",
            reason="INSOLVENT",
            context=context2
        )

        # Log Snapshot (using dict)
        snapshot_dict = {
            "gdp": 1000.0,
            "m2": 500.0,
            "cpi": 1.2,
            "transaction_count": 15
        }
        logger.log_snapshot(tick=1, snapshot_data=snapshot_dict)

        # Log Snapshot (using object)
        class SnapshotDTO:
            def __init__(self, gdp, m2, cpi, transaction_count):
                self.gdp = gdp
                self.m2 = m2
                self.cpi = cpi
                self.transaction_count = transaction_count

        snapshot_obj = SnapshotDTO(1050.0, 510.0, 1.25, 20)
        logger.log_snapshot(tick=2, snapshot_data=snapshot_obj)

        # Force flush (optional as __exit__ calls close() which calls flush())
        logger.flush()

    # Verify Data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check Thoughts
    cursor.execute("SELECT * FROM agent_thoughts WHERE run_id=999 ORDER BY agent_id")
    thoughts = cursor.fetchall()
    assert len(thoughts) == 2

    # thought 1: agent_001
    t1 = thoughts[0]
    # Schema: id, run_id, tick, agent_id, action_type, decision, reason, context_data
    assert t1[1] == 999
    assert t1[2] == 1
    assert t1[3] == "agent_001"
    assert t1[4] == "BUY_FOOD"
    assert t1[5] == "APPROVE"
    assert t1[6] == "HUNGRY"
    assert json.loads(t1[7]) == context1

    # thought 2: agent_002
    t2 = thoughts[1]
    assert t2[3] == "agent_002"
    assert t2[5] == "REJECT"
    assert t2[6] == "INSOLVENT"
    assert json.loads(t2[7]) == context2

    # Check Snapshots
    cursor.execute("SELECT * FROM tick_snapshots WHERE run_id=999 ORDER BY tick")
    snapshots = cursor.fetchall()
    assert len(snapshots) == 2

    # snapshot 1
    s1 = snapshots[0]
    # Schema: id, tick, run_id, gdp, m2, cpi, transaction_count
    assert s1[1] == 1
    assert s1[2] == 999
    assert s1[3] == 1000.0
    assert s1[4] == 500.0
    assert s1[5] == 1.2
    assert s1[6] == 15

    # snapshot 2
    s2 = snapshots[1]
    assert s2[1] == 2
    assert s2[3] == 1050.0
    assert s2[6] == 20

    conn.close()
