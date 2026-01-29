import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from simulation.db.base_repository import BaseRepository

if TYPE_CHECKING:
    from simulation.dtos import EconomicIndicatorData, AIDecisionData

logger = logging.getLogger(__name__)

class AnalyticsRepository(BaseRepository):
    """
    Repository for managing analytics data (economic indicators, AI decisions).
    """

    def save_economic_indicator(self, data: "EconomicIndicatorData"):
        """
        단일 경제 지표 데이터를 데이터베이스에 저장합니다.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO economic_indicators (run_id, time, unemployment_rate, avg_wage, food_avg_price, food_trade_volume, avg_goods_price,
                                                 total_production, total_consumption, total_household_assets,
                                                 total_firm_assets, total_food_consumption, total_inventory, avg_survival_need,
                                                 total_labor_income, total_capital_income)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.run_id,
                    data.time,
                    data.unemployment_rate,
                    data.avg_wage,
                    data.food_avg_price,
                    data.food_trade_volume,
                    data.avg_goods_price,
                    data.total_production,
                    data.total_consumption,
                    data.total_household_assets,
                    data.total_firm_assets,
                    data.total_food_consumption,
                    data.total_inventory,
                    data.avg_survival_need,
                    data.total_labor_income,
                    data.total_capital_income,
                ),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving economic indicator: {e}")
            self.conn.rollback()

    def save_economic_indicators_batch(self, indicators_data: List["EconomicIndicatorData"]):
        """
        여러 경제 지표 데이터를 데이터베이스에 일괄 저장합니다.
        """
        if not indicators_data:
            return
        try:
            data_to_insert = []
            for indicator_data in indicators_data:
                data_to_insert.append(
                    (
                        indicator_data.run_id,
                        indicator_data.time,
                        indicator_data.unemployment_rate,
                        indicator_data.avg_wage,
                        indicator_data.food_avg_price,
                        indicator_data.food_trade_volume,
                        indicator_data.avg_goods_price,
                        indicator_data.total_production,
                        indicator_data.total_consumption,
                        indicator_data.total_household_assets,
                        indicator_data.total_firm_assets,
                        indicator_data.total_food_consumption,
                        indicator_data.total_inventory,
                        indicator_data.avg_survival_need,
                        indicator_data.total_labor_income,
                        indicator_data.total_capital_income,
                    )
                )
            self.cursor.executemany(
                """
                INSERT INTO economic_indicators (run_id, time, unemployment_rate, avg_wage, food_avg_price, food_trade_volume, avg_goods_price,
                                                 total_production, total_consumption, total_household_assets,
                                                 total_firm_assets, total_food_consumption, total_inventory, avg_survival_need,
                                                 total_labor_income, total_capital_income)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data_to_insert,
            )
            self.conn.commit()
            logger.debug(f"Saved {len(indicators_data)} economic indicators in batch")
        except sqlite3.Error as e:
            logger.error(f"Error saving economic indicators batch: {e}")
            self.conn.rollback()
            raise

    def get_economic_indicators(
        self, start_tick: Optional[int] = None, end_tick: Optional[int] = None, run_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        경제 지표 데이터를 조회합니다.
        """
        query = "SELECT * FROM economic_indicators"
        params: List[Any] = []
        conditions = []

        if run_id is not None:
            conditions.append("run_id = ?")
            params.append(run_id)

        if start_tick is not None:
            conditions.append("time >= ?")
            params.append(start_tick)
        if end_tick is not None:
            conditions.append("time <= ?")
            params.append(end_tick)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Sort by time to ensure history is ordered
        query += " ORDER BY time ASC"

        self.cursor.execute(query, params)
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_latest_economic_indicator(self, indicator_name: str) -> Optional[float]:
        """
        특정 경제 지표의 최신 값을 조회합니다.
        """
        query = f"SELECT {indicator_name} FROM economic_indicators ORDER BY time DESC LIMIT 1"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result[0] if result else None

    def save_ai_decision(self, data: "AIDecisionData"):
        """
        AI 에이전트의 의사결정 데이터를 데이터베이스에 저장합니다.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO ai_decisions_history (
                    run_id, tick, agent_id, decision_type, decision_details, predicted_reward, actual_reward
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.run_id,
                    data.tick,
                    data.agent_id,
                    data.decision_type,
                    json.dumps(data.decision_details) if data.decision_details else None,
                    data.predicted_reward,
                    data.actual_reward,
                ),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving AI decision: {e}")
            self.conn.rollback()
            raise

    def clear_data(self):
        """
        economic_indicators 및 ai_decisions_history 테이블의 데이터를 삭제합니다.
        """
        try:
            self.cursor.execute("DELETE FROM economic_indicators")
            self.cursor.execute("DELETE FROM ai_decisions_history")
            self.conn.commit()
            logger.debug("Cleared economic_indicators and ai_decisions_history tables.")
        except sqlite3.Error as e:
            logger.error(f"Error clearing analytics data: {e}")
            self.conn.rollback()
