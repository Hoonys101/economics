from _typeshed import Incomplete
from collections import deque
from modules.system.api import CurrencyCode as CurrencyCode
from simulation.core_agents import Household as Household
from simulation.core_markets import Market as Market
from simulation.dtos.api import MarketContextDTO as MarketContextDTO
from simulation.firms import Firm as Firm
from simulation.world_state import WorldState as WorldState
from typing import Any

logger: Incomplete

class EconomicIndicatorTracker:
    """경제 시뮬레이션의 주요 지표들을 추적하고 기록하는 클래스.

    매 틱마다 가계, 기업, 시장 데이터를 기반으로 실업률, 평균 가격, 총 자산 등을 계산하고 저장합니다.
    """
    metrics: dict[str, list[float]]
    history_window: int
    gdp_history: deque[float]
    cpi_history: deque[float]
    m2_leak_history: deque[float]
    config_module: Incomplete
    exchange_engine: Incomplete
    all_fieldnames: list[str]
    logger: Incomplete
    def __init__(self, config_module: Any) -> None:
        """EconomicIndicatorTracker를 초기화합니다.

        metrics: 추적할 경제 지표들을 저장하는 딕셔너리.
        config_module: 시뮬레이션 설정을 담고 있는 모듈.
        all_fieldnames: CSV 파일 저장 시 사용될 모든 필드 이름 리스트 (이제 사용되지 않음).
        """
    def capture_market_context(self) -> MarketContextDTO:
        """
        Captures the current exchange rates and other global market context.
        Tick-Snapshot Injection to ensure O(1) access for AI agents.
        """
    def calculate_gini_coefficient(self, values: list[float]) -> float:
        """
        TD-015: Calculate Gini coefficient.
        """
    def calculate_social_cohesion(self, households: list[Household]) -> float:
        """
        TD-015: Calculate Social Cohesion based on average Trust Score of active households.
        """
    def calculate_population_metrics(self, households: list[Household], markets: dict[str, Market] | None = None) -> dict[str, Any]:
        """
        TD-015: Calculate Population Metrics (Distribution, Active Count).
        Returns a dictionary with 'distribution' (quintiles) and 'active_count'.
        Now includes Stock Portfolio value in Total Assets.
        """
    def track(self, time: int, households: list[Household], firms: list[Firm], markets: dict[str, Market], money_supply: float = 0.0, m2_leak: float = 0.0, monetary_base: float = 0.0) -> None:
        """현재 시뮬레이션 틱의 경제 지표를 계산하고 기록합니다."""
    def get_smoothed_values(self) -> dict[str, float]:
        """
        Returns the Simple Moving Average (SMA) of key indicators.
        Window size is defined by self.history_window (default 50).
        """
    def get_latest_indicators(self) -> dict[str, Any]:
        """가장 최근에 기록된 경제 지표들을 딕셔너리 형태로 반환합니다."""
    def calculate_monetary_aggregates(self, world_state: WorldState) -> dict[str, float]:
        """
        TD-015: Calculates M0, M1, M2 money supply aggregates.
        Delegates to WorldState for precise Penny Standard calculation.
        """
    def get_m2_money_supply(self, world_state: WorldState) -> float:
        """
        Calculates the M2 money supply for economic reporting.
        Deprecated: Use calculate_monetary_aggregates instead.
        """
