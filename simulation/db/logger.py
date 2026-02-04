import sqlite3
import json
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class SimulationLogger:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

        # Optimize SQLite for performance
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")

        self.buffer: List[tuple] = []
        self.snapshot_buffer: List[tuple] = []
        self.run_id: Optional[int] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def log_thought(self, tick: int, agent_id: str, action: str, decision: str, reason: str, context: Dict[str, Any]):
        """
        Logs an agent's thought process.
        """
        self.buffer.append((
            self.run_id,
            tick,
            agent_id,
            action,
            decision,
            reason,
            json.dumps(context)
        ))

    def log_snapshot(self, tick: int, snapshot_data: Any):
        """
        Logs a high-level snapshot of the simulation state.
        snapshot_data is expected to be an object (e.g. DTO) or dict with gdp, m2, cpi, transaction_count.
        """
        from modules.system.api import DEFAULT_CURRENCY

        # Handle both dict and object (DTO) access
        if isinstance(snapshot_data, dict):
            gdp = snapshot_data.get('gdp')
            m2 = snapshot_data.get('m2')
            cpi = snapshot_data.get('cpi')
            transaction_count = snapshot_data.get('transaction_count')
        else:
            gdp = getattr(snapshot_data, 'gdp', None)
            m2 = getattr(snapshot_data, 'm2', None)
            cpi = getattr(snapshot_data, 'cpi', None)
            transaction_count = getattr(snapshot_data, 'transaction_count', None)

        # Handle M2 as Dict (Phase 33)
        if isinstance(m2, dict):
            m2 = m2.get(DEFAULT_CURRENCY, 0.0)
        elif m2 is None:
            m2 = 0.0

        self.snapshot_buffer.append((
            tick,
            self.run_id,
            gdp,
            m2,
            cpi,
            transaction_count
        ))

    def flush(self):
        """
        Flushes buffered logs to the database in a single transaction.
        """
        if not self.buffer and not self.snapshot_buffer:
            return

        try:
            self.conn.execute("BEGIN TRANSACTION;")

            if self.buffer:
                self.conn.executemany("""
                    INSERT INTO agent_thoughts (run_id, tick, agent_id, action_type, decision, reason, context_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, self.buffer)
                self.buffer.clear()

            if self.snapshot_buffer:
                self.conn.executemany("""
                    INSERT INTO tick_snapshots (tick, run_id, gdp, m2, cpi, transaction_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, self.snapshot_buffer)
                self.snapshot_buffer.clear()

            self.conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Failed to flush simulation logs: {e}")
            self.conn.rollback()

    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.flush()
            self.conn.close()
            self.conn = None
