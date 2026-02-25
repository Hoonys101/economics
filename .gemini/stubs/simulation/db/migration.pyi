import sqlite3
from _typeshed import Incomplete
from modules.system.api import IDatabaseMigrator as IDatabaseMigrator, MigrationReportDTO
from simulation.db.schema import create_tables as create_tables

logger: Incomplete

class SchemaMigrator:
    """
    Handles database schema migrations to ensure consistency with the codebase.
    Implements IDatabaseMigrator protocol.
    """
    conn: Incomplete
    def __init__(self, connection: sqlite3.Connection) -> None: ...
    def check_schema_health(self) -> dict[str, bool]:
        """
        Verifies if critical tables and columns exist.
        Returns a dict mapping 'Table.Column' to Boolean existence.
        """
    def migrate(self) -> MigrationReportDTO:
        """
        Executes pending migrations (e.g., adding missing columns).
        Must be idempotent.
        """
