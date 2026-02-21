import sqlite3
import os
from simulation.db.schema import create_tables
from modules.system.constants import ID_GOVERNMENT, ID_CENTRAL_BANK

def verify_persistence():
    db_name = "persistence_test.db"
    if os.path.exists(db_name):
        os.remove(db_name)

    conn = sqlite3.connect(db_name)
    create_tables(conn)
    cursor = conn.cursor()

    # Simulate saving System Agents
    # Schema: agent_states (..., agent_id INTEGER NOT NULL, ...)

    # 1. Save Government (ID 1)
    gov_id = ID_GOVERNMENT
    cursor.execute("""
        INSERT INTO agent_states (run_id, time, agent_id, agent_type, assets, is_active, is_employed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (1, 0, gov_id, "government", 1000000, 1, 0))

    # 2. Save Central Bank (ID 0)
    cb_id = ID_CENTRAL_BANK
    cursor.execute("""
        INSERT INTO agent_states (run_id, time, agent_id, agent_type, assets, is_active, is_employed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (1, 0, cb_id, "central_bank", 999999999, 1, 0))

    conn.commit()

    # Verify Load
    cursor.execute("SELECT agent_id, agent_type FROM agent_states WHERE run_id=1")
    rows = cursor.fetchall()

    print(f"Loaded rows: {rows}")

    ids = [r[0] for r in rows]
    assert gov_id in ids, "Government ID not persisted"
    assert cb_id in ids, "Central Bank ID not persisted"

    # Verify Transaction with Integer IDs
    cursor.execute("""
        INSERT INTO transactions (run_id, time, buyer_id, seller_id, item_id, quantity, price, total_pennies, market_id, transaction_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (1, 0, cb_id, gov_id, "bond", 1.0, 1000.0, 100000, "bond_market", "purchase"))

    conn.commit()

    cursor.execute("SELECT buyer_id, seller_id FROM transactions WHERE run_id=1")
    tx_rows = cursor.fetchall()
    print(f"Transaction rows: {tx_rows}")

    assert tx_rows[0][0] == cb_id
    assert tx_rows[0][1] == gov_id

    conn.close()
    if os.path.exists(db_name):
        os.remove(db_name)

    print("SUCCESS: Persistence Verification Passed.")

if __name__ == "__main__":
    verify_persistence()
