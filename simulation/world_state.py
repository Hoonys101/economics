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
from modules.system.api import IAssetRecoverySystem


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
        self.agents: Dict[int, Any] = {}
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

        # New Systems
        self.social_system: Optional[SocialSystem] = None
        self.event_system: Optional[EventSystem] = None
        self.sensory_system: Optional[SensorySystem] = None
        self.settlement_system: Optional[SettlementSystem] = None
        self.commerce_system: Optional[CommerceSystem] = None
        self.labor_market_analyzer: Optional[LaborMarketAnalyzer] = None
        self.crisis_monitor: Optional[CrisisMonitor] = None
        self.stress_scenario_config: Optional[StressScenarioConfig] = None
        self.public_manager: Optional[IAssetRecoverySystem] = None

        # Attributes with default values
        self.batch_save_interval: int = 50
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

    def calculate_total_money(self) -> float:
        """
        Calculates the total money supply in the system.
        Money_Total = Household_Assets + Firm_Assets + Bank_Reserves + Government_Assets
        (Government assets are INCLUDED to ensure zero-sum integrity during transfers)
        """
        total = 0.0

        # 1. Households
        for h in self.households:
            if h.is_active:
                total += h.assets

        # 2. Firms
        for f in self.firms:
            if f.is_active:
                total += f.assets

        # 3. Bank Reserves
        if self.bank:
            total += self.bank.assets

        # 4. Government Assets (WO-Fix: Include Government in M2 to prevent leaks)
        if self.government:
            total += self.government.assets

        # 6. Central Bank Assets (WO-124: Include Central Bank for Genesis Protocol Integrity)
        # Central Bank holds negative cash if it distributed more than it had, or positive if it minted but hasn't distributed.
        if self.central_bank:
            total += self.central_bank.assets.get('cash', 0.0)

        # 7. Public Manager Treasury (Phase 3: Asset Liquidation)
        if self.public_manager:
            total += self.public_manager.system_treasury

        return total

    def resolve_agent_id(self, role: str) -> Optional[int]:
        """
        Dynamically resolves specific agent IDs by role (e.g. GOVERNMENT, CENTRAL_BANK).
        Used to eliminate hardcoded ID constants.
        """
        if role == "GOVERNMENT":
            return self.government.id if self.government else None
        elif role == "CENTRAL_BANK":
            return self.central_bank.id if self.central_bank else None
        return None

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
