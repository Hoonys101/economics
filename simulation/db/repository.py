import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from simulation.db.database import get_db_connection, close_db_connection

logger = logging.getLogger(__name__)


class SimulationRepository:
    """
    시뮬레이션 데이터를 SQLite3 데이터베이스에 저장하고 조회하는 Repository 클래스입니다.
    """

    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

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

    def save_ai_decision(
        self,
        run_id: int,
        tick: int,
        agent_id: int,
        decision_type: str,
        decision_details: Dict[str, Any],
        predicted_reward: Optional[float] = None,
        actual_reward: Optional[float] = None,
    ):
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
                    run_id,
                    tick,
                    agent_id,
                    decision_type,
                    json.dumps(decision_details) if decision_details else None,
                    predicted_reward,
                    actual_reward,
                ),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving AI decision: {e}")
            self.conn.rollback()
            raise

    def clear_all_data(self):
        """
        모든 시뮬레이션 관련 테이블의 데이터를 삭제합니다.
        """
        try:
            self.cursor.execute("DELETE FROM transactions")
            self.cursor.execute("DELETE FROM agent_states")
            self.cursor.execute("DELETE FROM market_history")
            self.cursor.execute("DELETE FROM economic_indicators")
            self.conn.commit()
            logger.info("All simulation data cleared from database.")
        except sqlite3.Error as e:
            logger.error(f"Error clearing data: {e}")
            self.conn.rollback()

    def save_transaction(self, run_id: int, transaction_data: Dict[str, Any]):
        """
        단일 거래 데이터를 데이터베이스에 저장합니다.
        """
        logger.debug(f"Attempting to save transaction: {transaction_data}")
        try:
            self.cursor.execute(
                """
                INSERT INTO transactions (run_id, time, buyer_id, seller_id, item_id, quantity, price, market_id, transaction_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    run_id,
                    transaction_data["time"],
                    transaction_data["buyer_id"],
                    transaction_data["seller_id"],
                    transaction_data["item_id"],
                    transaction_data["quantity"],
                    transaction_data["price"],
                    transaction_data["market_id"],
                    transaction_data["transaction_type"],
                ),
            )
            logger.debug("Transaction executed. Committing...")
            self.conn.commit()
            logger.debug("Transaction committed successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error saving transaction: {e}")
            self.conn.rollback()

    def save_agent_state(self, run_id: int, agent_state_data: Dict[str, Any]):
        """
        단일 에이전트 상태 데이터를 데이터베이스에 저장합니다.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO agent_states (run_id, time, agent_id, agent_type, assets, is_active, is_employed, employer_id,
                                          needs_survival, needs_labor, inventory_food, current_production, num_employees)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    run_id,
                    agent_state_data["time"],
                    agent_state_data["agent_id"],
                    agent_state_data["agent_type"],
                    agent_state_data["assets"],
                    agent_state_data["is_active"],
                    agent_state_data.get("is_employed"),
                    agent_state_data.get("employer_id"),
                    agent_state_data.get("needs_survival"),
                    agent_state_data.get("needs_labor"),
                    agent_state_data.get("inventory_food"),
                    agent_state_data.get("current_production"),
                    agent_state_data.get("num_employees"),
                ),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving agent state: {e}")
            self.conn.rollback()

    def save_market_history(self, market_history_data: Dict[str, Any]):
        """
        단일 시장 이력 데이터를 데이터베이스에 저장합니다.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO market_history (time, market_id, item_id, avg_price, trade_volume, best_ask, best_bid)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    market_history_data["time"],
                    market_history_data["market_id"],
                    market_history_data.get("item_id"),
                    market_history_data.get("avg_price"),
                    market_history_data.get("trade_volume"),
                    market_history_data.get("best_ask"),
                    market_history_data.get("best_bid"),
                ),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving market history: {e}")
            self.conn.rollback()

    def save_economic_indicator(self, run_id: int, indicator_data: Dict[str, Any]):
        """
        단일 경제 지표 데이터를 데이터베이스에 저장합니다.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO economic_indicators (run_id, time, unemployment_rate, avg_wage, food_avg_price, food_trade_volume, avg_goods_price,
                                                 total_production, total_consumption, total_household_assets,
                                                 total_firm_assets, total_food_consumption, total_inventory)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    run_id,
                    indicator_data["time"],
                    indicator_data.get("unemployment_rate"),
                    indicator_data.get("avg_wage"),
                    indicator_data.get("food_avg_price"),
                    indicator_data.get("food_trade_volume"),
                    indicator_data.get("avg_goods_price"),
                    indicator_data.get("total_production"),
                    indicator_data.get("total_consumption"),
                    indicator_data.get("total_household_assets"),
                    indicator_data.get("total_firm_assets"),
                    indicator_data.get("total_food_consumption"),
                    indicator_data.get("total_inventory"),
                ),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving economic indicator: {e}")
            self.conn.rollback()

    def save_agent_states_batch(self, run_id: int, agent_states_data: List[Dict[str, Any]]):
        """
        여러 에이전트 상태 데이터를 데이터베이스에 일괄 저장합니다.
        """
        if not agent_states_data:
            return
        try:
            # Prepare data for batch insertion
            data_to_insert = []
            for state_data in agent_states_data:
                data_to_insert.append(
                    (
                        run_id, # Add run_id to the data
                        state_data["time"],
                        state_data["agent_id"],
                        state_data["agent_type"],
                        state_data["assets"],
                        state_data["is_active"],
                        state_data.get("is_employed"),
                        state_data.get("employer_id"),
                        state_data.get("needs_survival"),
                        state_data.get("needs_labor"),
                        state_data.get("inventory_food"),
                        state_data.get("current_production"),
                        state_data.get("num_employees"),
                    )
                )
            self.cursor.executemany(
                """
                INSERT INTO agent_states (run_id, time, agent_id, agent_type, assets, is_active, is_employed, employer_id,
                                          needs_survival, needs_labor, inventory_food, current_production, num_employees)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data_to_insert,
            )
            self.conn.commit()
            logger.debug(f"Saved {len(agent_states_data)} agent states in batch for run_id {run_id}")
        except sqlite3.Error as e:
            logger.error(f"Error saving agent states batch: {e}")
            self.conn.rollback()
            raise

    def save_transactions_batch(self, run_id: int, transactions_data: List[Dict[str, Any]]):
        """
        여러 거래 데이터를 데이터베이스에 일괄 저장합니다.
        """
        if not transactions_data:
            return
        try:
            data_to_insert = []
            for tx_data in transactions_data:
                data_to_insert.append(
                    (
                        run_id,
                        tx_data["time"],
                        tx_data["buyer_id"],
                        tx_data["seller_id"],
                        tx_data["item_id"],
                        tx_data["quantity"],
                        tx_data["price"],
                        tx_data["market_id"],
                        tx_data["transaction_type"],
                    )
                )
            self.cursor.executemany(
                """
                INSERT INTO transactions (run_id, time, buyer_id, seller_id, item_id, quantity, price, market_id, transaction_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data_to_insert,
            )
            self.conn.commit()
            logger.debug(f"Saved {len(transactions_data)} transactions in batch for run_id {run_id}")
        except sqlite3.Error as e:
            logger.error(f"Error saving transactions batch: {e}")
            self.conn.rollback()
            raise

    def save_economic_indicators_batch(self, run_id: int, indicators_data: List[Dict[str, Any]]):
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
                        run_id,
                        indicator_data["time"],
                        indicator_data.get("unemployment_rate"),
                        indicator_data.get("avg_wage"),
                        indicator_data.get("food_avg_price"),
                        indicator_data.get("food_trade_volume"),
                        indicator_data.get("avg_goods_price"),
                        indicator_data.get("total_production"),
                        indicator_data.get("total_consumption"),
                        indicator_data.get("total_household_assets"),
                        indicator_data.get("total_firm_assets"),
                        indicator_data.get("total_food_consumption"),
                        indicator_data.get("total_inventory"),
                    )
                )
            self.cursor.executemany(
                """
                INSERT INTO economic_indicators (run_id, time, unemployment_rate, avg_wage, food_avg_price, food_trade_volume, avg_goods_price,
                                                 total_production, total_consumption, total_household_assets,
                                                 total_firm_assets, total_food_consumption, total_inventory)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data_to_insert,
            )
            self.conn.commit()
            logger.debug(f"Saved {len(indicators_data)} economic indicators in batch for run_id {run_id}")
        except sqlite3.Error as e:
            logger.error(f"Error saving economic indicators batch: {e}")
            self.conn.rollback()
            raise

    def get_economic_indicators(
        self, start_tick: Optional[int] = None, end_tick: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        경제 지표 데이터를 조회합니다.
        """
        query = "SELECT * FROM economic_indicators"
        params: List[Any] = []
        if start_tick is not None and end_tick is not None:
            query += " WHERE time BETWEEN ? AND ?"
            params = [start_tick, end_tick]
        elif start_tick is not None:
            query += " WHERE time >= ?"
            params = [start_tick]
        elif end_tick is not None:
            query += " WHERE time <= ?"
            params = [end_tick]

        self.cursor.execute(query, params)
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_latest_economic_indicator(self, indicator_name: str) -> Optional[float]:
        """
        특정 경제 지표의 최신 값을 조회합니다。
        """
        query = f"SELECT {indicator_name} FROM economic_indicators ORDER BY time DESC LIMIT 1"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_market_history(
        self,
        market_id: str,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        item_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        특정 시장의 이력 데이터를 조회합니다。
        """
        query = "SELECT * FROM market_history WHERE market_id = ?"
        params: List[Any] = [market_id]
        if start_tick is not None and end_tick is not None:
            query += " AND time BETWEEN ? AND ?"
            params.extend([start_tick, end_tick])
        elif start_tick is not None:
            query += " AND time >= ?"
            params.append(start_tick)
        elif end_tick is not None:
            query += " AND time <= ?"
            params.append(end_tick)
        if item_id is not None:
            query += " AND item_id = ?"
            params.append(item_id)

        self.cursor.execute(query, params)
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_agent_states(
        self,
        agent_id: int,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        특정 에이전트의 상태 변화 이력을 조회합니다。
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

    def get_transactions(
        self,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        market_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        거래 데이터를 조회합니다.
        """
        query = "SELECT * FROM transactions"
        params: List[Any] = []
        conditions = []

        if start_tick is not None:
            conditions.append("time >= ?")
            params.append(start_tick)
        if end_tick is not None:
            conditions.append("time <= ?")
            params.append(end_tick)
        if market_id is not None:
            conditions.append("market_id = ?")
            params.append(market_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        self.cursor.execute(query, params)
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def close(self):
        """
        Repository 사용을 마칠 때 데이터베이스 연결을 닫습니다.
        """
        close_db_connection()


if __name__ == "__main__":
    # 테스트 코드
    repo = SimulationRepository()

    # 테스트 데이터 저장
    repo.save_transaction(
        {
            "time": 1,
            "buyer_id": 1,
            "seller_id": 2,
            "item_id": "food",
            "quantity": 10.0,
            "price": 5.0,
            "market_id": "goods_market",
            "transaction_type": "goods",
        }
    )
    repo.save_agent_state(
        {
            "time": 1,
            "agent_id": 1,
            "agent_type": "household",
            "assets": 1000.0,
            "is_active": True,
            "is_employed": True,
            "employer_id": 10,
            "needs_survival": 50.0,
            "needs_labor": 20.0,
            "inventory_food": 5.0,
            "current_production": None,
            "num_employees": None,
        }
    )
    repo.save_economic_indicator(
        {
            "time": 1,
            "unemployment_rate": 5.0,
            "avg_wage": 1500.0,
            "food_avg_price": 5.0,
            "total_production": 100.0,
            "total_consumption": 50.0,
            "total_household_assets": 10000.0,
            "total_firm_assets": 5000.0,
            "total_food_consumption": 30.0,
            "total_inventory": 200.0,
        }
    )
    repo.save_market_history(
        {
            "time": 1,
            "market_id": "goods_market",
            "item_id": "food",
            "avg_price": 5.0,
            "trade_volume": 100.0,
            "best_ask": 4.5,
            "best_bid": 5.5,
        }
    )

    # 테스트 데이터 조회
    logger.info(
        "\nEconomic Indicators (Tick 1): %s",
        repo.get_economic_indicators(start_tick=1, end_tick=1),
    )
    logger.info(
        "\nGoods Market History (Tick 1): %s",
        repo.get_market_history(market_id="goods_market", start_tick=1, end_tick=1),
    )
    logger.info(
        "\nAgent 1 State (Tick 1): %s",
        repo.get_agent_states(agent_id=1, start_tick=1, end_tick=1),
    )
    logger.info(
        "\nTransactions (Tick 1): %s", repo.get_transactions(start_tick=1, end_tick=1)
    )

    repo.close()
    logger.info("\nRepository test completed.")
