import pytest
import sqlite3
import os
from simulation.db.migration import SchemaMigrator
from simulation.db.repository import SimulationRepository
from simulation.db.schema import create_tables

DB_PATH = "test_migration.db"

@pytest.fixture
def db_connection():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_migration_creates_tables_if_missing(db_connection):
    migrator = SchemaMigrator(db_connection)
    report = migrator.migrate()

    assert report.success
    assert "transactions (created)" in report.migrated_tables

    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
    assert cursor.fetchone() is not None

def test_migration_adds_total_pennies_column(db_connection):
    # 1. Setup Legacy Schema (Transactions without total_pennies)
    cursor = db_connection.cursor()
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            time INTEGER,
            buyer_id INTEGER,
            seller_id INTEGER,
            item_id TEXT,
            quantity REAL,
            price REAL,
            market_id TEXT,
            transaction_type TEXT
        )
    """)
    # Insert legacy data
    cursor.execute("""
        INSERT INTO transactions (run_id, time, buyer_id, seller_id, item_id, quantity, price, market_id, transaction_type)
        VALUES (1, 1, 101, 201, 'food', 10.0, 5.50, 'food_market', 'purchase')
    """)
    db_connection.commit()

    # Verify column is missing
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [info[1] for info in cursor.fetchall()]
    assert "total_pennies" not in columns

    # 2. Run Migration
    migrator = SchemaMigrator(db_connection)
    report = migrator.migrate()

    assert report.success
    assert "transactions (added total_pennies)" in report.migrated_tables

    # 3. Verify Column Added and Backfilled
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [info[1] for info in cursor.fetchall()]
    assert "total_pennies" in columns

    cursor.execute("SELECT total_pennies FROM transactions WHERE id=1")
    row = cursor.fetchone()
    # 10.0 * 5.50 = 55.0 -> 5500 pennies
    assert row[0] == 5500
    assert isinstance(row[0], int)

def test_migration_idempotency(db_connection):
    migrator = SchemaMigrator(db_connection)

    # First Run
    report1 = migrator.migrate()
    assert report1.success

    # Second Run
    report2 = migrator.migrate()
    assert report2.success
    assert not report2.migrated_tables  # Should be empty
    assert not report2.errors
