import sqlite3
import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from simulation.db.base_repository import BaseRepository
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.dtos import AgentStateData

logger = logging.getLogger(__name__)

class AgentRepository(BaseRepository):
    """
    Repository for managing agent state data.
    """

    def save_agent_state(self, data: "AgentStateData"):
        """
        단일 에이전트 상태 데이터를 데이터베이스에 저장합니다.
        """
        try:
            assets_val = data.assets
            if isinstance(assets_val, dict):
                assets_val = assets_val.get(DEFAULT_CURRENCY, 0.0)

            self.cursor.execute(
                """
                INSERT INTO agent_states (run_id, time, agent_id, agent_type, assets, is_active, is_employed, employer_id,
                                          needs_survival, needs_labor, inventory_food, current_production, num_employees, education_xp, generation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.run_id,
                    data.time,
                    data.agent_id,
                    data.agent_type,
                    assets_val,
                    data.is_active,
                    data.is_employed,
                    data.employer_id,
                    data.needs_survival,
                    data.needs_labor,
                    data.inventory_food,
                    data.current_production,
                    data.num_employees,
                    data.education_xp,
                    data.generation,
                ),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving agent state: {e}")
            self.conn.rollback()

    def save_agent_states_batch(self, agent_states_data: List["AgentStateData"]):
        """
        여러 에이전트 상태 데이터를 데이터베이스에 일괄 저장합니다.
        """
        if not agent_states_data:
            return
        try:
            # Prepare data for batch insertion
            data_to_insert = []
            for state_data in agent_states_data:
                assets_val = state_data.assets
                if isinstance(assets_val, dict):
                    assets_val = assets_val.get(DEFAULT_CURRENCY, 0.0)

                data_to_insert.append(
                    (
                        state_data.run_id,
                        state_data.time,
                        state_data.agent_id,
                        state_data.agent_type,
                        assets_val,
                        state_data.is_active,
                        state_data.is_employed,
                        state_data.employer_id,
                        state_data.needs_survival,
                        state_data.needs_labor,
                        state_data.inventory_food,
                        state_data.current_production,
                        state_data.num_employees,
                        state_data.education_xp,
                        state_data.generation,
                    )
                )
            self.cursor.executemany(
                """
                INSERT INTO agent_states (run_id, time, agent_id, agent_type, assets, is_active, is_employed, employer_id,
                                          needs_survival, needs_labor, inventory_food, current_production, num_employees, education_xp, generation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data_to_insert,
            )
            self.conn.commit()
            logger.debug(f"Saved {len(agent_states_data)} agent states in batch")
        except sqlite3.Error as e:
            logger.error(f"Error saving agent states batch: {e}")
            self.conn.rollback()
            raise

    def get_agent_states(
        self,
        agent_id: int,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        특정 에이전트의 상태 변화 이력을 조회합니다.
        """
        query = "SELECT * FROM agent_states WHERE agent_id = ?"
        params: List[Any] = [agent_id]
        if start_tick is not None and end_tick is not None:
            query += " AND time BETWEEN ? AND ?"
            params.extend([start_tick, end_tick])
        elif start_tick is not None:
            query += " AND time >= ?"
            params.append(start_tick)
        elif end_tick is not None:
            query += " AND time <= ?"
            params.append(end_tick)

        self.cursor.execute(query, params)
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_generation_stats(self, tick: int, run_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        특정 틱의 세대별 인구 및 자산 통계를 조회합니다.
        """
        query = """
            SELECT generation as gen, COUNT(*) as count, AVG(assets) as avg_assets
            FROM agent_states
            WHERE time = ? AND agent_type = 'household'
        """
        params = [tick]
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        query += " GROUP BY generation"

        self.cursor.execute(query, params)
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_attrition_counts(self, start_tick: int, end_tick: int, run_id: Optional[int] = None) -> Dict[str, int]:
        """
        Calculates the number of agents that became inactive (bankruptcy/death) between start_tick and end_tick.

        Args:
            start_tick: The starting tick of the window (inclusive).
            end_tick: The ending tick of the window (inclusive).
            run_id: The simulation run ID.

        Returns:
            Dict with keys "bankruptcy_count" and "death_count".
        """
        params = [end_tick, start_tick]
        query_suffix = ""
        if run_id:
            query_suffix = " AND run_id = ?"

        # Bankruptcy (Firms)
        firm_query = f"""
            SELECT COUNT(DISTINCT agent_id)
            FROM agent_states
            WHERE time = ? AND is_active = 0 AND agent_type = 'firm'
            AND agent_id IN (
                SELECT agent_id FROM agent_states
                WHERE time = ? AND is_active = 1 AND agent_type = 'firm' {query_suffix}
            )
            {query_suffix}
        """

        # Death (Households)
        household_query = f"""
            SELECT COUNT(DISTINCT agent_id)
            FROM agent_states
            WHERE time = ? AND is_active = 0 AND agent_type = 'household'
            AND agent_id IN (
                SELECT agent_id FROM agent_states
                WHERE time = ? AND is_active = 1 AND agent_type = 'household' {query_suffix}
            )
            {query_suffix}
        """

        result = {}

        # Execute Firm Query
        p_firm = [end_tick, start_tick]
        if run_id:
            p_firm.extend([run_id, run_id])

        self.cursor.execute(firm_query, p_firm)
        result["bankruptcy_count"] = self.cursor.fetchone()[0]

        # Execute Household Query
        p_household = [end_tick, start_tick]
        if run_id:
            p_household.extend([run_id, run_id])

        self.cursor.execute(household_query, p_household)
        result["death_count"] = self.cursor.fetchone()[0]

        return result

    def clear_data(self):
        """
        agent_states 테이블의 데이터를 삭제합니다.
        """
        try:
            self.cursor.execute("DELETE FROM agent_states")
            self.conn.commit()
            logger.debug("Cleared agent_states table.")
        except sqlite3.Error as e:
            logger.error(f"Error clearing agent data: {e}")
            self.conn.rollback()
