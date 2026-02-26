import logging
from _typeshed import Incomplete
from collections import deque
from modules.analysis.crisis_monitor import CrisisMonitor as CrisisMonitor
from modules.common.config_manager.api import ConfigManager as ConfigManager
from modules.finance.api import ISettlementSystem as ISettlementSystem, IShareholderRegistry as IShareholderRegistry
from modules.finance.kernel.api import IMonetaryLedger as IMonetaryLedger, ISagaOrchestrator as ISagaOrchestrator
from modules.finance.system import FinanceSystem as FinanceSystem
from modules.governance.api import SystemCommand as SystemCommand
from modules.government.politics_system import PoliticsSystem as PoliticsSystem
from modules.market.api import IIndexCircuitBreaker as IIndexCircuitBreaker
from modules.simulation.api import AgentID, IEstateRegistry as IEstateRegistry
from modules.simulation.dtos.api import MoneySupplyDTO
from modules.system.api import CurrencyCode as CurrencyCode, IAgentRegistry as IAgentRegistry, IAssetRecoverySystem as IAssetRecoverySystem, ICurrencyHolder as ICurrencyHolder, IGlobalRegistry as IGlobalRegistry
from modules.system.server_bridge import CommandQueue as CommandQueue, TelemetryExchange as TelemetryExchange
from simulation.agents.central_bank import CentralBank as CentralBank
from simulation.agents.government import Government as Government
from simulation.ai.ai_training_manager import AITrainingManager as AITrainingManager
from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner as VectorizedHouseholdPlanner
from simulation.ai_model import AIEngineRegistry as AIEngineRegistry
from simulation.bank import Bank as Bank
from simulation.core_agents import Household as Household
from simulation.core_markets import Market as Market
from simulation.db.repository import SimulationRepository as SimulationRepository
from simulation.dtos.commands import GodCommandDTO as GodCommandDTO
from simulation.dtos.scenario import StressScenarioConfig as StressScenarioConfig
from simulation.firms import Firm as Firm
from simulation.markets.stock_market import StockMarket as StockMarket
from simulation.metrics.economic_tracker import EconomicIndicatorTracker as EconomicIndicatorTracker
from simulation.metrics.inequality_tracker import InequalityTracker as InequalityTracker
from simulation.metrics.stock_tracker import PersonalityStatisticsTracker as PersonalityStatisticsTracker, StockMarketTracker as StockMarketTracker
from simulation.models import RealEstateUnit as RealEstateUnit, Transaction as Transaction
from simulation.orchestration.dashboard_service import DashboardService as DashboardService
from simulation.systems.analytics_system import AnalyticsSystem as AnalyticsSystem
from simulation.systems.bootstrapper import Bootstrapper as Bootstrapper
from simulation.systems.commerce_system import CommerceSystem as CommerceSystem
from simulation.systems.demographic_manager import DemographicManager as DemographicManager
from simulation.systems.event_system import EventSystem as EventSystem
from simulation.systems.firm_management import FirmSystem as FirmSystem
from simulation.systems.generational_wealth_audit import GenerationalWealthAudit as GenerationalWealthAudit
from simulation.systems.housing_system import HousingSystem as HousingSystem
from simulation.systems.immigration_manager import ImmigrationManager as ImmigrationManager
from simulation.systems.inheritance_manager import InheritanceManager as InheritanceManager
from simulation.systems.labor_market_analyzer import LaborMarketAnalyzer as LaborMarketAnalyzer
from simulation.systems.ma_manager import MAManager as MAManager
from simulation.systems.persistence_manager import PersistenceManager as PersistenceManager
from simulation.systems.sensory_system import SensorySystem as SensorySystem
from simulation.systems.settlement_system import SettlementSystem as SettlementSystem
from simulation.systems.social_system import SocialSystem as SocialSystem
from simulation.systems.technology_manager import TechnologyManager as TechnologyManager
from simulation.systems.transaction_processor import TransactionProcessor as TransactionProcessor
from typing import Any

class WorldState:
    """
    Holds the entire state of the simulation world.
    Decomposed from Simulation engine.
    """
    config_manager: Incomplete
    config_module: Incomplete
    logger: Incomplete
    repository: Incomplete
    time: int
    run_id: int
    households: list[Household]
    firms: list[Firm]
    agents: dict[AgentID, Any]
    next_agent_id: int
    markets: dict[str, Market]
    bank: Bank | None
    government: Government | None
    central_bank: CentralBank | None
    stock_market: StockMarket | None
    tracker: EconomicIndicatorTracker | None
    inequality_tracker: InequalityTracker | None
    stock_tracker: StockMarketTracker | None
    personality_tracker: PersonalityStatisticsTracker | None
    ai_training_manager: AITrainingManager | None
    ma_manager: MAManager | None
    demographic_manager: DemographicManager | None
    immigration_manager: ImmigrationManager | None
    inheritance_manager: InheritanceManager | None
    housing_system: HousingSystem | None
    persistence_manager: PersistenceManager | None
    analytics_system: AnalyticsSystem | None
    firm_system: FirmSystem | None
    technology_manager: TechnologyManager | None
    generational_wealth_audit: GenerationalWealthAudit | None
    breeding_planner: VectorizedHouseholdPlanner | None
    transaction_processor: TransactionProcessor | None
    lifecycle_manager: Any | None
    goods_data: list[dict[str, Any]]
    real_estate_units: list[RealEstateUnit]
    finance_system: FinanceSystem | None
    ai_trainer: AIEngineRegistry | None
    transactions: list[Any]
    inter_tick_queue: list[Transaction]
    effects_queue: list[dict[str, Any]]
    inactive_agents: dict[int, Any]
    system_commands: list[SystemCommand]
    god_commands: list[GodCommandDTO]
    command_queue: CommandQueue | None
    telemetry_exchange: TelemetryExchange | None
    dashboard_service: DashboardService | None
    social_system: SocialSystem | None
    event_system: EventSystem | None
    sensory_system: SensorySystem | None
    settlement_system: ISettlementSystem | None
    agent_registry: IAgentRegistry | None
    saga_orchestrator: ISagaOrchestrator | None
    monetary_ledger: IMonetaryLedger | None
    shareholder_registry: IShareholderRegistry | None
    taxation_system: Any | None
    commerce_system: CommerceSystem | None
    labor_market_analyzer: LaborMarketAnalyzer | None
    crisis_monitor: CrisisMonitor | None
    stress_scenario_config: StressScenarioConfig | None
    public_manager: IAssetRecoverySystem | None
    politics_system: PoliticsSystem | None
    index_circuit_breaker: IIndexCircuitBreaker | None
    currency_holders: list[ICurrencyHolder]
    estate_registry: IEstateRegistry | None
    global_registry: IGlobalRegistry | None
    telemetry_collector: Any | None
    scenario_verifier: Any | None
    batch_save_interval: int
    household_time_allocation: dict[int, float]
    last_interest_rate: float
    inflation_buffer: Incomplete
    unemployment_buffer: Incomplete
    gdp_growth_buffer: Incomplete
    wage_buffer: Incomplete
    approval_buffer: Incomplete
    last_avg_price_for_sma: float
    last_gdp_for_sma: float
    baseline_money_supply: float
    tick_withdrawal_pennies: int
    market_panic_index: float
    def __init__(self, config_manager: ConfigManager, config_module: Any, logger: logging.Logger, repository: SimulationRepository) -> None: ...
    def record_withdrawal(self, amount_pennies: int) -> None:
        """Records a withdrawal event for panic index calculation."""
    def calculate_base_money(self) -> dict[CurrencyCode, int]:
        """
        Calculates M0 (Base Money) for each currency.
        M0 = Bank Reserves (Liquidity held at CB).
        In this simulation, Bank.wallet is its Reserve account.
        MIGRATION: Returns int (pennies).
        """
    def calculate_total_money(self) -> MoneySupplyDTO:
        """
        Calculates M2 (Total Money Supply) and System Debt.
        M2 is delegated to the Unified Monetary Ledger (SSoT).
        SystemDebt = Sum(abs(balance)) where balance < 0.
        Returns: MoneySupplyDTO with strict penny values.
        """
    def get_total_system_money_for_diagnostics(self, target_currency: CurrencyCode = 'USD') -> float:
        """
        Provides a single float value for total system money for backward compatibility
        with diagnostic tools. Converts M2 (pennies) to float.
        """
    def resolve_agent_id(self, role: str) -> AgentID | None:
        """
        Dynamically resolves specific agent IDs by role (e.g. GOVERNMENT, CENTRAL_BANK).
        Used to eliminate hardcoded ID constants.
        """
    def register_currency_holder(self, holder: ICurrencyHolder) -> None:
        """Registers an agent as a currency holder for M2 tracking."""
    def unregister_currency_holder(self, holder: ICurrencyHolder) -> None:
        """Unregisters an agent from M2 tracking (e.g. upon death)."""
    def get_all_agents(self) -> list[Any]:
        """시뮬레이션에 참여하는 모든 활성 에이전트(가계, 기업, 은행 등)를 반환합니다."""
