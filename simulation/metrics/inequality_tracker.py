"""
불평등 및 계층 이동 지표 추적기

지니계수, 분위별 자산, 계층 이동 등의 경제적 불평등 지표를 계산합니다.
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
import logging
from statistics import median

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.markets.stock_market import StockMarket

logger = logging.getLogger(__name__)


class InequalityTracker:
    """불평등 및 계층 이동 지표 추적기"""

    def __init__(self, config_module: Any):
        self.config_module = config_module
        
        # 이전 틱의 분위 정보 (틱 간 이동 추적용)
        self.previous_quintiles: Dict[int, int] = {}  # household_id -> quintile (1-5)
        
        # 초기 분위 정보 (코호트 추적용 - 시뮬레이션 시작 시점)
        self.initial_quintiles: Dict[int, int] = {}   # household_id -> initial quintile
        self.cohort_initialized: bool = False
        
        # 전이 행렬 (initial_quintile -> current_quintile -> count)
        self.transition_matrix: Dict[int, Dict[int, int]] = {
            i: {j: 0 for j in range(1, 6)} for i in range(1, 6)
        }
        
    def calculate_gini_coefficient(self, values: List[float]) -> float:
        """
        지니계수를 계산합니다.
        
        Args:
            values: 자산/소득 값 리스트
            
        Returns:
            지니계수 (0~1, 높을수록 불평등)
        """
        if not values or len(values) < 2:
            return 0.0
        
        n = len(values)
        sorted_values = sorted(values)
        
        # 모든 값이 0인 경우
        if sum(sorted_values) == 0:
            return 0.0
        
        # 지니계수 공식: G = (2 * sum(i * x_i) - (n+1) * sum(x_i)) / (n * sum(x_i))
        cumsum = sum((i + 1) * x for i, x in enumerate(sorted_values))
        total = sum(sorted_values)
        
        gini = (2 * cumsum - (n + 1) * total) / (n * total)
        return max(0.0, min(1.0, gini))
    
    def _assign_quintiles(self, households: List["Household"]) -> Dict[int, int]:
        """가계들에 분위를 할당합니다."""
        if not households:
            return {}
        
        sorted_households = sorted(households, key=lambda h: h.total_wealth)
        n = len(sorted_households)
        quintile_size = n // 5 if n >= 5 else 1
        
        quintiles: Dict[int, int] = {}
        for i, h in enumerate(sorted_households):
            quintile = min(5, i // quintile_size + 1) if quintile_size > 0 else 1
            quintiles[h.id] = quintile
        
        return quintiles
    
    def initialize_cohort(self, households: List["Household"]) -> None:
        """
        코호트 추적을 초기화합니다.
        시뮬레이션 시작 시점의 분위를 기록합니다.
        """
        self.initial_quintiles = self._assign_quintiles(households)
        self.cohort_initialized = True
        self.transition_matrix = {
            i: {j: 0 for j in range(1, 6)} for i in range(1, 6)
        }
        
        logger.info(
            f"Cohort initialized with {len(households)} households",
            extra={"tags": ["inequality", "cohort"]}
        )
    
    def calculate_quintile_distribution(
        self, households: List["Household"]
    ) -> Dict[str, Any]:
        """
        자산 기준 5분위 분포를 계산합니다.
        
        Returns:
            분위별 가계 수, 평균 자산, 점유율
        """
        if not households:
            return {}
        
        # 자산 순으로 정렬
        sorted_households = sorted(households, key=lambda h: h.total_wealth)
        n = len(sorted_households)
        quintile_size = n // 5
        
        quintiles: Dict[int, List["Household"]] = {i: [] for i in range(1, 6)}
        
        for i, h in enumerate(sorted_households):
            quintile = min(5, i // quintile_size + 1) if quintile_size > 0 else 1
            quintiles[quintile].append(h)
        
        # 분위별 통계 계산
        total_assets = sum(h.total_wealth for h in households)
        result: Dict[str, Any] = {}
        
        for q in range(1, 6):
            q_households = quintiles[q]
            q_assets = sum(h.total_wealth for h in q_households)
            
            result[f"quintile_{q}_count"] = len(q_households)
            result[f"quintile_{q}_avg_assets"] = (
                q_assets / len(q_households) if q_households else 0.0
            )
            result[f"quintile_{q}_wealth_share"] = (
                q_assets / total_assets if total_assets > 0 else 0.0
            )
        
        return result
    
    def calculate_social_mobility(
        self, households: List["Household"]
    ) -> Dict[str, Any]:
        """
        계층 이동 지표를 계산합니다 (틱 간 단기 이동).
        
        Returns:
            상향/하향/유지 이동 수, 이동성 지수
        """
        if not households:
            return {
                "upward_mobility_count": 0,
                "downward_mobility_count": 0,
                "stable_count": 0,
                "mobility_index": 0.0,
            }
        
        current_quintiles = self._assign_quintiles(households)
        
        # 이동 계산
        upward = 0
        downward = 0
        stable = 0
        
        for h_id, current_q in current_quintiles.items():
            prev_q = self.previous_quintiles.get(h_id)
            
            if prev_q is None:
                stable += 1  # 첫 틱
            elif current_q > prev_q:
                upward += 1
            elif current_q < prev_q:
                downward += 1
            else:
                stable += 1
        
        # 이동성 지수: (상향 + 하향) / 총 가계 수
        total = len(households)
        mobility_index = (upward + downward) / total if total > 0 else 0.0
        
        # 현재 분위 저장 (다음 틱 비교용)
        self.previous_quintiles = current_quintiles.copy()
        
        return {
            "upward_mobility_count": upward,
            "downward_mobility_count": downward,
            "stable_count": stable,
            "mobility_index": mobility_index,
        }
    
    def calculate_longitudinal_mobility(
        self, households: List["Household"]
    ) -> Dict[str, Any]:
        """
        코호트 기반 종단 계층 이동을 계산합니다.
        초기 분위에서 현재 분위로의 이동을 추적합니다.
        
        Returns:
            - 초기 하위층(1-2분위) → 현재 상위층(4-5분위) 상승 수
            - 초기 상위층(4-5분위) → 현재 하위층(1-2분위) 하락 수
            - 전이 행렬
        """
        if not households or not self.cohort_initialized:
            return {
                "bottom_to_top_count": 0,
                "top_to_bottom_count": 0,
                "bottom_to_top_rate": 0.0,
                "top_to_bottom_rate": 0.0,
                "transition_matrix": {},
            }
        
        current_quintiles = self._assign_quintiles(households)
        
        # 전이 행렬 초기화
        self.transition_matrix = {
            i: {j: 0 for j in range(1, 6)} for i in range(1, 6)
        }
        
        # 종단 이동 계산
        bottom_to_top = 0  # 초기 1-2분위 → 현재 4-5분위
        top_to_bottom = 0  # 초기 4-5분위 → 현재 1-2분위
        
        initial_bottom_count = 0  # 초기 하위층 총 수
        initial_top_count = 0      # 초기 상위층 총 수
        
        for h_id, current_q in current_quintiles.items():
            initial_q = self.initial_quintiles.get(h_id)
            
            if initial_q is None:
                continue  # 시뮬레이션 중간에 추가된 가계
            
            # 전이 행렬 업데이트
            self.transition_matrix[initial_q][current_q] += 1
            
            # 하위층 → 상위층
            if initial_q <= 2:
                initial_bottom_count += 1
                if current_q >= 4:
                    bottom_to_top += 1
            
            # 상위층 → 하위층
            if initial_q >= 4:
                initial_top_count += 1
                if current_q <= 2:
                    top_to_bottom += 1
        
        # 비율 계산
        bottom_to_top_rate = (
            bottom_to_top / initial_bottom_count 
            if initial_bottom_count > 0 else 0.0
        )
        top_to_bottom_rate = (
            top_to_bottom / initial_top_count 
            if initial_top_count > 0 else 0.0
        )
        
        return {
            "bottom_to_top_count": bottom_to_top,
            "top_to_bottom_count": top_to_bottom,
            "bottom_to_top_rate": bottom_to_top_rate,
            "top_to_bottom_rate": top_to_bottom_rate,
            "initial_bottom_count": initial_bottom_count,
            "initial_top_count": initial_top_count,
            "transition_matrix": self.transition_matrix,
        }
    
    def get_transition_probability_matrix(self) -> Dict[int, Dict[int, float]]:
        """
        전이 확률 행렬을 반환합니다.
        각 초기 분위에서 다른 분위로 이동할 확률을 계산합니다.
        """
        prob_matrix: Dict[int, Dict[int, float]] = {}
        
        for initial_q in range(1, 6):
            row = self.transition_matrix.get(initial_q, {})
            row_total = sum(row.values())
            
            prob_matrix[initial_q] = {}
            for current_q in range(1, 6):
                count = row.get(current_q, 0)
                prob_matrix[initial_q][current_q] = (
                    count / row_total if row_total > 0 else 0.0
                )
        
        return prob_matrix
    
    def calculate_wealth_distribution(
        self,
        households: List["Household"],
        stock_market: Optional["StockMarket"] = None,
    ) -> Dict[str, Any]:
        """
        부의 분배 종합 지표를 계산합니다.
        """
        if not households:
            return {}
        
        # 코호트 초기화 (첫 호출 시)
        if not self.cohort_initialized:
            self.initialize_cohort(households)
        
        # 자산 데이터 수집
        total_assets = [h.total_wealth for h in households]
        
        # 금융자산 (현금 + 주식 포트폴리오 가치)
        financial_assets = []
        stock_holdings = []
        
        for h in households:
            portfolio_value = 0.0
            total_shares = 0.0
            
            if stock_market is not None:
                # Use portfolio directly
                for firm_id, holding in h._econ_state.portfolio.holdings.items():
                    shares = holding.quantity
                    price = stock_market.get_stock_price(firm_id) or 0.0
                    portfolio_value += shares * price
                    total_shares += shares
            
            # Use total_wealth instead of _econ_state.assets (dict)
            financial_assets.append(h.total_wealth + portfolio_value)
            stock_holdings.append(portfolio_value)
        
        # 분위 계산
        quintile_data = self.calculate_quintile_distribution(households)
        mobility_data = self.calculate_social_mobility(households)
        longitudinal_data = self.calculate_longitudinal_mobility(households)
        
        # 평균/중위 계산
        mean_assets = sum(total_assets) / len(total_assets)
        median_assets = median(total_assets)
        
        return {
            "gini_total_assets": self.calculate_gini_coefficient(total_assets),
            "gini_financial_assets": self.calculate_gini_coefficient(financial_assets),
            "gini_stock_holdings": self.calculate_gini_coefficient(stock_holdings),
            "top_10_pct_wealth_share": self._calculate_top_percentile_share(total_assets, 0.1),
            "bottom_50_pct_wealth_share": self._calculate_bottom_percentile_share(total_assets, 0.5),
            "mean_household_assets": mean_assets,
            "median_household_assets": median_assets,
            "mean_to_median_ratio": mean_assets / median_assets if median_assets > 0 else 1.0,
            **quintile_data,
            **mobility_data,
            **longitudinal_data,
        }
    
    def _calculate_top_percentile_share(
        self, values: List[float], percentile: float
    ) -> float:
        """상위 X%의 자산 점유율을 계산합니다."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values, reverse=True)
        n = len(sorted_values)
        top_n = max(1, int(n * percentile))
        
        top_sum = sum(sorted_values[:top_n])
        total_sum = sum(values)
        
        return top_sum / total_sum if total_sum > 0 else 0.0
    
    def _calculate_bottom_percentile_share(
        self, values: List[float], percentile: float
    ) -> float:
        """하위 X%의 자산 점유율을 계산합니다."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        bottom_n = max(1, int(n * percentile))
        
        bottom_sum = sum(sorted_values[:bottom_n])
        total_sum = sum(values)
        
        return bottom_sum / total_sum if total_sum > 0 else 0.0

