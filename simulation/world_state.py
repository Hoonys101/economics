from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from collections import deque

if TYPE_CHECKING:
    from simulation.models import RealEstateUnit, Transaction
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.core_markets import Market
    from simulation.bank import Bank
    from simulation.agents.government import Government
    from simulation.agents.central_bank import CentralBank
    from simulation.markets.stock_market import StockMarket
    from simulation.metrics.economic_tracker import EconomicIndicatorTracker
    from simulation.metrics.inequality_tracker import InequalityTracker
    from simulation.metrics.stock_tracker import StockMarketTracker, PersonalityStatisticsTracker
    from simulation.ai_model import AIEngineRegistry
    from simulation.ai.ai_training_manager import AITrainingManager
    from simulation.systems.ma_manager import MAManager
    from simulation.systems.demographic_manager import DemographicManager
    from simulation.systems.immigration_manager import ImmigrationManager
    from simulation.systems.inheritance_manager import InheritanceManager
    from simulation.systems.housing_system import HousingSystem
    from simulation.systems.persistence_manager import PersistenceManager
    from simulation.systems.analytics_system import AnalyticsSystem
    from simulation.systems.firm_management import FirmSystem
    from simulation.systems.technology_manager import TechnologyManager
    from simulation.systems.bootstrapper import Bootstrapper
    from simulation.systems.generational_wealth_audit import GenerationalWealthAudit
    from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner
    from simulation.systems.transaction_processor import TransactionProcessor
    from modules.finance.system import FinanceSystem
    from simulation.systems.social_system import SocialSystem
    from simulation.systems.event_system import EventSystem
    from simulation.systems.sensory_system import SensorySystem
    from simulation.systems.settlement_system import SettlementSystem
    from modules.finance.api import ISettlementSystem
    from simulation.systems.commerce_system import CommerceSystem
    from simulation.systems.labor_market_analyzer import LaborMarketAnalyzer
    from modules.analysis.crisis_monitor import CrisisMonitor
    from simulation.db.repository import SimulationRepository
    from modules.common.config_manager.api import ConfigManager
    from simulation.dtos.scenario import StressScenarioConfig
    from modules.government.politics_system import PoliticsSystem
from modules.system.api import IAssetRecoverySystem, ICurrencyHolder, CurrencyCode, IGlobalRegistry, IAgentRegistry, DEFAULT_CURRENCY # Added for Phase 33
from modules.system.constants import ID_CENTRAL_BANK, ID_PUBLIC_MANAGER, ID_SYSTEM
from modules.finance.kernel.api import ISagaOrchestrator, IMonetaryLedger
from modules.finance.api import IShareholderRegistry
from modules.simulation.api import AgentID, IEstateRegistry
from modules.governance.api import SystemCommand
from simulation.dtos.commands import GodCommandDTO
from modules.simulation.dtos.api import MoneySupplyDTO
from modules.system.server_bridge import CommandQueue, TelemetryExchange
from simulation.orchestration.dashboard_service import DashboardService


class WorldState:
    """
    Holds the entire state of the simulation world.
    Decomposed from Simulation engine.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        config_module: Any,
        logger: logging.Logger,
        repository: SimulationRepository
    ) -> None:
        self.config_manager = config_manager
        self.config_module = config_module
        self.logger = logger
        self.repository = repository

        # These attributes are populated by the SimulationInitializer
        self.time: int = 0
        self.run_id: int = 0
        self.households: List[Household] = []
        self.firms: List[Firm] = []
        self.agents: Dict[AgentID, Any] = {}
        self.next_agent_id: int = 0
        self.markets: Dict[str, Market] = {}
        self.bank: Optional[Bank] = None
        self.government: Optional[Government] = None
        self.central_bank: Optional[CentralBank] = None
        self.stock_market: Optional[StockMarket] = None
        self.tracker: Optional[EconomicIndicatorTracker] = None
        self.inequality_tracker: Optional[InequalityTracker] = None
        self.stock_tracker: Optional[StockMarketTracker] = None
        self.personality_tracker: Optional[PersonalityStatisticsTracker] = None
        self.ai_training_manager: Optional[AITrainingManager] = None
        self.ma_manager: Optional[MAManager] = None
        self.demographic_manager: Optional[DemographicManager] = None
        self.immigration_manager: Optional[ImmigrationManager] = None
        self.inheritance_manager: Optional[InheritanceManager] = None
        self.housing_system: Optional[HousingSystem] = None
        self.persistence_manager: Optional[PersistenceManager] = None
        self.analytics_system: Optional[AnalyticsSystem] = None
        self.firm_system: Optional[FirmSystem] = None
        self.technology_manager: Optional[TechnologyManager] = None
        self.generational_wealth_audit: Optional[GenerationalWealthAudit] = None
        self.breeding_planner: Optional[VectorizedHouseholdPlanner] = None
        self.transaction_processor: Optional[TransactionProcessor] = None
        self.lifecycle_manager: Optional[Any] = None # To be AgentLifecycleManager
        self.goods_data: List[Dict[str, Any]] = []
        self.real_estate_units: List[RealEstateUnit] = []
        self.finance_system: Optional[FinanceSystem] = None
        self.ai_trainer: Optional[AIEngineRegistry] = None
        self.transactions: List[Any] = []  # Stores transactions of the current tick
        self.inter_tick_queue: List[Transaction] = []  # WO-109: Queue for next tick
        self.effects_queue: List[Dict[str, Any]] = []  # WO-109: Queue for side-effects
        self.inactive_agents: Dict[int, Any] = {}  # WO-109: Store inactive agents for transaction processing
        from collections import deque
        self.system_commands: List[SystemCommand] = [] # TD-255: Cockpit Event Queue
        self.god_command_queue: deque[GodCommandDTO] = deque() # FOUND-03: Thread-safe Phase 0 Queue

        # Production Integration (INT-01)
        self.command_queue: Optional[CommandQueue] = None
        self.telemetry_exchange: Optional[TelemetryExchange] = None
        self.dashboard_service: Optional[DashboardService] = None

        # New Systems
        self.social_system: Optional[SocialSystem] = None
        self.event_system: Optional[EventSystem] = None
        self.sensory_system: Optional[SensorySystem] = None
        self.settlement_system: Optional[ISettlementSystem] = None
        self.agent_registry: Optional[IAgentRegistry] = None # Added for explicit typing
        self.saga_orchestrator: Optional[ISagaOrchestrator] = None
        self.monetary_ledger: Optional[IMonetaryLedger] = None
        self.shareholder_registry: Optional[IShareholderRegistry] = None # TD-275
        self.taxation_system: Optional[Any] = None # WO-116
        self.commerce_system: Optional[CommerceSystem] = None
        self.labor_market_analyzer: Optional[LaborMarketAnalyzer] = None
        self.crisis_monitor: Optional[CrisisMonitor] = None
        self.stress_scenario_config: Optional[StressScenarioConfig] = None
        self.public_manager: Optional[IAssetRecoverySystem] = None
        self.politics_system: Optional[PoliticsSystem] = None # Phase 4.4: Political Orchestrator
        self.currency_holders: List[ICurrencyHolder] = [] # Added for Phase 33
        self._currency_holders_set: set = set()
        self.estate_registry: Optional[IEstateRegistry] = None
        # FOUND-03: Global Registry - Initialized via Dependency Injection (simulation.lock via initializer)
        self.global_registry: Optional[IGlobalRegistry] = None
        self.telemetry_collector: Optional[Any] = None
        self.scenario_verifier: Optional[Any] = None

        # Attributes with default values
        self.batch_save_interval: int = self.config_manager.get("simulation.batch_save_interval", 50)
        self.household_time_allocation: Dict[int, float] = {}
        self.last_interest_rate: float = 0.0

        # Buffers
        self.inflation_buffer = deque(maxlen=10)
        self.unemployment_buffer = deque(maxlen=10)
        self.gdp_growth_buffer = deque(maxlen=10)
        self.wage_buffer = deque(maxlen=10)
        self.approval_buffer = deque(maxlen=10)

        self.last_avg_price_for_sma = 10.0
        self.last_gdp_for_sma = 0.0

        self.baseline_money_supply: float = 0.0
        
        # Phase 4.1: Macro & Sentiment Metrics
        self.tick_withdrawal_pennies: int = 0
        self.market_panic_index: float = 0.0

    def record_withdrawal(self, amount_pennies: int) -> None:
        """Records a withdrawal event for panic index calculation."""
        self.tick_withdrawal_pennies += amount_pennies

    def calculate_base_money(self) -> Dict[CurrencyCode, int]:
        """
        Calculates M0 (Base Money) for each currency.
        M0 = Bank Reserves (Liquidity held at CB).
        In this simulation, Bank.wallet is its Reserve account.
        MIGRATION: Returns int (pennies).
        """
        totals: Dict[CurrencyCode, int] = {}
        if self.bank:
            assets_dict = self.bank.get_assets_by_currency()
            for cur, amount in assets_dict.items():
                totals[cur] = totals.get(cur, 0) + max(0, int(amount))
        return totals

    def calculate_total_money(self) -> MoneySupplyDTO:
        """
        Calculates M2 (Total Money Supply) and System Debt.
        M2 = Sum(max(0, balance)) for all agents (including System Agents).
        SystemDebt = Sum(abs(balance)) where balance < 0.
        Returns: MoneySupplyDTO with strict penny values.
        """
        total_m2_pennies = 0
        system_debt_pennies = 0

        # Helper to process an agent
        def process_agent(agent):
            nonlocal total_m2_pennies, system_debt_pennies
            # Check if agent holds currency
            if not hasattr(agent, 'get_assets_by_currency'):
                return

            # Retrieve assets safely (strictly in pennies)
            assets_dict = agent.get_assets_by_currency()
            val = int(assets_dict.get(DEFAULT_CURRENCY, 0))
            
            if val >= 0:
                total_m2_pennies += val
            else:
                system_debt_pennies += abs(val)

        # 1. Active Agents in Registry
        # Use self.agents as the primary source of truth to avoid missing agents
        system_agent_ids = {ID_CENTRAL_BANK, ID_SYSTEM, getattr(self.bank, 'id', -999) if self.bank else -999}
        
        for agent in self.agents.values():
            # Dead Agent Guard (Strict)
            if hasattr(agent, 'is_active') and not agent.is_active:
                continue
            
            # Exclude System Agents from M2 (Double-counting guard)
            if hasattr(agent, 'id') and agent.id in system_agent_ids:
                continue
                
            process_agent(agent)

        # 2. Estate Agents (Always Inactive, but holding funds)
        if self.estate_registry:
            for agent in self.estate_registry.get_all_estate_agents():
                process_agent(agent)

        return MoneySupplyDTO(
            total_m2_pennies=total_m2_pennies,
            system_debt_pennies=system_debt_pennies,
            currency=DEFAULT_CURRENCY
        )

    def get_total_system_money_for_diagnostics(self, target_currency: CurrencyCode = "USD") -> float:
        """
        Provides a single float value for total system money for backward compatibility
        with diagnostic tools. Converts M2 (pennies) to float.
        """
        supply_dto = self.calculate_total_money()
        # Strictly return M2 in pennies as float for legacy diagnostics
        return float(supply_dto.total_m2_pennies)

    def resolve_agent_id(self, role: str) -> Optional[AgentID]:
        """
        Dynamically resolves specific agent IDs by role (e.g. GOVERNMENT, CENTRAL_BANK).
        Used to eliminate hardcoded ID constants.
        """
        if role == "GOVERNMENT":
            self.logger.warning("Call to deprecated method WorldState.resolve_agent_id('GOVERNMENT')")
            return AgentID(self.government.id) if self.government else None
        elif role == "CENTRAL_BANK":
            return AgentID(self.central_bank.id) if self.central_bank else None
        return None

    def register_currency_holder(self, holder: ICurrencyHolder) -> None:
        """Registers an agent as a currency holder for M2 tracking."""
        if holder not in self._currency_holders_set:
            self.currency_holders.append(holder)
            self._currency_holders_set.add(holder)

    def unregister_currency_holder(self, holder: ICurrencyHolder) -> None:
        """Unregisters an agent from M2 tracking (e.g. upon death)."""
        if holder in self._currency_holders_set:
            self.currency_holders.remove(holder)
            self._currency_holders_set.remove(holder)

    def get_all_agents(self) -> List[Any]:
        """시뮬레이션에 참여하는 모든 활성 에이전트(가계, 기업, 은행 등)를 반환합니다."""
        all_agents = []
        for agent in self.agents.values():
            if (
                getattr(agent, "is_active", True)
                and hasattr(agent, "value_orientation")
                and agent.value_orientation != "N/A"
            ):
                all_agents.append(agent)
        return all_agents
