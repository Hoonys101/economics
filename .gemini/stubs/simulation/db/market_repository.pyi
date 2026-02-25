from _typeshed import Incomplete
from simulation.db.base_repository import BaseRepository as BaseRepository
from simulation.dtos import MarketHistoryData as MarketHistoryData, TransactionData as TransactionData
from typing import Any

logger: Incomplete

class MarketRepository(BaseRepository):
    """
    Repository for managing market and transaction data.
    """
    def save_transaction(self, data: TransactionData):
        """
        단일 거래 데이터를 데이터베이스에 저장합니다.
        """
    def save_transactions_batch(self, transactions_data: list['TransactionData']):
        """
        여러 거래 데이터를 데이터베이스에 일괄 저장합니다.
        """
    def save_market_history(self, data: MarketHistoryData):
        """
        단일 시장 이력 데이터를 데이터베이스에 저장합니다.
        """
    def save_market_history_batch(self, market_history_data: list['MarketHistoryData']):
        """
        여러 시장 이력 데이터를 데이터베이스에 일괄 저장합니다.
        """
    def get_transactions(self, start_tick: int | None = None, end_tick: int | None = None, market_id: str | None = None) -> list[dict[str, Any]]:
        """
        거래 데이터를 조회합니다.
        """
    def get_market_history(self, market_id: str, start_tick: int | None = None, end_tick: int | None = None, item_id: str | None = None) -> list[dict[str, Any]]:
        """
        특정 시장의 이력 데이터를 조회합니다.
        """
    def clear_data(self) -> None:
        """
        transactions 및 market_history 테이블의 데이터를 삭제합니다.
        """
