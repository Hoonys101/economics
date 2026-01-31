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
from simulation.systems.transaction_manager import TransactionManager
from simulation.systems.registry import Registry
from simulation.systems.accounting import AccountingSystem
from simulation.systems.central_bank_system import CentralBankSystem
from simulation.systems.handlers import InheritanceHandler
from modules.finance.system import FinanceSystem
from modules.finance.credit_scoring import CreditScoringService
from simulation.db.repository import SimulationRepository
from simulation.systems.lifecycle_manager import AgentLifecycleManager
from simulation.engine import Simulation
from simulation.systems.social_system import SocialSystem
from simulation.systems.event_system import EventSystem
from simulation.systems.sensory_system import SensorySystem
from simulation.systems.settlement_system import SettlementSystem
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.labor_market_analyzer import LaborMarketAnalyzer
from modules.system.escrow_agent import EscrowAgent

# Phase 29: Crisis Monitor
from modules.analysis.crisis_monitor import CrisisMonitor
from modules.system.execution.public_manager import PublicManager


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
                 ai_trainer: AIEngineRegistry,
                 initial_balances: Optional[Dict[int, float]] = None):
        self.config_manager = config_manager
        self.config = config_module
        self.goods_data = goods_data
        self.repository = repository
        self.logger = logger
        self.households = households
        self.firms = firms
        self.ai_trainer = ai_trainer
        self.initial_balances = initial_balances or {}

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
        sim.settlement_system = SettlementSystem(logger=self.logger)

        sim.tracker = EconomicIndicatorTracker(config_module=self.config)

        # WO-136: Initialize Scenario Strategy (Replacing StressScenarioConfig & Config Injection)
        from simulation.dtos.strategy import ScenarioStrategy

        # Load Scenario from JSON if directed by config
        active_scenario_name = self.config_manager.get("simulation.active_scenario")
        strategy = ScenarioStrategy()

        if active_scenario_name:
            scenario_path = f"config/scenarios/{active_scenario_name}.json"
            if os.path.exists(scenario_path):
                 try:
                     with open(scenario_path, 'r') as f:
                         scenario_data = json.load(f)

                     # Extract parameters
                     params = scenario_data.get("parameters", {})

                     # Helper to resolve params with priority and proper zero-handling
                     def resolve(keys, default=None):
                         for k in keys:
                             if k in params and params[k] is not None:
                                 return params[k]
                         return default

                     # Map parameters to Strategy DTO
                     strategy = ScenarioStrategy(
                         name=active_scenario_name,
                         is_active=scenario_data.get("is_active", False),
                         start_tick=scenario_data.get("start_tick", 50),
                         scenario_name=scenario_data.get("scenario_name", active_scenario_name),

                         # Stress Params
                         inflation_expectation_multiplier=resolve(["inflation_expectation_multiplier"], 1.0),
                         hoarding_propensity_factor=resolve(["hoarding_propensity_factor"], 0.0),
                         demand_shock_cash_injection=resolve(["demand_shock_cash_injection"], 0.0),
                         panic_selling_enabled=resolve(["panic_selling_enabled"], False),
                         debt_aversion_multiplier=resolve(["debt_aversion_multiplier"], 1.0),
                         consumption_pessimism_factor=resolve(["consumption_pessimism_factor"], 0.0),
                         asset_shock_reduction=resolve(["asset_shock_reduction"], 0.0),
                         exogenous_productivity_shock=resolve(["exogenous_productivity_shock"], {}),
                         monetary_shock_target_rate=resolve(["monetary_shock_target_rate", "MONETARY_SHOCK_TARGET_RATE"]),
                         fiscal_shock_tax_rate=resolve(["fiscal_shock_tax_rate", "FISCAL_SHOCK_TAX_RATE"]),
                         base_interest_rate_multiplier=resolve(["base_interest_rate_multiplier"]),
                         corporate_tax_rate_delta=resolve(["corporate_tax_rate_delta"]),
                         demand_shock_multiplier=resolve(["demand_shock_multiplier"]),

                         # Config Injection Replacements
                         tfp_multiplier=resolve(["TFP_MULTIPLIER", "food_tfp_multiplier"], 3.0),
                         tech_fertilizer_unlock_tick=resolve(["TECH_FERTILIZER_UNLOCK_TICK"], 50),
                         tech_diffusion_rate=resolve(["TECH_DIFFUSION_RATE"], 0.05),
                         food_sector_config=resolve(["FOOD_SECTOR_CONFIG"], {}),
                         market_config=resolve(["MARKET_CONFIG"], {}),
                         deflationary_pressure_multiplier=resolve(["DEFLATIONARY_PRESSURE_MULTIPLIER"], 1.0),
                         limits=resolve(["LIMITS"], {}),
                         firm_decision_engine=resolve(["FIRM_DECISION_ENGINE"]),
                         household_decision_engine=resolve(["HOUSEHOLD_DECISION_ENGINE"]),

                         # --- Initialization Parameters (Golden Era & Legacy) ---
                         initial_base_interest_rate=resolve(["base_interest_rate", "INITIAL_BASE_ANNUAL_RATE"]),
                         initial_corporate_tax_rate=resolve(["tax_rate_corporate", "CORPORATE_TAX_RATE"]),
                         initial_income_tax_rate=resolve(["tax_rate_income", "INCOME_TAX_RATE"]),
                         newborn_engine_type=resolve(["newborn_engine_type", "NEWBORN_ENGINE_TYPE"]),
                         firm_decision_mode=resolve(["firm_decision_mode"]),
                         innovation_weight=resolve(["innovation_weight"]),

                         parameters=params # Store raw params just in case
                     )

                     self.logger.info(f"Loaded Scenario Strategy: {strategy.name} (Active: {strategy.is_active})")

                     # Legacy Parameter Logging
                     if strategy.initial_corporate_tax_rate:
                         self.logger.debug(f"Initial Corporate Tax Rate set to {strategy.initial_corporate_tax_rate} via strategy.")
                     if strategy.tfp_multiplier:
                         self.logger.debug(f"TFP Multiplier set to {strategy.tfp_multiplier} via strategy.")

                 except Exception as e:
                     self.logger.error(f"Failed to load scenario file '{scenario_path}': {e}")
            else:
                self.logger.warning(f"Active scenario '{active_scenario_name}' requested but {scenario_path} not found.")

        sim.strategy = strategy
        # Alias for backward compatibility (DecisionContext uses this name)
        sim.stress_scenario_config = strategy

        # WO-124: Initialize CentralBank EARLY for Genesis Protocol
        sim.central_bank = CentralBank(
            tracker=sim.tracker,
            config_module=self.config,
            strategy=sim.strategy
        )
        # Genesis Step 1: Fiat Lux (Minting M0)
        sim.central_bank.deposit(self.config.INITIAL_MONEY_SUPPLY)
        self.logger.info(f"GENESIS | Central Bank minted M0: {self.config.INITIAL_MONEY_SUPPLY:,.2f}")

        sim.households = self.households
        sim.firms = self.firms
        sim.goods_data = self.goods_data
        sim.agents: Dict[int, Any] = {h.id: h for h in self.households}
        sim.agents.update({f.id: f for f in self.firms})
        sim.next_agent_id = len(self.households) + len(self.firms)

        # Inject SettlementSystem into all agents
        for agent in sim.agents.values():
            agent.settlement_system = sim.settlement_system

        sim.ai_trainer = self.ai_trainer
        sim.time: int = 0

        # WO-078: Initialize CreditScoringService
        credit_scoring_service = CreditScoringService(config_module=self.config)

        # WO-124: Initialize Bank with 0.0 assets
        sim.bank = Bank(
            id=sim.next_agent_id,
            initial_assets=0.0, # Will be funded via Genesis Grant
            config_manager=self.config_manager,
            settlement_system=sim.settlement_system,
            credit_scoring_service=credit_scoring_service
        )
        self.initial_balances[sim.bank.id] = self.config.INITIAL_BANK_ASSETS # Record for distribution

        sim.bank.settlement_system = sim.settlement_system
        sim.agents[sim.bank.id] = sim.bank
        sim.next_agent_id += 1

        sim.government = Government(
            id=sim.next_agent_id,
            initial_assets=0.0,
            config_module=self.config,
            strategy=sim.strategy
        )
        sim.government.settlement_system = sim.settlement_system
        sim.agents[sim.government.id] = sim.government
        sim.next_agent_id += 1

        # Inject government into bank for monetary tracking
        sim.bank.set_government(sim.government)

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
            good_name: OrderBookMarket(market_id=good_name, config_module=self.config)
            for good_name in self.config.GOODS
        }
        sim.markets["labor"] = OrderBookMarket(market_id="labor", config_module=self.config)
        # WO-075 / Phase 31: Security Market for OMO
        sim.markets["security_market"] = OrderBookMarket(market_id="security_market", config_module=self.config)
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

        sim.markets["housing"] = OrderBookMarket(market_id="housing", config_module=self.config)

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

        # WO-124: Genesis Step 3 - Distribution (Atomic Transfer)
        self.logger.info("GENESIS | Starting initial wealth distribution...")
        distributed_count = 0
        for agent_id, amount in self.initial_balances.items():
            if agent_id in sim.agents and amount > 0:
                Bootstrapper.distribute_initial_wealth(
                    central_bank=sim.central_bank,
                    target_agent=sim.agents[agent_id],
                    amount=amount,
                    settlement_system=sim.settlement_system
                )
                distributed_count += 1
        self.logger.info(f"GENESIS | Distributed wealth to {distributed_count} agents.")

        # Phase 22.5 & WO-058: Bootstrap firms BEFORE first update_needs call
        # WO-124: Updated to use SettlementSystem
        Bootstrapper.inject_initial_liquidity(
            firms=sim.firms,
            config=self.config,
            settlement_system=sim.settlement_system,
            central_bank=sim.central_bank
        )

        # TD-115: Establish baseline money supply AFTER all liquidity injection
        # but BEFORE any agent-level activities (hiring, update_needs) begin.
        sim.world_state.central_bank = sim.central_bank # Ensure WorldState has CB ref
        sim.world_state.baseline_money_supply = sim.world_state.calculate_total_money()
        self.logger.info(f"Initial baseline money supply established: {sim.world_state.baseline_money_supply:,.2f}")

        Bootstrapper.force_assign_workers(sim.firms, sim.households)

        for agent in sim.households + sim.firms:
            agent.update_needs(sim.time)
            agent.decision_engine.markets = sim.markets
            agent.decision_engine.goods_data = self.goods_data

        sim.inequality_tracker = InequalityTracker(config_module=self.config)
        sim.personality_tracker = PersonalityStatisticsTracker(config_module=self.config)
        # Initialize with a combined list copy to prevent aliasing sim.households
        # Note: New agents must be explicitly added to this list by lifecycle managers.
        sim.ai_training_manager = AITrainingManager(sim.households + sim.firms, self.config)
        sim.ma_manager = MAManager(sim, self.config, settlement_system=sim.settlement_system)
        sim.demographic_manager = DemographicManager(config_module=self.config, strategy=sim.strategy)
        sim.demographic_manager.settlement_system = sim.settlement_system # Inject SettlementSystem
        sim.immigration_manager = ImmigrationManager(config_module=self.config, settlement_system=sim.settlement_system)
        sim.inheritance_manager = InheritanceManager(config_module=self.config)
        sim.housing_system = HousingSystem(config_module=self.config)
        sim.persistence_manager = PersistenceManager(
            run_id=0,
            config_module=self.config,
            repository=self.repository
        )
        sim.firm_system = FirmSystem(config_module=self.config, strategy=sim.strategy)
        sim.technology_manager = TechnologyManager(config_module=self.config, logger=self.logger, strategy=sim.strategy)

        sim.generational_wealth_audit = GenerationalWealthAudit(config_module=self.config)
        sim.breeding_planner = VectorizedHouseholdPlanner(self.config)

        # WO-124: Initialize Transaction Manager Components
        sim.registry = Registry(logger=self.logger)
        sim.accounting_system = AccountingSystem(logger=self.logger)
        sim.central_bank_system = CentralBankSystem(
            central_bank_agent=sim.central_bank,
            settlement_system=sim.settlement_system,
            logger=self.logger
        )
        sim.handlers = {
            "inheritance_distribution": InheritanceHandler(
                settlement_system=sim.settlement_system,
                logger=self.logger
            )
        }

        # Initialize Escrow Agent (TD-170)
        sim.escrow_agent = EscrowAgent(id=sim.next_agent_id)
        sim.agents[sim.escrow_agent.id] = sim.escrow_agent
        sim.next_agent_id += 1

        sim.transaction_processor = TransactionManager(
            registry=sim.registry,
            accounting_system=sim.accounting_system,
            settlement_system=sim.settlement_system,
            central_bank_system=sim.central_bank_system,
            config=self.config,
            escrow_agent=sim.escrow_agent,
            handlers=sim.handlers,
            logger=self.logger
        )

        # Phase 3: Public Manager
        sim.public_manager = PublicManager(config=self.config)
        sim.world_state.public_manager = sim.public_manager

        # AgentLifecycleManager is created here and injected into the simulation
        sim.lifecycle_manager = AgentLifecycleManager(
            config_module=self.config,
            demographic_manager=sim.demographic_manager,
            inheritance_manager=sim.inheritance_manager,
            firm_system=sim.firm_system,
            settlement_system=sim.settlement_system,
            public_manager=sim.public_manager,
            logger=self.logger
        )

        # Initialize New Systems (Social, Event, Sensory, Commerce, Labor)
        sim.social_system = SocialSystem(self.config)
        sim.event_system = EventSystem(self.config, settlement_system=sim.settlement_system)
        sim.sensory_system = SensorySystem(self.config)
        # sim.settlement_system initialized early
        sim.commerce_system = CommerceSystem(self.config)
        sim.labor_market_analyzer = LaborMarketAnalyzer(self.config)

        # Phase 29: Crisis Monitor
        sim.crisis_monitor = CrisisMonitor(logger=self.logger, run_id=sim.run_id)

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
