import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from simulation.db.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class RunRepository(BaseRepository):
    """
    Repository for managing simulation runs.
    """

    def save_simulation_run(self, config_hash: str, description: str, seed: Optional[int] = None) -> int:
        """
        새로운 시뮬레이션 실행 정보를 저장하고 실행 ID를 반환합니다.
        """
        try:
            start_time = datetime.now().isoformat()
            self.cursor.execute(
                "INSERT INTO simulation_runs (start_time, description, config_hash, seed) VALUES (?, ?, ?, ?)",
                (start_time, description, config_hash, seed),
            )
            self.conn.commit()
            run_id = self.cursor.lastrowid
            logger.info(f"Started new simulation run with ID: {run_id}, Seed: {seed}")
            return run_id
        except sqlite3.Error as e:
            logger.error(f"Error creating simulation run: {e}")
            self.conn.rollback()
            raise

    def get_run_info(self, run_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves details of a simulation run.
        """
        try:
            self.cursor.execute("SELECT * FROM simulation_runs WHERE run_id = ?", (run_id,))
            row = self.cursor.fetchone()
            if row:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching run info for {run_id}: {e}")
            return None

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
