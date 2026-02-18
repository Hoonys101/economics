import sqlite3
import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from simulation.db.base_repository import BaseRepository

if TYPE_CHECKING:
    from simulation.dtos import TransactionData, MarketHistoryData

logger = logging.getLogger(__name__)

class MarketRepository(BaseRepository):
    """
    Repository for managing market and transaction data.
    """

    def save_transaction(self, data: "TransactionData"):
        """
        단일 거래 데이터를 데이터베이스에 저장합니다.
        """
        logger.debug(f"Attempting to save transaction: {data}")
        try:
            self.cursor.execute(
                """
                INSERT INTO transactions (run_id, time, buyer_id, seller_id, item_id, quantity, price, total_pennies, market_id, transaction_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.run_id,
                    data.time,
                    data.buyer_id,
                    data.seller_id,
                    data.item_id,
                    data.quantity,
                    data.price,
                    data.total_pennies,
                    data.market_id,
                    data.transaction_type,
                ),
            )
            logger.debug("Transaction executed. Committing...")
            self.conn.commit()
            logger.debug("Transaction committed successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error saving transaction: {e}")
            self.conn.rollback()

    def save_transactions_batch(self, transactions_data: List["TransactionData"]):
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
                        tx_data.run_id,
                        tx_data.time,
                        tx_data.buyer_id,
                        tx_data.seller_id,
                        tx_data.item_id,
                        tx_data.quantity,
                        tx_data.price,
                        tx_data.total_pennies,
                        tx_data.market_id,
                        tx_data.transaction_type,
                    )
                )
            self.cursor.executemany(
                """
                INSERT INTO transactions (run_id, time, buyer_id, seller_id, item_id, quantity, price, total_pennies, market_id, transaction_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data_to_insert,
            )
            self.conn.commit()
            logger.debug(f"Saved {len(transactions_data)} transactions in batch")
        except sqlite3.Error as e:
            logger.error(f"Error saving transactions batch: {e}")
            self.conn.rollback()
            raise

    def save_market_history(self, data: "MarketHistoryData"):
        """
        단일 시장 이력 데이터를 데이터베이스에 저장합니다.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO market_history (time, market_id, item_id, avg_price, trade_volume, best_ask, best_bid, avg_ask, avg_bid, worst_ask, worst_bid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.time,
                    data.market_id,
                    data.item_id,
                    data.avg_price,
                    data.trade_volume,
                    data.best_ask,
                    data.best_bid,
                    data.avg_ask,
                    data.avg_bid,
                    data.worst_ask,
                    data.worst_bid,
                ),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving market history: {e}")
            self.conn.rollback()

    def save_market_history_batch(self, market_history_data: List["MarketHistoryData"]):
        """
        여러 시장 이력 데이터를 데이터베이스에 일괄 저장합니다.
        """
        if not market_history_data:
            return
        try:
            data_to_insert = []
            for data in market_history_data:
                data_to_insert.append(
                    (
                        data.time,
                        data.market_id,
                        data.item_id,
                        data.avg_price,
                        data.trade_volume,
                        data.best_ask,
                        data.best_bid,
                        data.avg_ask,
                        data.avg_bid,
                        data.worst_ask,
                        data.worst_bid,
                    )
                )
            self.cursor.executemany(
                """
                INSERT INTO market_history (time, market_id, item_id, avg_price, trade_volume, best_ask, best_bid, avg_ask, avg_bid, worst_ask, worst_bid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data_to_insert,
            )
            self.conn.commit()
            logger.debug(f"Saved {len(market_history_data)} market history records in batch")
        except sqlite3.Error as e:
            logger.error(f"Error saving market history batch: {e}")
            self.conn.rollback()
            raise

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

    def get_market_history(
        self,
        market_id: str,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        item_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        특정 시장의 이력 데이터를 조회합니다.
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

    def clear_data(self):
        """
        transactions 및 market_history 테이블의 데이터를 삭제합니다.
        """
        try:
            self.cursor.execute("DELETE FROM transactions")
            self.cursor.execute("DELETE FROM market_history")
            self.conn.commit()
            logger.debug("Cleared transactions and market_history tables.")
        except sqlite3.Error as e:
            logger.error(f"Error clearing market data: {e}")
            self.conn.rollback()
