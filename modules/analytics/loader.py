"""
Analytics Loader for Simulation Data.
Handles data loading from SQLite and auxiliary JSON files.
"""
import sqlite3
import pandas as pd
import json
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, db_path: str = "simulation_data.db"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            logger.warning(f"Database file not found at {self.db_path}")

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _get_latest_run_id(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT MAX(run_id) FROM simulation_runs")
                result = cursor.fetchone()
                return result[0] if result and result[0] else 1
            except sqlite3.OperationalError:
                # Fallback if table doesn't exist or other error
                return 1

    def load_economic_indicators(self, run_id: Optional[int] = None) -> pd.DataFrame:
        """Loads economic indicators for a specific run."""
        if run_id is None or run_id == "latest":
            run_id = self._get_latest_run_id()

        query = f"SELECT * FROM economic_indicators WHERE run_id = {run_id} ORDER BY time ASC"

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        if not df.empty:
            df.set_index("time", inplace=True)
        return df

    def load_agent_states(self, run_id: Optional[int] = None) -> pd.DataFrame:
        """Loads agent states for a specific run."""
        if run_id is None or run_id == "latest":
            run_id = self._get_latest_run_id()

        query = f"SELECT * FROM agent_states WHERE run_id = {run_id} ORDER BY time ASC"

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        # Note: agent_states can be large, we don't set index by default as time is not unique
        return df

    def load_market_history(self, run_id: Optional[int] = None, market_id: str = "goods_market") -> pd.DataFrame:
        """Loads market history for a specific market."""
        # Note: market_history table does not always have run_id in legacy schema,
        # but SimulationRepository.save_market_history inserts it?
        # Let's check schema. SimulationRepository schema for market_history:
        # INSERT INTO market_history (time, market_id, item_id, avg_price, ...)
        # It does NOT have run_id!
        # This implies market_history is cleared between runs or shared?
        # SimulationRepository.clear_all_data clears it.
        # So we assume the current DB content belongs to the relevant run(s).
        # We cannot filter by run_id if the column doesn't exist.

        # Check if table has run_id column
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(market_history)")
            columns = [info[1] for info in cursor.fetchall()]

        has_run_id = "run_id" in columns

        query = f"SELECT * FROM market_history WHERE market_id = '{market_id}'"
        if has_run_id and run_id:
             if run_id == "latest":
                 run_id = self._get_latest_run_id()
             query += f" AND run_id = {run_id}"

        query += " ORDER BY time ASC"

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        if not df.empty:
            df.set_index("time", inplace=True)
        return df

    def load_fiscal_history(self, filepath: str = "reports/fiscal_history.json") -> Dict[str, pd.DataFrame]:
        """Loads fiscal history from JSON artifact."""
        if not os.path.exists(filepath):
            logger.warning(f"Fiscal history file not found at {filepath}")
            return {}

        with open(filepath, "r") as f:
            data = json.load(f)

        result = {}
        if "tax_history" in data:
            # tax_history is list of dicts: [{"tick": 1, "total": 100, "tax_revenue": {...}}, ...]
            # We need to flatten it.
            # Actually, the structure in Government agent:
            # revenue_snapshot = self.current_tick_stats["tax_revenue"].copy() -> {"income_tax": 10, ...}
            # revenue_snapshot["tick"] = current_tick
            # revenue_snapshot["total"] = ...

            df_tax = pd.DataFrame(data["tax_history"])
            if not df_tax.empty:
                df_tax.set_index("tick", inplace=True)
            result["tax"] = df_tax

        if "welfare_history" in data:
            df_welfare = pd.DataFrame(data["welfare_history"])
            if not df_welfare.empty:
                df_welfare.set_index("tick", inplace=True)
            result["welfare"] = df_welfare

        return result
