from _typeshed import Incomplete
from simulation.core_agents import Household as Household
from simulation.firms import Firm as Firm
from simulation.markets.stock_market import StockMarket as StockMarket
from typing import Any

logger: Incomplete

class InequalityTracker:
    """불평등 및 계층 이동 지표 추적기"""
    config_module: Incomplete
    previous_quintiles: dict[int, int]
    initial_quintiles: dict[int, int]
    cohort_initialized: bool
    transition_matrix: dict[int, dict[int, int]]
    def __init__(self, config_module: Any) -> None: ...
    def calculate_gini_coefficient(self, values: list[float]) -> float:
        """
        지니계수를 계산합니다.
        
        Args:
            values: 자산/소득 값 리스트
            
        Returns:
            지니계수 (0~1, 높을수록 불평등)
        """
    def initialize_cohort(self, households: list['Household']) -> None:
        """
        코호트 추적을 초기화합니다.
        시뮬레이션 시작 시점의 분위를 기록합니다.
        """
    def calculate_quintile_distribution(self, households: list['Household']) -> dict[str, Any]:
        """
        자산 기준 5분위 분포를 계산합니다.
        
        Returns:
            분위별 가계 수, 평균 자산, 점유율
        """
    def calculate_social_mobility(self, households: list['Household']) -> dict[str, Any]:
        """
        계층 이동 지표를 계산합니다 (틱 간 단기 이동).
        
        Returns:
            상향/하향/유지 이동 수, 이동성 지수
        """
    def calculate_longitudinal_mobility(self, households: list['Household']) -> dict[str, Any]:
        """
        코호트 기반 종단 계층 이동을 계산합니다.
        초기 분위에서 현재 분위로의 이동을 추적합니다.
        
        Returns:
            - 초기 하위층(1-2분위) → 현재 상위층(4-5분위) 상승 수
            - 초기 상위층(4-5분위) → 현재 하위층(1-2분위) 하락 수
            - 전이 행렬
        """
    def get_transition_probability_matrix(self) -> dict[int, dict[int, float]]:
        """
        전이 확률 행렬을 반환합니다.
        각 초기 분위에서 다른 분위로 이동할 확률을 계산합니다.
        """
    def calculate_wealth_distribution(self, households: list['Household'], stock_market: StockMarket | None = None) -> dict[str, Any]:
        """
        부의 분배 종합 지표를 계산합니다.
        """
