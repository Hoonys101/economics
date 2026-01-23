# simulation/initialization/initializer.py

from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING
import logging
import hashlib
import json
import os
from collections import deque

if TYPE_CHECKING:
    from simulation.engine import Simulation

# All imports moved from engine.py
from modules.common.config_manager.api import ConfigManager
from simulation.initialization.api import SimulationInitializerInterface
from simulation.models import Order, RealEstateUnit
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.core_markets import Market
from simulation.bank import Bank
from simulation.agents.government import Government
from simulation.agents.central_bank import CentralBank
from simulation.loan_market import LoanMarket
from simulation.markets.order_book_market import OrderBookMarket
from simulation.markets.stock_market import StockMarket
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.metrics.inequality_tracker import InequalityTracker
from simulation.metrics.stock_tracker import StockMarketTracker, PersonalityStatisticsTracker
from simulation.ai_model import AIEngineRegistry
from simulation.ai.ai_training_manager import AITrainingManager
from simulation.systems.ma_manager import MAManager
from simulation.systems.reflux_system import EconomicRefluxSystem
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
from simulation.db.repository import SimulationRepository
from simulation.systems.lifecycle_manager import AgentLifecycleManager
from simulation.engine import Simulation
from simulation.systems.social_system import SocialSystem
from simulation.systems.event_system import EventSystem
from simulation.systems.sensory_system import SensorySystem
from simulation.systems.settlement_system import SettlementSystem
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.labor_market_analyzer import LaborMarketAnalyzer

# Phase 29: Crisis Monitor
from modules.analysis.crisis_monitor import CrisisMonitor


class SimulationInitializer(SimulationInitializerInterface):
    """Simulation 인스턴스 생성 및 모든 구성 요소의 초기화를 전담합니다."""

    def __init__(self,
                 config_manager: ConfigManager,
                 config_module: Any,
                 goods_data: List[Dict[str, Any]],
                 repository: SimulationRepository,
                 logger: logging.Logger,
                 households: List[Household],
                 firms: List[Firm],
                 ai_trainer: AIEngineRegistry):
        self.config_manager = config_manager
        self.config = config_module
        self.goods_data = goods_data
        self.repository = repository
        self.logger = logger
        self.households = households
        self.firms = firms
        self.ai_trainer = ai_trainer

    def build_simulation(self) -> Simulation:
        """
        Simulation 인스턴스를 생성하고 모든 구성 요소를 조립합니다.
        (기존 Simulation.__init__ 로직을 이 곳으로 이동)
        """
        # 1. Create the empty Simulation shell
        sim = Simulation(
            config_manager=self.config_manager,
            config_module=self.config,
            logger=self.logger,
            repository=self.repository
        )

        # 2. Populate the shell with all its components
        sim.households = self.households
        sim.firms = self.firms
        sim.goods_data = self.goods_data
        sim.agents: Dict[int, Any] = {h.id: h for h in self.households}
        sim.agents.update({f.id: f for f in self.firms})
        sim.next_agent_id = len(self.households) + len(self.firms)

        sim.ai_trainer = self.ai_trainer
        sim.time: int = 0
        sim.batch_save_interval = 50

        # Initialize Settlement System Early (WO-116)
        sim.settlement_system = SettlementSystem(logger=self.logger)

        sim.bank = Bank(
            id=sim.next_agent_id,
            initial_assets=self.config.INITIAL_BANK_ASSETS,
            config_manager=self.config_manager
        )
        sim.agents[sim.bank.id] = sim.bank
        sim.next_agent_id += 1

        sim.government = Government(
            id=sim.next_agent_id,
            initial_assets=0.0,
            config_module=self.config
        )
        sim.agents[sim.government.id] = sim.government
        sim.next_agent_id += 1

        sim.tracker = EconomicIndicatorTracker(config_module=self.config)

        sim.central_bank = CentralBank(
            tracker=sim.tracker,
            config_module=self.config
        )

        sim.finance_system = FinanceSystem(
            government=sim.government,
            central_bank=sim.central_bank,
            bank=sim.bank,
            config_module=self.config_manager,
            settlement_system=sim.settlement_system
        )
        sim.government.finance_system = sim.finance_system

        sim.real_estate_units: List[RealEstateUnit] = [
            RealEstateUnit(id=i, estimated_value=self.config.INITIAL_PROPERTY_VALUE,
                           rent_price=self.config.INITIAL_RENT_PRICE)
            for i in range(self.config.NUM_HOUSING_UNITS)
        ]

        top_20_count = len(sim.households) // 5
        top_households = sorted(sim.households, key=lambda h: h.assets, reverse=True)[:top_20_count]

        for i, hh in enumerate(top_households):
            if i < len(sim.real_estate_units):
                unit = sim.real_estate_units[i]
                unit.owner_id = hh.id
                hh.owned_properties.append(unit.id)
                unit.occupant_id = hh.id
                hh.residing_property_id = unit.id
                hh.is_homeless = False

        sim.markets: Dict[str, Market] = {
            good_name: OrderBookMarket(market_id=good_name)
            for good_name in self.config.GOODS
        }
        sim.markets["labor"] = OrderBookMarket(market_id="labor")
        sim.markets["loan_market"] = LoanMarket(
            market_id="loan_market", bank=sim.bank, config_module=self.config
        )
        sim.markets["loan_market"].agents_ref = sim.agents

        if getattr(self.config, "STOCK_MARKET_ENABLED", False):
            sim.stock_market = StockMarket(config_module=self.config, logger=self.logger)
            sim.stock_tracker = StockMarketTracker(config_module=self.config)
            sim.markets["stock_market"] = sim.stock_market
            for firm in sim.firms:
                if hasattr(firm, "init_ipo"):
                    firm.init_ipo(sim.stock_market)
        else:
            sim.stock_market = None
            sim.stock_tracker = None

        sim.markets["housing"] = OrderBookMarket(market_id="housing")

        for unit in sim.real_estate_units:
            if unit.owner_id is None:
                sell_order = Order(
                    agent_id=sim.government.id,
                    item_id=f"unit_{unit.id}",
                    price=unit.estimated_value,
                    quantity=1.0,
                    market_id="housing",
                    order_type="SELL"
                )
                if "housing" in sim.markets:
                    sim.markets["housing"].place_order(sell_order, sim.time)

        for agent in sim.households + sim.firms:
            agent.update_needs(sim.time)
            agent.decision_engine.markets = sim.markets
            agent.decision_engine.goods_data = self.goods_data
            if isinstance(agent, Firm):
                agent.config_module = self.config

        sim.inequality_tracker = InequalityTracker(config_module=self.config)
        sim.personality_tracker = PersonalityStatisticsTracker(config_module=self.config)
        # Initialize with a combined list copy to prevent aliasing sim.households
        # Note: New agents must be explicitly added to this list by lifecycle managers.
        sim.ai_training_manager = AITrainingManager(sim.households + sim.firms, self.config)
        sim.ma_manager = MAManager(sim, self.config)
        sim.reflux_system = EconomicRefluxSystem()
        sim.demographic_manager = DemographicManager(config_module=self.config)
        sim.immigration_manager = ImmigrationManager(config_module=self.config)
        sim.inheritance_manager = InheritanceManager(config_module=self.config)
        sim.housing_system = HousingSystem(config_module=self.config)
        sim.persistence_manager = PersistenceManager(
            run_id=0,
            config_module=self.config,
            repository=self.repository
        )
        sim.firm_system = FirmSystem(config_module=self.config)
        sim.technology_manager = TechnologyManager(config_module=self.config, logger=self.logger)

        Bootstrapper.inject_initial_liquidity(sim.firms, self.config, sim.settlement_system, sim.central_bank)
        Bootstrapper.force_assign_workers(sim.firms, sim.households)

        sim.generational_wealth_audit = GenerationalWealthAudit(config_module=self.config)
        sim.breeding_planner = VectorizedHouseholdPlanner(self.config)
        sim.transaction_processor = TransactionProcessor(self.config)

        # AgentLifecycleManager is created here and injected into the simulation
        sim.lifecycle_manager = AgentLifecycleManager(
            config_module=self.config,
            demographic_manager=sim.demographic_manager,
            inheritance_manager=sim.inheritance_manager,
            firm_system=sim.firm_system,
            logger=self.logger
        )

        # Initialize New Systems (Social, Event, Sensory, Commerce, Labor)
        sim.social_system = SocialSystem(self.config)
        sim.event_system = EventSystem(self.config)
        sim.sensory_system = SensorySystem(self.config)
        # sim.settlement_system initialized earlier
        sim.commerce_system = CommerceSystem(self.config, sim.reflux_system)
        sim.labor_market_analyzer = LaborMarketAnalyzer(self.config)

        # Phase 29: Crisis Monitor
        sim.crisis_monitor = CrisisMonitor(logger=self.logger, run_id=sim.run_id)

        # Phase 28: Initialize Stress Scenario Config
        from simulation.dtos.scenario import StressScenarioConfig
        sim.stress_scenario_config = StressScenarioConfig()

        # Load Scenario from JSON if directed by config
        active_scenario_name = self.config_manager.get("simulation.active_scenario")
        if active_scenario_name:
            scenario_path = f"config/scenarios/{active_scenario_name}.json"
            if os.path.exists(scenario_path):
                 try:
                     with open(scenario_path, 'r') as f:
                         scenario_data = json.load(f)

                     sim.stress_scenario_config.is_active = scenario_data.get("is_active", False)
                     sim.stress_scenario_config.scenario_name = scenario_data.get("scenario_name", active_scenario_name)
                     sim.stress_scenario_config.start_tick = scenario_data.get("start_tick", 50)

                     params = scenario_data.get("parameters", {})
                     sim.stress_scenario_config.monetary_shock_target_rate = params.get("MONETARY_SHOCK_TARGET_RATE")
                     sim.stress_scenario_config.fiscal_shock_tax_rate = params.get("FISCAL_SHOCK_TAX_RATE")
                     sim.stress_scenario_config.base_interest_rate_multiplier = params.get("base_interest_rate_multiplier")
                     sim.stress_scenario_config.corporate_tax_rate_delta = params.get("corporate_tax_rate_delta")
                     sim.stress_scenario_config.demand_shock_multiplier = params.get("demand_shock_multiplier")

                     self.logger.info(f"Loaded Stress Scenario: {sim.stress_scenario_config.scenario_name} (Active: {sim.stress_scenario_config.is_active})")
                 except Exception as e:
                     self.logger.error(f"Failed to load scenario file '{scenario_path}': {e}")
            else:
                self.logger.warning(f"Active scenario '{active_scenario_name}' requested but {scenario_path} not found.")

        sim.household_time_allocation: Dict[int, float] = {}
        sim.inflation_buffer = deque(maxlen=10)
        sim.unemployment_buffer = deque(maxlen=10)
        sim.gdp_growth_buffer = deque(maxlen=10)
        sim.wage_buffer = deque(maxlen=10)
        sim.approval_buffer = deque(maxlen=10)

        sim.last_avg_price_for_sma = 10.0
        sim.last_gdp_for_sma = 0.0
        sim.last_interest_rate = sim.bank.base_rate

        config_content = str(self.config.__dict__)
        config_hash = hashlib.sha256(config_content.encode()).hexdigest()
        sim.run_id = self.repository.save_simulation_run(
            config_hash=config_hash,
            description="Economic simulation run with DB storage",
        )
        sim.persistence_manager.run_id = sim.run_id
        # Update crisis monitor run_id
        sim.crisis_monitor.run_id = sim.run_id

        self.logger.info(
            f"Simulation run started with run_id: {sim.run_id}",
            extra={"run_id": sim.run_id},
        )

        self.logger.info(f"Simulation fully initialized with run_id: {sim.run_id}")

        return sim
