import sqlite3
import logging
from datetime import datetime
from typing import Optional
from simulation.db.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class RunRepository(BaseRepository):
    """
    Repository for managing simulation runs.
    """

    def save_simulation_run(self, config_hash: str, description: str) -> int:
        """
        새로운 시뮬레이션 실행 정보를 저장하고 실행 ID를 반환합니다.
        """
        try:
            start_time = datetime.now().isoformat()
            self.cursor.execute(
                "INSERT INTO simulation_runs (start_time, description, config_hash) VALUES (?, ?, ?)",
                (start_time, description, config_hash),
            )
            self.conn.commit()
            run_id = self.cursor.lastrowid
            logger.info(f"Started new simulation run with ID: {run_id}")
            return run_id
        except sqlite3.Error as e:
            logger.error(f"Error creating simulation run: {e}")
            self.conn.rollback()
            raise

    def update_simulation_run_end_time(self, run_id: int):
        """
        시뮬레이션 실행의 종료 시간을 업데이트합니다.
        """
        try:
            end_time = datetime.now().isoformat()
            self.cursor.execute(
                "UPDATE simulation_runs SET end_time = ? WHERE run_id = ?",
                (end_time, run_id),
            )
            self.conn.commit()
            logger.info(f"Finalized simulation run with ID: {run_id}")
        except sqlite3.Error as e:
            logger.error(f"Error finalizing simulation run {run_id}: {e}")
            self.conn.rollback()
            raise

    def update_last_safe_tick(self, run_id: int, tick: int) -> None:
        """
        Updates the last_safe_tick for the specified run_id.
        """
        try:
            self.cursor.execute(
                "UPDATE simulation_runs SET last_safe_tick = ? WHERE run_id = ?",
                (tick, run_id)
            )
            self.conn.commit()
            logger.debug(f"Updated last_safe_tick to {tick} for run {run_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating last_safe_tick for run {run_id}: {e}")
            self.conn.rollback()
            raise

    def get_last_safe_tick(self, run_id: int) -> int:
        """
        Retrieves the last_safe_tick for the given run_id.
        """
        try:
            self.cursor.execute(
                "SELECT last_safe_tick FROM simulation_runs WHERE run_id = ?",
                (run_id,)
            )
            row = self.cursor.fetchone()
            if row and row[0] is not None:
                return row[0]
            return 0
        except sqlite3.Error as e:
            logger.error(f"Error retrieving last_safe_tick for run {run_id}: {e}")
            return 0

    def save_registry_snapshot(self, run_id: int, tick: int, data: str) -> None:
        """
        Saves a JSON snapshot of the GlobalRegistry at a specific tick.
        """
        try:
            self.cursor.execute(
                "INSERT INTO registry_snapshots (run_id, time, data) VALUES (?, ?, ?)",
                (run_id, tick, data)
            )
            self.conn.commit()
            logger.debug(f"Saved registry snapshot for run {run_id} at tick {tick}")
        except sqlite3.Error as e:
            logger.error(f"Error saving registry snapshot for run {run_id}: {e}")
            self.conn.rollback()
            raise
