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
    from simulation.systems.commerce_system import CommerceSystem
    from simulation.systems.labor_market_analyzer import LaborMarketAnalyzer
    from modules.analysis.crisis_monitor import CrisisMonitor
    from simulation.db.repository import SimulationRepository
    from modules.common.config_manager.api import ConfigManager
    from simulation.dtos.scenario import StressScenarioConfig
from modules.system.api import IAssetRecoverySystem, ICurrencyHolder, CurrencyCode, IGlobalRegistry, IAgentRegistry # Added for Phase 33
from modules.system.constants import ID_CENTRAL_BANK
from modules.finance.kernel.api import ISagaOrchestrator, IMonetaryLedger
from modules.finance.api import IShareholderRegistry
from modules.simulation.api import AgentID
from modules.governance.api import SystemCommand
from simulation.dtos.commands import GodCommandDTO
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
        self.governments: List[Government] = [] # Changed for Phase 33
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
        self.system_command_queue: List[SystemCommand] = [] # TD-255: Cockpit Event Queue
        self.god_command_queue: deque[GodCommandDTO] = deque() # FOUND-03: Thread-safe Phase 0 Queue

        # Production Integration (INT-01)
        self.command_queue: Optional[CommandQueue] = None
        self.telemetry_exchange: Optional[TelemetryExchange] = None
        self.dashboard_service: Optional[DashboardService] = None

        # New Systems
        self.social_system: Optional[SocialSystem] = None
        self.event_system: Optional[EventSystem] = None
        self.sensory_system: Optional[SensorySystem] = None
        self.settlement_system: Optional[SettlementSystem] = None
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
        self.currency_holders: List[ICurrencyHolder] = [] # Added for Phase 33
        self._currency_holders_set: set = set()
        # FOUND-03: Global Registry - Initialized via Dependency Injection (simulation.lock via initializer)
        self.global_registry: Optional[IGlobalRegistry] = None

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

    def calculate_base_money(self) -> Dict[CurrencyCode, int]:
        """
        Calculates M0 (Base Money) for each currency.
        M0 = Sum of assets held by all agents EXCEPT Central Bank.
        (Central Bank assets represented as negative would cancel out creation).
        MIGRATION: Returns int (pennies).
        """
        totals: Dict[CurrencyCode, int] = {}
        for holder in self.currency_holders:
            # Exclude CentralBank from M0 summation (Source of Money)
            if hasattr(holder, 'id') and holder.id == ID_CENTRAL_BANK:
                continue
            if hasattr(holder, '__class__') and holder.__class__.__name__ == "CentralBank":
                continue

            assets_dict = holder.get_assets_by_currency()
            for cur, amount in assets_dict.items():
                totals[cur] = totals.get(cur, 0) + int(amount)
        return totals

    def calculate_total_money(self) -> Dict[CurrencyCode, int]:
        """
        Calculates M2 (Total Money Supply).
        M2 = M0 - Bank Reserves + Bank Deposits.
        (Currency in Circulation + Deposits).
        MIGRATION: Returns int (pennies).
        """
        m2_totals = self.calculate_base_money()

        # Adjust for Fractional Reserve Banking
        # 1. Deduct Bank Reserves (Vault Cash) from M0 to get Currency in Circulation
        # 2. Add Bank Deposits (Created Money)

        # We need to identify Banks.
        # Assuming currency_holders includes banks.
        for holder in self.currency_holders:
            is_bank = False
            if hasattr(holder, '__class__') and holder.__class__.__name__ == "Bank":
                is_bank = True
            elif hasattr(holder, 'id') and str(holder.id).startswith("bank"): # Heuristic?
                # Better to check class or interface if possible, or rely on explicit list
                pass

            # Explicit check for Bank class
            if hasattr(holder, 'deposits') and hasattr(holder, 'wallet'):
                 is_bank = True

            if is_bank:
                # 1. Deduct Reserves (Bank Wallets are not Circulation)
                reserves = holder.get_assets_by_currency()
                for cur, amount in reserves.items():
                    m2_totals[cur] = m2_totals.get(cur, 0) - int(amount)

                # 2. Add Deposits - REMOVED
                # M2 = Currency + Deposits.
                # In this simulation, Agent Wallets ARE Deposits (or Cash).
                # calculate_base_money() already sums Agent Wallets.
                # Adding Bank.get_total_deposits() double-counts the money supply.
                # (Unless Agent Wallets were strictly Physical Cash and Deposits were invisible, which is not the case here).

        return m2_totals

    def get_total_system_money_for_diagnostics(self, target_currency: CurrencyCode = "USD") -> float:
        """
        Provides a single float value for total system money for backward compatibility
        with diagnostic tools. Converts all currencies to the target currency.
        """
        all_money = self.calculate_total_money()

        # Use tracker's exchange engine if available
        if self.tracker and hasattr(self.tracker, "exchange_engine"):
            total = 0.0
            for cur, amount in all_money.items():
                converted = self.tracker.exchange_engine.convert(amount, cur, target_currency)
                total += converted
            return total

        # Fallback if no exchange engine: just return the target currency balance
        return float(all_money.get(target_currency, 0))

    def resolve_agent_id(self, role: str) -> Optional[AgentID]:
        """
        Dynamically resolves specific agent IDs by role (e.g. GOVERNMENT, CENTRAL_BANK).
        Used to eliminate hardcoded ID constants.
        """
        if role == "GOVERNMENT":
            self.logger.warning("Call to deprecated method WorldState.resolve_agent_id('GOVERNMENT')")
            return AgentID(self.governments[0].id) if self.governments else None
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
