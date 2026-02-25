import sqlite3
import logging
import time
from typing import Dict, List, Any
from modules.system.api import IDatabaseMigrator, MigrationReportDTO
from simulation.db.schema import create_tables

logger = logging.getLogger(__name__)

class SchemaMigrator:
    """
    Handles database schema migrations to ensure consistency with the codebase.
    Implements IDatabaseMigrator protocol.
    """
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def check_schema_health(self) -> Dict[str, bool]:
        """
        Verifies if critical tables and columns exist.
        Returns a dict mapping 'Table.Column' to Boolean existence.
        """
        health_report = {}

        # Check transactions table
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
        table_exists = cursor.fetchone() is not None
        health_report["transactions"] = table_exists

        if table_exists:
            cursor.execute("PRAGMA table_info(transactions)")
            columns = [info[1] for info in cursor.fetchall()]
            health_report["transactions.total_pennies"] = "total_pennies" in columns
        else:
            health_report["transactions.total_pennies"] = False

        return health_report

    def migrate(self) -> MigrationReportDTO:
        """
        Executes pending migrations (e.g., adding missing columns).
        Must be idempotent.
        """
        migrated_tables = []
        rows_affected = 0
        errors = []
        success = True

        try:
            health = self.check_schema_health()

            # Migration 1: Ensure transactions table exists
            if not health["transactions"]:
                logger.info("Table 'transactions' missing. Creating tables via schema definition.")
                create_tables(self.conn)
                migrated_tables.append("transactions (created)")
                # Re-check health
                health = self.check_schema_health()

            # Migration 2: Add total_pennies column
            if health["transactions"] and not health["transactions.total_pennies"]:
                logger.info("Column 'total_pennies' missing in 'transactions'. Migrating schema.")
                cursor = self.conn.cursor()

                # Add column
                cursor.execute("ALTER TABLE transactions ADD COLUMN total_pennies INTEGER DEFAULT 0")

                # Populate column
                # Using ROUND(price * quantity * 100) to ensure precision before casting to INT.
                # This aligns with modules.finance.utils.currency_math.round_to_pennies.
                cursor.execute("""
                    UPDATE transactions
                    SET total_pennies = CAST(ROUND(price * quantity * 100) AS INTEGER)
                """)
                rows_affected = cursor.rowcount
                self.conn.commit()

                migrated_tables.append("transactions (added total_pennies)")
                logger.info(f"Migration complete: Added 'total_pennies' to 'transactions'. Updated {rows_affected} rows.")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            errors.append(str(e))
            success = False
            self.conn.rollback()

        return MigrationReportDTO(
            success=success,
            migrated_tables=migrated_tables,
            rows_affected=rows_affected,
            errors=errors,
            timestamp=time.time(),
            schema_version="1.1.0"
        )
