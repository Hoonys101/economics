from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union, TypedDict
from modules.simulation.dtos.api import FirmStateDTO, HouseholdConfigDTO, FirmConfigDTO
from simulation.models import Order
from simulation.dtos.decision_dtos import DecisionOutputDTO
from modules.finance.api import IFinancialAgent
from modules.simulation.api import AgentID
from modules.governance.api import SystemCommand
from simulation.dtos.commands import GodCommandDTO

# Renamed to enforce explicit usage of CanonicalOrderDTO vs Legacy Order
LegacySimulationOrder = Order
# Deprecated alias kept for backward compatibility until all consumers are updated
OrderDTO = Order


if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.dtos.scenario import StressScenarioConfig
    from modules.household.dtos import HouseholdStateDTO

@dataclass
class TransactionData:
    run_id: int
    time: int
    buyer_id: AgentID
    seller_id: AgentID
    item_id: str
    quantity: float
    price: float
    total_pennies: int # Added for Reporting DTO Hardening
    currency: CurrencyCode  # Added for Phase 33
    market_id: str
    transaction_type: str

@dataclass
class AgentStateData:
    run_id: int
    time: int
    agent_id: AgentID
    agent_type: str
    assets: Dict[CurrencyCode, int] # Changed for Phase 33 (Hardened to int)
    is_active: bool
    is_employed: Optional[bool] = None
    employer_id: Optional[AgentID] = None
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
    market_insight: Optional[float] = 0.5 # Phase 4.1: Perception & Adaptive Logic

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
    total_consumption: Optional[int] = None
    total_household_assets: Optional[int] = None # Changed for Reporting DTO Hardening (Pennies)
    total_firm_assets: Optional[int] = None # Changed for Reporting DTO Hardening (Pennies)
    total_food_consumption: Optional[int] = None
    total_inventory: Optional[float] = None
    avg_survival_need: Optional[float] = None
    total_labor_income: Optional[int] = None # Changed for Reporting DTO Hardening (Pennies)
    total_capital_income: Optional[int] = None # Changed for Reporting DTO Hardening (Pennies)
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
    agent_id: AgentID
    decision_type: str
    decision_details: Optional[Dict[str, Any]] = None
    predicted_reward: Optional[float] = None
    actual_reward: Optional[float] = None

class GoodsDTO(TypedDict, total=False):
    id: str
    name: str
    category: str
    is_durable: bool
    is_essential: bool
    initial_price: int
    base_need_satisfaction: float
    quality_modifier: float
    # Fields from goods.json
    type: str
    satiety: float
    decay_rate: float

class MarketHistoryDTO(TypedDict, total=False):
    avg_price: float
    trade_volume: float
    best_ask: int
    best_bid: int
    avg_ask: float
    avg_bid: float
    worst_ask: int
    worst_bid: int

# Phase 1: MarketSnapshotDTO moved to modules.system.api
from modules.system.api import (
    CurrencyCode, # Added for Phase 33
    MarketSnapshotDTO,
    HousingMarketSnapshotDTO,
    LoanMarketSnapshotDTO,
    LaborMarketSnapshotDTO,
    HousingMarketUnitDTO,
    MarketContextDTO # Refactored to TypedDict in modules.system.api
)
# Phase 1: EconomicIndicatorsDTO from modules.simulation.api
from modules.simulation.api import EconomicIndicatorsDTO

@dataclass
class GovernmentPolicyDTO:
    """A pure-data snapshot of current government policies affecting agent decisions."""
    income_tax_rate: float
    sales_tax_rate: float
    corporate_tax_rate: float
    base_interest_rate: float
    
    # Phase 4.1: Macro & Sentiment Metrics
    system_debt_to_gdp_ratio: float = 0.0
    system_liquidity_index: float = 1.0
    market_panic_index: float = 0.0
    fiscal_stance_indicator: str = "NEUTRAL" # "EXPANSION", "NEUTRAL", "AUSTERITY"

@dataclass
class DecisionInputDTO:
    """
    Standardized input DTO for agent decision-making.
    Encapsulates all external system inputs passed to make_decision.
    """
    market_snapshot: MarketSnapshotDTO
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    fiscal_context: Optional[FiscalContext] = None
    macro_context: Optional[MacroFinancialContext] = None
    stress_scenario_config: Optional[Any] = None # Avoid circular import with StressScenarioConfig if possible, or use forward ref
    government_policy: Optional[GovernmentPolicyDTO] = None
    agent_registry: Optional[Dict[str, int]] = None
    housing_system: Optional[Any] = None # Added for Saga initiation
    market_context: Optional[MarketContextDTO] = None


@dataclass
class DecisionContext:
    """
    A pure data container for decision-making.
    Direct agent instance access is strictly forbidden (Enforced by Purity Gate).
    """
    goods_data: List[GoodsDTO]
    market_data: Dict[str, MarketHistoryDTO]
    current_time: int
    
    # State DTO representing the agent's current condition
    state: Union[HouseholdStateDTO, FirmStateDTO]
    
    # Static configuration values relevant to the agent type
    config: Union[HouseholdConfigDTO, FirmConfigDTO]

    # New DTOs
    market_snapshot: Optional[MarketSnapshotDTO] = None
    government_policy: Optional[GovernmentPolicyDTO] = None

    stress_scenario_config: Optional[StressScenarioConfig] = None # Phase 28

    # Agent Discovery Registry (WO-138)
    agent_registry: Dict[str, AgentID] = field(default_factory=dict)

    # Tick-Snapshot Injection
    market_context: Optional[MarketContextDTO] = None


@dataclass
class FiscalContext:
    """
    Context providing access to fiscal entities (Government) in a restricted manner.
    Used by agents to interact with the government (e.g., paying taxes, receiving subsidies)
    without direct access to the full Government agent object.
    """
    government: IFinancialAgent


@dataclass
class SimulationState:
    """
    WO-103: Simulation State DTO to reduce coupling.
    Passes all necessary data from the Simulation object to system services.
    """
    time: int
    households: List[Household]
    firms: List[Firm]
    agents: Dict[AgentID, Any]
    markets: Dict[str, Any]
    primary_government: Any  # Renamed from government for clarity
    governments: List[Any] # TD-ARCH-GOV-MISMATCH: Added for alignment
    bank: Any        # Bank
    central_bank: Any # CentralBank
    escrow_agent: Optional[Any] # EscrowAgent
    stock_market: Optional[Any] # StockMarket
    stock_tracker: Optional[Any] # Added for WO-133 Fix
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
    inter_tick_queue: List[Any] = None # List[Transaction]
    effects_queue: List[Dict[str, Any]] = None # WO-109: Queue for side-effects
    inactive_agents: Dict[AgentID, Any] = None # WO-109: Store inactive agents
    taxation_system: Optional[Any] = None # WO-116: Taxation System
    currency_holders: List[Any] = None # Added for M2 tracking (Phase 33/5)
    stress_scenario_config: Optional[StressScenarioConfig] = None # Phase 28
    transaction_processor: Optional[Any] = None # Added for system delegation compatibility
    shareholder_registry: Optional[Any] = None # TD-275 Shareholder Registry
    housing_service: Optional[Any] = None # Phase 4.1: Housing Saga Fix
    registry: Optional[Any] = None # Standard Domain Registry

    # Phase 4.1: Saga Orchestration & Monetary Ledger (TD-253)
    saga_orchestrator: Optional[Any] = None
    monetary_ledger: Optional[Any] = None

    # TD-255: System Command Pipeline
    system_commands: List[SystemCommand] = field(default_factory=list)
    god_command_snapshot: List[GodCommandDTO] = field(default_factory=list) # Renamed from god_commands

    # --- NEW TRANSIENT FIELDS ---
    # From Phase 1 (Decisions)
    firm_pre_states: Dict[AgentID, Any] = None
    household_pre_states: Dict[AgentID, Any] = None
    household_time_allocation: Dict[AgentID, float] = None

    # From Commerce System (planned in Phase 1, used in PostSequence)
    planned_consumption: Optional[Dict[AgentID, Dict[str, Any]]] = None # TD-118

    # From Lifecycle (used in PostSequence for Learning)
    household_leisure_effects: Dict[AgentID, float] = None

    # Injection
    injectable_sensory_dto: Optional[Any] = None # GovernmentStateDTO
    currency_registry_handler: Optional[Any] = None # WorldState injection for strict registry

    def register_currency_holder(self, holder: Any) -> None:
        if self.currency_registry_handler:
            self.currency_registry_handler.register_currency_holder(holder)
        elif self.currency_holders is not None:
             self.currency_holders.append(holder) # Fallback

    def unregister_currency_holder(self, holder: Any) -> None:
        if self.currency_registry_handler:
            self.currency_registry_handler.unregister_currency_holder(holder)
        elif self.currency_holders is not None:
             if holder in self.currency_holders:
                 self.currency_holders.remove(holder) # Fallback

    def __post_init__(self):
        if self.transactions is None:
            self.transactions = []
        if self.system_commands is None:
            self.system_commands = []
        if self.god_command_snapshot is None:
            self.god_command_snapshot = []
        if self.inter_tick_queue is None:
            self.inter_tick_queue = []
        if self.effects_queue is None:
            self.effects_queue = []
        if self.inactive_agents is None:
            self.inactive_agents = {}
        if self.currency_holders is None:
            self.currency_holders = []
        if self.firm_pre_states is None:
            self.firm_pre_states = {}
        if self.household_pre_states is None:
            self.household_pre_states = {}
        if self.household_time_allocation is None:
            self.household_time_allocation = {}
        if self.planned_consumption is None:
            self.planned_consumption = {}
        if self.household_leisure_effects is None:
            self.household_leisure_effects = {}


# ------------------------------------------------------------------------------
# 주식 시장 및 경제 분석 DTO
# ------------------------------------------------------------------------------

@dataclass
class StockMarketHistoryData:
    """주식 시장 틱별 이력 (기업별)"""
    run_id: int
    time: int
    firm_id: AgentID
    
    # 주가 관련
    stock_price: int                # 현재 주가 (거래가 또는 기준가) [Pennies]
    book_value_per_share: float     # 주당 순자산가치 (BPS)
    price_to_book_ratio: float      # PBR (주가/BPS)
    
    # 거래 관련
    trade_volume: float             # 거래량
    buy_order_count: int            # 매수 주문 수
    sell_order_count: int           # 매도 주문 수
    
    # 기업 실적 연계
    firm_assets: int                # 기업 총자산 [Pennies]
    firm_profit: int                # 기업 이익 (당기) [Pennies]
    dividend_paid: int              # 배당금 지급액 [Pennies]
    market_cap: int                 # 시가총액 [Pennies]


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
    household_id: AgentID
    
    labor_income: int               # 노동 소득 (임금) [Pennies]
    dividend_income: int            # 배당 소득 [Pennies]
    capital_gains: int              # 주식 매매 차익 [Pennies]
    total_income: int               # 총 소득 [Pennies]
    
    portfolio_value: int            # 포트폴리오 가치 [Pennies]
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
    agent_id: AgentID
    generation: int
    parent_id: Optional[AgentID]
    children_ids: List[AgentID]
    children_avg_xp: float = 0.0  # 자녀들의 평균 지능


@dataclass
class LeisureEffectDTO:
    """여가 활동의 결과"""
    leisure_type: LeisureType
    leisure_hours: float
    utility_gained: float       # 사회적 만족
    xp_gained: float           # 자녀 XP 증가 (Parenting) 또는 본인 생산성 (Self-Dev)

@dataclass
class GovernmentSensoryDTO:
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
    # WO-057-A: Added for AdaptiveGovBrain
    gini_index: float = 0.0
    approval_low_asset: float = 0.5
    approval_high_asset: float = 0.5

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
@dataclass
class JobOfferDTO:
    """Firm's labor demand signaling."""
    firm_id: AgentID
    offer_wage: float
    required_education: int = 0
    quantity: float = 1.0

@dataclass
class JobSeekerDTO:
    """Household's labor supply signaling (Signaling Game)."""
    household_id: AgentID
    reservation_wage: float
    education_level: int
    # Note: labor_skill is hidden from the market per Architect's directive.
    quantity: float = 1.0
