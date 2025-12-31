from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm

@dataclass
class TransactionData:
    run_id: int
    time: int
    buyer_id: int
    seller_id: int
    item_id: str
    quantity: float
    price: float
    market_id: str
    transaction_type: str

@dataclass
class AgentStateData:
    run_id: int
    time: int
    agent_id: int
    agent_type: str
    assets: float
    is_active: bool
    is_employed: Optional[bool] = None
    employer_id: Optional[int] = None
    needs_survival: Optional[float] = None
    needs_labor: Optional[float] = None
    inventory_food: Optional[float] = None
    current_production: Optional[float] = None
    num_employees: Optional[int] = None
    education_xp: Optional[float] = None
    generation: Optional[int] = 0
    # Experiment: Time Allocation Tracking
    time_worked: Optional[float] = None
    time_leisure: Optional[float] = None

@dataclass
class EconomicIndicatorData:
    run_id: int
    time: int
    unemployment_rate: Optional[float] = None
    avg_wage: Optional[float] = None
    food_avg_price: Optional[float] = None
    food_trade_volume: Optional[float] = None
    avg_goods_price: Optional[float] = None
    total_production: Optional[float] = None
    total_consumption: Optional[float] = None
    total_household_assets: Optional[float] = None
    total_firm_assets: Optional[float] = None
    total_food_consumption: Optional[float] = None
    total_inventory: Optional[float] = None
    avg_survival_need: Optional[float] = None

@dataclass
class MarketHistoryData:
    time: int
    market_id: str
    item_id: Optional[str] = None
    avg_price: Optional[float] = None
    trade_volume: Optional[float] = None
    best_ask: Optional[float] = None
    best_bid: Optional[float] = None
    avg_ask: Optional[float] = None
    avg_bid: Optional[float] = None
    worst_ask: Optional[float] = None
    worst_bid: Optional[float] = None

@dataclass
class AIDecisionData:
    run_id: int
    tick: int
    agent_id: int
    decision_type: str
    decision_details: Optional[Dict[str, Any]] = None
    predicted_reward: Optional[float] = None
    actual_reward: Optional[float] = None

@dataclass
class DecisionContext:

    markets: Dict[str, Any]
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    household: Optional[Household] = None # Avoid circular import if possible, or use TYPE_CHECKING
    firm: Optional[Firm] = None
    government: Optional[Any] = None


# ------------------------------------------------------------------------------
# 주식 시장 및 경제 분석 DTO
# ------------------------------------------------------------------------------

@dataclass
class StockMarketHistoryData:
    """주식 시장 틱별 이력 (기업별)"""
    run_id: int
    time: int
    firm_id: int
    
    # 주가 관련
    stock_price: float              # 현재 주가 (거래가 또는 기준가)
    book_value_per_share: float     # 주당 순자산가치 (BPS)
    price_to_book_ratio: float      # PBR (주가/BPS)
    
    # 거래 관련
    trade_volume: float             # 거래량
    buy_order_count: int            # 매수 주문 수
    sell_order_count: int           # 매도 주문 수
    
    # 기업 실적 연계
    firm_assets: float              # 기업 총자산
    firm_profit: float              # 기업 이익 (당기)
    dividend_paid: float            # 배당금 지급액
    market_cap: float               # 시가총액


@dataclass
class WealthDistributionData:
    """부의 분배 지표 (틱별)"""
    run_id: int
    time: int
    
    # 자산 분배 (지니계수)
    gini_total_assets: float        # 총자산 지니계수
    gini_financial_assets: float    # 금융자산 지니계수 (현금 + 주식)
    gini_stock_holdings: float      # 주식 보유 지니계수
    
    # 소득 분배
    labor_income_share: float       # 노동소득 비율 (노동소득 / 총소득)
    capital_income_share: float     # 자본소득 비율 (배당 + 주식차익 / 총소득)
    
    # 분위별 자산
    top_10_pct_wealth_share: float  # 상위 10% 자산 점유율
    bottom_50_pct_wealth_share: float # 하위 50% 자산 점유율
    
    # 평균/중위 비교
    mean_household_assets: float
    median_household_assets: float
    mean_to_median_ratio: float     # 불평등 지표 (>1이면 불평등)


@dataclass
class HouseholdIncomeData:
    """가계별 소득 원천 추적"""
    run_id: int
    time: int
    household_id: int
    
    labor_income: float             # 노동 소득 (임금)
    dividend_income: float          # 배당 소득
    capital_gains: float            # 주식 매매 차익
    total_income: float             # 총 소득
    
    portfolio_value: float          # 포트폴리오 가치
    portfolio_return_rate: float    # 투자 수익률


@dataclass
class SocialMobilityData:
    """계층 이동 지표 (틱별)"""
    run_id: int
    time: int
    
    # 계층 구분 (자산 기준 5분위)
    quintile_1_count: int           # 1분위 (하위 20%) 가계 수
    quintile_2_count: int           # 2분위 가계 수
    quintile_3_count: int           # 3분위 가계 수
    quintile_4_count: int           # 4분위 가계 수
    quintile_5_count: int           # 5분위 (상위 20%) 가계 수
    
    # 계층 이동 (이전 틱 대비)
    upward_mobility_count: int      # 상향 이동 가계 수
    downward_mobility_count: int    # 하향 이동 가계 수
    stable_count: int               # 유지 가계 수
    
    # 분위별 평균 자산
    quintile_1_avg_assets: float
    quintile_2_avg_assets: float
    quintile_3_avg_assets: float
    quintile_4_avg_assets: float
    quintile_5_avg_assets: float
    
    # 계층 고착도 (동일 분위 유지 비율)
    mobility_index: float           # 이동성 지수 (0~1, 높을수록 유동적)


@dataclass
class PersonalityStatisticsData:
    """성향별 통계 (틱별)"""
    run_id: int
    time: int
    personality_type: str           # "MISER", "STATUS_SEEKER", "GROWTH_ORIENTED"
    
    # 기본 통계
    count: int                      # 해당 성향 가계 수
    avg_assets: float               # 평균 자산
    median_assets: float            # 중위 자산
    
    # 소득 구조
    avg_labor_income: float         # 평균 노동 소득
    avg_capital_income: float       # 평균 자본 소득 (배당 + 차익)
    labor_income_ratio: float       # 노동소득 비율
    
    # 고용 및 투자
    employment_rate: float          # 고용률
    avg_portfolio_value: float      # 평균 포트폴리오 가치
    avg_stock_holdings: float       # 평균 주식 보유량
    
    # 욕구 충족
    avg_survival_need: float        # 평균 생존 욕구
    avg_social_need: float          # 평균 사회적 욕구
    avg_improvement_need: float     # 평균 성장 욕구
    
    # 성과 지표
    avg_wealth_growth_rate: float   # 평균 자산 증가율
@dataclass
class DashboardGlobalIndicatorsDTO:
    death_rate: float
    bankruptcy_rate: float
    employment_rate: float
    gdp: float
    avg_wage: float
    gini: float

@dataclass
class GenerationStatDTO:
    gen: int
    count: int
    avg_assets: float

@dataclass
class SocietyTabDataDTO:
    generations: List[GenerationStatDTO]
    mitosis_cost: float
    unemployment_pie: Dict[str, int] # e.g., {"struggling": 80, "voluntary": 20}

@dataclass
class GovernmentTabDataDTO:
    tax_revenue: Dict[str, float]
    fiscal_balance: Dict[str, float]

@dataclass
class MarketTabDataDTO:
    commodity_volumes: Dict[str, float]
    cpi: List[float]
    maslow_fulfillment: List[float]

@dataclass
class FinanceTabDataDTO:
    market_cap: float
    volume: float
    turnover: float
    dividend_yield: float

@dataclass
class DashboardSnapshotDTO:
    tick: int
    global_indicators: DashboardGlobalIndicatorsDTO
    tabs: Dict[str, Any] # Or specific classes for each tab


# ==============================================================================
# Phase 5: Time Allocation & Genealogy DTOs
# ==============================================================================
from typing import Literal

LeisureType = Literal["PARENTING", "SELF_DEV", "ENTERTAINMENT", "IDLE"]

@dataclass
class TimeBudgetDTO:
    """한 틱(24시간) 동안의 시간 배분 결과"""
    total_hours: float = 24.0
    work_hours: float = 0.0
    leisure_hours: float = 0.0
    selected_leisure_type: LeisureType = "IDLE"
    efficiency_multiplier: float = 1.0  # 도구(재화) 사용에 따른 효율


@dataclass
class FamilyInfoDTO:
    """가계의 가족 관계 정보 (AI 의사결정용 입력)"""
    agent_id: int
    generation: int
    parent_id: Optional[int]
    children_ids: List[int]
    children_avg_xp: float = 0.0  # 자녀들의 평균 지능


@dataclass
class LeisureEffectDTO:
    """여가 활동의 결과"""
    leisure_type: LeisureType
    leisure_hours: float
    utility_gained: float       # 사회적 만족
    xp_gained: float           # 자녀 XP 증가 (Parenting) 또는 본인 생산성 (Self-Dev)
