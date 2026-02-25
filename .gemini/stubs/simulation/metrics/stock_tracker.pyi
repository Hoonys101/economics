from _typeshed import Incomplete
from collections import deque
from modules.system.api import CurrencyCode as CurrencyCode
from simulation.core_agents import Household as Household
from simulation.firms import Firm as Firm
from simulation.markets.stock_market import StockMarket as StockMarket
from typing import Any

logger: Incomplete

class StockMarketTracker:
    """주식 시장 지표 추적기"""
    config_module: Incomplete
    exchange_engine: Incomplete
    previous_firm_data: dict[int, dict[str, float]]
    market_price_history: deque[float]
    def __init__(self, config_module: Any) -> None: ...
    def get_market_volatility(self) -> float:
        """
        Calculates the annualized market volatility (VIX proxy).
        """
    def track_firm_stock_data(self, firm: Firm, stock_market: StockMarket) -> dict[str, Any]:
        """
        개별 기업의 주식 시장 데이터를 수집합니다.
        """
    def track_all_firms(self, firms: list['Firm'], stock_market: StockMarket) -> list[dict[str, Any]]:
        """
        모든 기업의 주식 시장 데이터를 수집합니다.
        """
    def calculate_aggregate_metrics(self, firms: list['Firm'], stock_market: StockMarket) -> dict[str, Any]:
        """
        주식 시장 집계 지표를 계산합니다.
        """

class PersonalityStatisticsTracker:
    """성향별 통계 추적기"""
    config_module: Incomplete
    previous_assets: dict[int, float]
    def __init__(self, config_module: Any) -> None: ...
    def calculate_personality_statistics(self, households: list['Household'], stock_market: StockMarket | None = None) -> list[dict[str, Any]]:
        """
        성향별 통계를 계산합니다.
        """
