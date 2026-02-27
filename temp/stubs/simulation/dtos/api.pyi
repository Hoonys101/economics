from _typeshed import Incomplete
from dataclasses import dataclass, field
from modules.finance.api import IFinancialAgent as IFinancialAgent
from modules.finance.kernel.api import IMonetaryLedger as IMonetaryLedger
from modules.government.dtos import GovernmentSensoryDTO as GovernmentSensoryDTO
from modules.government.politics_system import PoliticsSystem as PoliticsSystem
from modules.household.dtos import HouseholdStateDTO as HouseholdStateDTO
from modules.labor.api import JobOfferDTO as JobOfferDTO, JobSeekerDTO as JobSeekerDTO
from modules.simulation.api import AgentID as AgentID, EconomicIndicatorsDTO as EconomicIndicatorsDTO
from modules.simulation.dtos.api import FirmConfigDTO as FirmConfigDTO, FirmStateDTO as FirmStateDTO, HouseholdConfigDTO as HouseholdConfigDTO
from modules.system.api import CurrencyCode as CurrencyCode, HousingMarketSnapshotDTO as HousingMarketSnapshotDTO, HousingMarketUnitDTO as HousingMarketUnitDTO, LaborMarketSnapshotDTO as LaborMarketSnapshotDTO, LoanMarketSnapshotDTO as LoanMarketSnapshotDTO, MarketContextDTO as MarketContextDTO, MarketSnapshotDTO as MarketSnapshotDTO
from modules.system.command_pipeline.api import CommandBatchDTO
from simulation.core_agents import Household as Household
from simulation.dtos.decision_dtos import DecisionOutputDTO as DecisionOutputDTO
from simulation.dtos.scenario import StressScenarioConfig as StressScenarioConfig
from simulation.firms import Firm as Firm
from simulation.models import Order as Order
from typing import Any
from uuid import UUID

LegacySimulationOrder = Order
OrderDTO = Order

@dataclass(frozen=True)
class DepartmentContextDTO:
    """Module B: Context for firm-department orchestration."""
    parent_firm_id: AgentID
    department_type: str
    is_active: bool
    budget_pennies: int

@dataclass(frozen=True)
class SagaParticipantDTO:
    """Module C: Saga participant state for atomic rollbacks."""
    saga_id: UUID
    participant_id: AgentID
    state: str
    last_checkpoint_tick: int

@dataclass(frozen=True)
class MockFactoryDTO:
    """Module D: Testing infrastructure for decoupled mocks."""
    target_protocol: str
    mock_id: str
    behavior_config: dict[str, Any]

@dataclass
class TransactionData:
    run_id: int
    time: int
    buyer_id: AgentID
    seller_id: AgentID
    item_id: str
    quantity: float
    price: float
    total_pennies: int
    currency: CurrencyCode
    market_id: str
    transaction_type: str

@dataclass
class AgentStateData:
    run_id: int
    time: int
    agent_id: AgentID
    agent_type: str
    assets: dict[CurrencyCode, int]
    is_active: bool
    is_employed: bool | None = ...
    employer_id: AgentID | None = ...
    needs_survival: float | None = ...
    needs_labor: float | None = ...
    inventory_food: float | None = ...
    current_production: float | None = ...
    num_employees: int | None = ...
    education_xp: float | None = ...
    generation: int | None = ...
    time_worked: float | None = ...
    time_leisure: float | None = ...
    market_insight: float | None = ...

@dataclass
class EconomicIndicatorData:
    run_id: int
    time: int
    unemployment_rate: float | None = ...
    avg_wage: int | None = ...
    food_avg_price: int | None = ...
    food_trade_volume: float | None = ...
    avg_goods_price: int | None = ...
    total_production: float | None = ...
    total_consumption: int | None = ...
    total_household_assets: int | None = ...
    total_firm_assets: int | None = ...
    total_food_consumption: int | None = ...
    total_inventory: float | None = ...
    avg_survival_need: float | None = ...
    total_labor_income: int | None = ...
    total_capital_income: int | None = ...
    avg_education_level: float | None = ...
    education_spending: int | None = ...
    education_coverage: float | None = ...
    brain_waste_count: int | None = ...

@dataclass
class MarketHistoryData:
    time: int
    market_id: str
    item_id: str | None = ...
    avg_price: float | None = ...
    trade_volume: float | None = ...
    best_ask: float | None = ...
    best_bid: float | None = ...
    avg_ask: float | None = ...
    avg_bid: float | None = ...
    worst_ask: float | None = ...
    worst_bid: float | None = ...

@dataclass
class AIDecisionData:
    run_id: int
    tick: int
    agent_id: AgentID
    decision_type: str
    decision_details: dict[str, Any] | None = ...
    predicted_reward: float | None = ...
    actual_reward: float | None = ...

@dataclass(frozen=True)
class GoodsDTO:
    id: str
    name: str
    category: str
    is_durable: bool
    is_essential: bool
    initial_price: int
    base_need_satisfaction: float
    quality_modifier: float
    type: str
    satiety: float
    decay_rate: float

@dataclass(frozen=True)
class MarketHistoryDTO:
    avg_price: float
    trade_volume: float
    best_ask: int
    best_bid: int
    avg_ask: float
    avg_bid: float
    worst_ask: int
    worst_bid: int

@dataclass
class GovernmentPolicyDTO:
    """A pure-data snapshot of current government policies affecting agent decisions."""
    income_tax_rate: float
    sales_tax_rate: float
    corporate_tax_rate: float
    base_interest_rate: float
    system_debt_to_gdp_ratio: float = ...
    system_liquidity_index: float = ...
    market_panic_index: float = ...
    fiscal_stance_indicator: str = ...

@dataclass
class DecisionInputDTO:
    """
    Standardized input DTO for agent decision-making.
    Encapsulates all external system inputs passed to make_decision.
    """
    market_snapshot: MarketSnapshotDTO
    goods_data: list[dict[str, Any]]
    market_data: dict[str, Any]
    current_time: int
    fiscal_context: FiscalContext | None = ...
    macro_context: MacroFinancialContext | None = ...
    stress_scenario_config: Any | None = ...
    government_policy: GovernmentPolicyDTO | None = ...
    agent_registry: dict[str, int] | None = ...
    housing_system: Any | None = ...
    market_context: MarketContextDTO | None = ...

@dataclass
class DecisionContext:
    """
    A pure data container for decision-making.
    Direct agent instance access is strictly forbidden (Enforced by Purity Gate).
    """
    goods_data: list[GoodsDTO]
    market_data: dict[str, MarketHistoryDTO]
    current_time: int
    state: HouseholdStateDTO | FirmStateDTO
    config: HouseholdConfigDTO | FirmConfigDTO
    market_snapshot: MarketSnapshotDTO | None = ...
    government_policy: GovernmentPolicyDTO | None = ...
    stress_scenario_config: StressScenarioConfig | None = ...
    agent_registry: dict[str, AgentID] = field(default_factory=dict)
    market_context: MarketContextDTO | None = ...

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
    households: list[Household]
    firms: list[Firm]
    agents: dict[AgentID, Any]
    markets: dict[str, Any]
    primary_government: Any
    bank: Any
    central_bank: Any
    escrow_agent: Any | None
    stock_market: Any | None
    stock_tracker: Any | None
    goods_data: dict[str, Any]
    market_data: dict[str, Any]
    config_module: Any
    tracker: Any
    logger: Any
    ai_training_manager: Any | None
    ai_trainer: Any | None
    settlement_system: Any | None = ...
    next_agent_id: int = ...
    real_estate_units: list[Any] = field(default_factory=list)
    transactions: list[Any] | None = ...
    inter_tick_queue: list[Any] | None = ...
    effects_queue: list[dict[str, Any]] | None = ...
    inactive_agents: dict[AgentID, Any] | None = ...
    taxation_system: Any | None = ...
    currency_holders: list[Any] | None = ...
    stress_scenario_config: StressScenarioConfig | None = ...
    transaction_processor: Any | None = ...
    shareholder_registry: Any | None = ...
    housing_service: Any | None = ...
    registry: Any | None = ...
    saga_orchestrator: Any | None = ...
    monetary_ledger: IMonetaryLedger | None = ...
    command_batch: CommandBatchDTO | None = ...
    god_commands: list[GodCommandDTO] = field(default_factory=list)
    system_commands: list[Any] = field(default_factory=list)
    firm_pre_states: dict[AgentID, Any] | None = ...
    household_pre_states: dict[AgentID, Any] | None = ...
    household_time_allocation: dict[AgentID, float] | None = ...
    planned_consumption: dict[AgentID, dict[str, Any]] | None = ...
    household_leisure_effects: dict[AgentID, float] | None = ...
    injectable_sensory_dto: Any | None = ...
    currency_registry_handler: Any | None = ...
    public_manager: Any | None = ...
    politics_system: PoliticsSystem | None = ...
    def __post_init__(self) -> None: ...

@dataclass
class StockMarketHistoryData:
    """주식 시장 틱별 이력 (기업별)"""
    run_id: int
    time: int
    firm_id: AgentID
    stock_price: int
    book_value_per_share: float
    price_to_book_ratio: float
    trade_volume: float
    buy_order_count: int
    sell_order_count: int
    firm_assets: int
    firm_profit: int
    dividend_paid: int
    market_cap: int

@dataclass
class WealthDistributionData:
    """부의 분배 지표 (틱별)"""
    run_id: int
    time: int
    gini_total_assets: float
    gini_financial_assets: float
    gini_stock_holdings: float
    labor_income_share: float
    capital_income_share: float
    top_10_pct_wealth_share: float
    bottom_50_pct_wealth_share: float
    mean_household_assets: float
    median_household_assets: float
    mean_to_median_ratio: float

@dataclass
class HouseholdIncomeData:
    """가계별 소득 원천 추적"""
    run_id: int
    time: int
    household_id: AgentID
    labor_income: int
    dividend_income: int
    capital_gains: int
    total_income: int
    portfolio_value: int
    portfolio_return_rate: float

@dataclass
class SocialMobilityData:
    """계층 이동 지표 (틱별)"""
    run_id: int
    time: int
    quintile_1_count: int
    quintile_2_count: int
    quintile_3_count: int
    quintile_4_count: int
    quintile_5_count: int
    upward_mobility_count: int
    downward_mobility_count: int
    stable_count: int
    quintile_1_avg_assets: float
    quintile_2_avg_assets: float
    quintile_3_avg_assets: float
    quintile_4_avg_assets: float
    quintile_5_avg_assets: float
    mobility_index: float

@dataclass
class PersonalityStatisticsData:
    """성향별 통계 (틱별)"""
    run_id: int
    time: int
    personality_type: str
    count: int
    avg_assets: float
    median_assets: float
    avg_labor_income: float
    avg_capital_income: float
    labor_income_ratio: float
    employment_rate: float
    avg_portfolio_value: float
    avg_stock_holdings: float
    avg_survival_need: float
    avg_social_need: float
    avg_improvement_need: float
    avg_wealth_growth_rate: float

LeisureType: Incomplete

@dataclass
class TimeBudgetDTO:
    """한 틱(24시간) 동안의 시간 배분 결과"""
    total_hours: float = ...
    work_hours: float = ...
    leisure_hours: float = ...
    selected_leisure_type: LeisureType = ...
    efficiency_multiplier: float = ...

@dataclass
class FamilyInfoDTO:
    """가계의 가족 관계 정보 (AI 의사결정용 입력)"""
    agent_id: AgentID
    generation: int
    parent_id: AgentID | None
    children_ids: list[AgentID]
    children_avg_xp: float = ...

@dataclass
class LeisureEffectDTO:
    """여가 활동의 결과"""
    leisure_type: LeisureType
    leisure_hours: float
    utility_gained: float
    xp_gained: float

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
    items_consumed: dict[str, float]
    satisfaction: float
