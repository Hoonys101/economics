import pytest
import sqlite3
import logging
from simulation.db.migration import SchemaMigrator
from simulation.db.schema import create_tables

@pytest.fixture
def db_connection():
    # Use in-memory DB for tests
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()

def test_fresh_install_transactions_table_created(db_connection):
    """
    Test that migrate() creates tables if they don't exist.
    """
    migrator = SchemaMigrator(db_connection)
    report = migrator.migrate()

    assert report.success
    # Wait, my logic says "If transactions missing, create tables".
    # And report adds "transactions (created)"
    assert any("transactions" in s for s in report.migrated_tables)

    # Verify table structure
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "total_pennies" in columns

def test_migration_adds_total_pennies(db_connection):
    """
    Test that migrate() adds total_pennies column if missing,
    and populates it correctly from price * quantity.
    """
    cursor = db_connection.cursor()
    # Manually create a legacy table WITHOUT total_pennies
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            time INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            market_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL
        )
    """)
    # Insert legacy data
    cursor.execute("""
        INSERT INTO transactions (run_id, time, buyer_id, seller_id, item_id, quantity, price, market_id, transaction_type)
        VALUES (1, 10, 100, 200, 'apple', 2.0, 1.5, 'fruit_market', 'buy')
    """)
    db_connection.commit()

    # Verify initial state
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "total_pennies" not in columns

    # Run migration
    migrator = SchemaMigrator(db_connection)
    report = migrator.migrate()

    assert report.success
    # Check if column added
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "total_pennies" in columns

    # Check data population
    cursor.execute("SELECT total_pennies FROM transactions WHERE item_id='apple'")
    val = cursor.fetchone()[0]
    # 2.0 * 1.5 = 3.0 -> * 100 = 300
    assert val == 300

def test_idempotency(db_connection):
    """
    Test that running migrate() twice does not cause errors.
    """
    migrator = SchemaMigrator(db_connection)
    report1 = migrator.migrate()
    assert report1.success

    report2 = migrator.migrate()
    assert report2.success
    assert report2.rows_affected == 0
    assert not report2.errors
