from _typeshed import Incomplete
from simulation.db.base_repository import BaseRepository as BaseRepository
from simulation.dtos import AIDecisionData as AIDecisionData, EconomicIndicatorData as EconomicIndicatorData
from typing import Any

logger: Incomplete

class AnalyticsRepository(BaseRepository):
    """
    Repository for managing analytics data (economic indicators, AI decisions).
    """
    def save_economic_indicator(self, data: EconomicIndicatorData):
        """
        단일 경제 지표 데이터를 데이터베이스에 저장합니다.
        """
    def save_economic_indicators_batch(self, indicators_data: list['EconomicIndicatorData']):
        """
        여러 경제 지표 데이터를 데이터베이스에 일괄 저장합니다.
        """
    def get_economic_indicators(self, start_tick: int | None = None, end_tick: int | None = None, run_id: int | None = None) -> list[dict[str, Any]]:
        """
        경제 지표 데이터를 조회합니다.
        """
    def get_latest_economic_indicator(self, indicator_name: str) -> float | None:
        """
        특정 경제 지표의 최신 값을 조회합니다.
        """
    def save_ai_decision(self, data: AIDecisionData):
        """
        AI 에이전트의 의사결정 데이터를 데이터베이스에 저장합니다.
        """
    def clear_data(self) -> None:
        """
        economic_indicators 및 ai_decisions_history 테이블의 데이터를 삭제합니다.
        """
