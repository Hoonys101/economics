import sqlite3
import logging
from typing import Optional
from simulation.db.database import get_db_connection

logger = logging.getLogger(__name__)

class BaseRepository:
    """
    Base class for repositories to share database connection logic.
    """
    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self.conn = conn if conn else get_db_connection()
        self.cursor = self.conn.cursor()
