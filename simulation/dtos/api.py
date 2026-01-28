from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union
from simulation.dtos.firm_state_dto import FirmStateDTO
from simulation.models import Order

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.dtos.scenario import StressScenarioConfig
    from modules.household.dtos import HouseholdStateDTO

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
    total_labor_income: Optional[float] = None
    total_capital_income: Optional[float] = None
    # Phase 23: Education & Opportunity Metrics
    avg_education_level: Optional[float] = None
    education_spending: Optional[float] = None
    education_coverage: Optional[float] = None
    brain_waste_count: Optional[int] = None

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
class MarketSnapshotDTO:
    """A pure-data snapshot of the state of all markets at a point in time."""
    prices: Dict[str, float]
    volumes: Dict[str, float]
    asks: Dict[str, List[Order]]
    best_asks: Dict[str, float]

@dataclass
class GovernmentPolicyDTO:
    """A pure-data snapshot of current government policies affecting agent decisions."""
    income_tax_rate: float
    sales_tax_rate: float
    corporate_tax_rate: float
    base_interest_rate: float

@dataclass
class HouseholdConfigDTO:
    """Static configuration values relevant to household decisions."""
    survival_need_consumption_threshold: float
    target_food_buffer_quantity: float
    food_purchase_max_per_tick: float
    assets_threshold_for_other_actions: float
    wage_decay_rate: float
    reservation_wage_floor: float
    survival_critical_turns: float
    labor_market_min_wage: float
    # New from Household.make_decision refactoring
    household_low_asset_threshold: float
    household_low_asset_wage: float
    household_default_wage: float
    
    # AI Engine requirements
    market_price_fallback: float
    need_factor_base: float
    need_factor_scale: float
    valuation_modifier_base: float
    valuation_modifier_range: float
    household_max_purchase_quantity: float
    bulk_buy_need_threshold: float
    bulk_buy_agg_threshold: float
    bulk_buy_moderate_ratio: float
    panic_buying_threshold: float
    hoarding_factor: float
    deflation_wait_threshold: float
    delay_factor: float
    dsr_critical_threshold: float
    budget_limit_normal_ratio: float
    budget_limit_urgent_need: float
    budget_limit_urgent_ratio: float
    min_purchase_quantity: float
    job_quit_threshold_base: float
    job_quit_prob_base: float
    job_quit_prob_scale: float
    stock_market_enabled: bool
    household_min_assets_for_investment: float
    stock_investment_equity_delta_threshold: float
    stock_investment_diversification_count: int
    expected_startup_roi: float
    startup_cost: float
    debt_repayment_ratio: float
    debt_repayment_cap: float
    debt_liquidity_ratio: float
    # Added for parity
    initial_rent_price: float
    # Added for AI Engine Purity
    default_mortgage_rate: float
    # Housing Manager
    enable_vanity_system: bool
    mimicry_factor: float
    maintenance_rate_per_tick: float

@dataclass
class FirmConfigDTO:
    """Static configuration values relevant to firm decisions."""
    firm_min_production_target: float
    firm_max_production_target: float
    startup_cost: float
    seo_trigger_ratio: float
    seo_max_sell_ratio: float
    automation_cost_per_pct: float
    firm_safety_margin: float
    automation_tax_rate: float
    altman_z_score_threshold: float
    dividend_suspension_loss_ticks: int
    dividend_rate_min: float
    dividend_rate_max: float
    labor_alpha: float
    automation_labor_reduction: float
    severance_pay_weeks: float
    labor_market_min_wage: float
    overstock_threshold: float
    understock_threshold: float
    production_adjustment_factor: float
    max_sell_quantity: float
    invisible_hand_sensitivity: float
    capital_to_output_ratio: float

@dataclass
class DecisionContext:
    """
    A pure data container for decision-making.
    Direct agent instance access is strictly forbidden (Enforced by Purity Gate).
    """
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    
    # State DTO representing the agent's current condition
    state: Union[HouseholdStateDTO, FirmStateDTO]
    
    # Static configuration values relevant to the agent type
    config: Union[HouseholdConfigDTO, FirmConfigDTO]

    # New DTOs
    market_snapshot: Optional[MarketSnapshotDTO] = None
    government_policy: Optional[GovernmentPolicyDTO] = None

    stress_scenario_config: Optional[StressScenarioConfig] = None # Phase 28


@dataclass
class SimulationState:
    """
    WO-103: Simulation State DTO to reduce coupling.
    Passes all necessary data from the Simulation object to system services.
    """
    time: int
    households: List[Household]
    firms: List[Firm]
    agents: Dict[int, Any]
    markets: Dict[str, Any]
    government: Any  # Government
    bank: Any        # Bank
    central_bank: Any # CentralBank
    stock_market: Optional[Any] # StockMarket
    goods_data: Dict[str, Any]
    market_data: Dict[str, Any] # Added for WO-103
    config_module: Any
    tracker: Any
    logger: Any # logging.Logger
    ai_training_manager: Optional[Any]
    ai_trainer: Optional[Any] # Added for WO-103
    settlement_system: Optional[Any] = None # WO-112: Settlement System
    next_agent_id: int = 0 # Added for WO-103
    real_estate_units: List[Any] = field(default_factory=list) # Added for WO-103
    # Mutable state for the tick
    transactions: List[Any] = None # List[Transaction]
    effects_queue: List[Dict[str, Any]] = None # WO-109: Queue for side-effects
    inactive_agents: Dict[int, Any] = None # WO-109: Store inactive agents
    planned_consumption: Optional[Dict[int, Dict[str, Any]]] = None # TD-118

    def __post_init__(self):
        if self.transactions is None:
            self.transactions = []
        if self.effects_queue is None:
            self.effects_queue = []
        if self.inactive_agents is None:
            self.inactive_agents = {}
        if self.planned_consumption is None:
            self.planned_consumption = {}


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
    # Phase 5 Additions
    avg_tax_rate: float
    avg_leisure_hours: float
    parenting_rate: float

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
    # Phase 5 Additions
    time_allocation: Dict[str, float] # e.g., {"WORK": 100, "PARENTING": 20}
    avg_leisure_hours: float
    # Phase 23: Opportunity Index
    avg_education_level: float
    brain_waste_count: int

@dataclass
class GovernmentTabDataDTO:
    tax_revenue: Dict[str, float] # Cumulative total
    fiscal_balance: Dict[str, float]
    # Phase 5 Additions
    tax_revenue_history: List[Dict[str, Any]] # Last 50 ticks breakdown
    welfare_spending: float
    current_avg_tax_rate: float
    welfare_history: List[Dict[str, float]] # Last 50 ticks spending
    # Phase 23: Education Spending
    education_spending: float
    education_history: List[Dict[str, float]] # Last 50 ticks spending

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

@dataclass
class GovernmentStateDTO:
    """
    WO-057-B: Sensory Module DTO.
    Transfers 10-tick SMA macro data to the Government Agent.
    """
    tick: int
    inflation_sma: float
    unemployment_sma: float
    gdp_growth_sma: float
    wage_sma: float
    approval_sma: float
    current_gdp: float

@dataclass
class MacroFinancialContext:
    """
    WO-062: Macro-Linked Portfolio Decisions.
    Transfers macro financial data to portfolio decision modules.
    This DTO is activated by the MACRO_PORTFOLIO_ADJUSTMENT_ENABLED flag.
    """
    inflation_rate: float
    gdp_growth_rate: float
    market_volatility: float
    interest_rate_trend: float


@dataclass
class LaborResult:
    """Represents the result of a household's labor activities for a tick."""
    hours_worked: float
    income_earned: float


@dataclass
class ConsumptionResult:
    """Represents the result of a household's consumption activities for a tick."""
    items_consumed: Dict[str, float]
    satisfaction: float
