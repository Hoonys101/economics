import sqlite3
from _typeshed import Incomplete
from simulation.db.database import get_db_connection as get_db_connection

logger: Incomplete

class BaseRepository:
    """
    Base class for repositories to share database connection logic.
    """
    conn: Incomplete
    cursor: Incomplete
    def __init__(self, conn: sqlite3.Connection | None = None) -> None: ...
