from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING
import logging
import hashlib
import json
import os
from collections import deque
if TYPE_CHECKING:
    from simulation.engine import Simulation
from modules.platform.infrastructure.lock_manager import PlatformLockManager, LockAcquisitionError
from modules.common.config_manager.api import ConfigManager
from simulation.initialization.api import SimulationInitializerInterface
from simulation.models import Order, RealEstateUnit
from modules.system.api import DEFAULT_CURRENCY, ICurrencyHolder, OriginType
from modules.system.constants import ID_CENTRAL_BANK, ID_GOVERNMENT, ID_BANK, ID_ESCROW, ID_PUBLIC_MANAGER
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
from simulation.systems.analytics_system import AnalyticsSystem
from simulation.systems.firm_management import FirmSystem
from simulation.systems.technology_manager import TechnologyManager
from simulation.systems.bootstrapper import Bootstrapper
from simulation.systems.generational_wealth_audit import GenerationalWealthAudit
from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.systems.registry import Registry
from simulation.systems.accounting import AccountingSystem
from simulation.systems.central_bank_system import CentralBankSystem
from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from simulation.systems.handlers.labor_handler import LaborTransactionHandler
from simulation.systems.handlers.stock_handler import StockTransactionHandler
from simulation.systems.handlers.asset_transfer_handler import AssetTransferHandler
from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler
from modules.housing.service import HousingService
from simulation.systems.handlers.inheritance_handler import InheritanceHandler
from simulation.systems.handlers.monetary_handler import MonetaryTransactionHandler
from simulation.systems.handlers.financial_handler import FinancialTransactionHandler
from simulation.systems.handlers.escheatment_handler import EscheatmentHandler
from simulation.systems.handlers.government_spending_handler import GovernmentSpendingHandler
from simulation.systems.handlers.emergency_handler import EmergencyTransactionHandler
from simulation.systems.handlers.public_manager_handler import PublicManagerTransactionHandler
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
from modules.labor.system import LaborMarket
from modules.system.escrow_agent import EscrowAgent
from modules.government.taxation.system import TaxationSystem
from modules.analysis.crisis_monitor import CrisisMonitor
from modules.system.execution.public_manager import PublicManager
from modules.finance.kernel.ledger import MonetaryLedger
from modules.finance.sagas.orchestrator import SagaOrchestrator
from modules.finance.shareholder_registry import ShareholderRegistry
from modules.system.event_bus.event_bus import EventBus
from modules.governance.judicial.system import JudicialSystem
from modules.system.registry import AgentRegistry, GlobalRegistry
from modules.household.api import HouseholdFactoryContext
from simulation.factories.household_factory import HouseholdFactory
from simulation.utils.config_factory import create_config_dto
from modules.simulation.dtos.api import HouseholdConfigDTO

class SimulationInitializer(SimulationInitializerInterface):
    """Simulation 인스턴스 생성 및 모든 구성 요소의 초기화를 전담합니다."""

    def __init__(self, config_manager: ConfigManager, config_module: Any, goods_data: List[Dict[str, Any]], repository: SimulationRepository, logger: logging.Logger, households: List[Household], firms: List[Firm], ai_trainer: AIEngineRegistry, initial_balances: Optional[Dict[int, float]]=None):
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
        # Cross-Platform Locking Mechanism (Wave 1.5)
        lock_manager = PlatformLockManager('simulation.lock')
        try:
            lock_manager.acquire()
        except LockAcquisitionError:
            self.logger.error('Another simulation instance is already running (locked by simulation.lock).')
            raise RuntimeError('Simulation is already running.')

        global_registry = GlobalRegistry()
        agent_registry = AgentRegistry()
        settlement_system = SettlementSystem(logger=self.logger, agent_registry=agent_registry)
        from modules.system.services.command_service import CommandService
        command_service = CommandService(registry=global_registry, settlement_system=settlement_system, agent_registry=agent_registry)
        sim = Simulation(config_manager=self.config_manager, config_module=self.config, logger=self.logger, repository=self.repository, registry=global_registry, settlement_system=settlement_system, agent_registry=agent_registry, command_service=command_service)

        # sim.agent_registry.set_state(sim.world_state) # DEFERRED to end of build_simulation

        sim.lock_manager = lock_manager
        sim.event_bus = EventBus()
        sim.world_state.taxation_system = TaxationSystem(config_module=self.config)
        from modules.system.telemetry import TelemetryCollector
        sim.telemetry_collector = TelemetryCollector(sim.world_state.global_registry)
        sim.world_state.telemetry_collector = sim.telemetry_collector
        sim.world_state.global_registry.set('system.telemetry_collector', sim.telemetry_collector, origin=OriginType.SYSTEM)
        sim.monetary_ledger = MonetaryLedger(sim.world_state.transactions, sim)
        sim.saga_orchestrator = SagaOrchestrator(monetary_ledger=sim.monetary_ledger)
        sim.world_state.monetary_ledger = sim.monetary_ledger
        sim.world_state.saga_orchestrator = sim.saga_orchestrator
        sim.shareholder_registry = ShareholderRegistry()
        sim.world_state.shareholder_registry = sim.shareholder_registry
        sim.tracker = EconomicIndicatorTracker(config_module=self.config)
        from simulation.dtos.strategy import ScenarioStrategy
        active_scenario_name = self.config_manager.get('simulation.active_scenario')
        strategy = ScenarioStrategy()
        if active_scenario_name:
            scenario_path = f'config/scenarios/{active_scenario_name}.json'
            if os.path.exists(scenario_path):
                try:
                    with open(scenario_path, 'r') as f:
                        scenario_data = json.load(f)
                    params = scenario_data.get('parameters', {})

                    def resolve(keys, default=None):
                        for k in keys:
                            if k in params and params[k] is not None:
                                return params[k]
                        return default
                    strategy = ScenarioStrategy(name=active_scenario_name, is_active=scenario_data.get('is_active', False), start_tick=scenario_data.get('start_tick', 50), scenario_name=scenario_data.get('scenario_name', active_scenario_name), inflation_expectation_multiplier=resolve(['inflation_expectation_multiplier'], 1.0), hoarding_propensity_factor=resolve(['hoarding_propensity_factor'], 0.0), demand_shock_cash_injection=resolve(['demand_shock_cash_injection'], 0.0), panic_selling_enabled=resolve(['panic_selling_enabled'], False), debt_aversion_multiplier=resolve(['debt_aversion_multiplier'], 1.0), consumption_pessimism_factor=resolve(['consumption_pessimism_factor'], 0.0), asset_shock_reduction=resolve(['asset_shock_reduction'], 0.0), exogenous_productivity_shock=resolve(['exogenous_productivity_shock'], {}), monetary_shock_target_rate=resolve(['monetary_shock_target_rate', 'MONETARY_SHOCK_TARGET_RATE']), fiscal_shock_tax_rate=resolve(['fiscal_shock_tax_rate', 'FISCAL_SHOCK_TAX_RATE']), base_interest_rate_multiplier=resolve(['base_interest_rate_multiplier']), corporate_tax_rate_delta=resolve(['corporate_tax_rate_delta']), demand_shock_multiplier=resolve(['demand_shock_multiplier']), tfp_multiplier=resolve(['TFP_MULTIPLIER', 'food_tfp_multiplier'], 3.0), tech_fertilizer_unlock_tick=resolve(['TECH_FERTILIZER_UNLOCK_TICK'], 50), tech_diffusion_rate=resolve(['TECH_DIFFUSION_RATE'], 0.05), food_sector_config=resolve(['FOOD_SECTOR_CONFIG'], {}), market_config=resolve(['MARKET_CONFIG'], {}), deflationary_pressure_multiplier=resolve(['DEFLATIONARY_PRESSURE_MULTIPLIER'], 1.0), limits=resolve(['LIMITS'], {}), firm_decision_engine=resolve(['FIRM_DECISION_ENGINE']), household_decision_engine=resolve(['HOUSEHOLD_DECISION_ENGINE']), initial_base_interest_rate=resolve(['base_interest_rate', 'INITIAL_BASE_ANNUAL_RATE']), initial_corporate_tax_rate=resolve(['tax_rate_corporate', 'CORPORATE_TAX_RATE']), initial_income_tax_rate=resolve(['tax_rate_income', 'INCOME_TAX_RATE']), newborn_engine_type=resolve(['newborn_engine_type', 'NEWBORN_ENGINE_TYPE']), firm_decision_mode=resolve(['firm_decision_mode']), innovation_weight=resolve(['innovation_weight']), parameters=params)
                    self.logger.info(f'Loaded Scenario Strategy: {strategy.name} (Active: {strategy.is_active})')
                    if strategy.initial_corporate_tax_rate:
                        self.logger.debug(f'Initial Corporate Tax Rate set to {strategy.initial_corporate_tax_rate} via strategy.')
                    if strategy.tfp_multiplier:
                        self.logger.debug(f'TFP Multiplier set to {strategy.tfp_multiplier} via strategy.')
                except Exception as e:
                    self.logger.error(f"Failed to load scenario file '{scenario_path}': {e}")
            else:
                self.logger.warning(f"Active scenario '{active_scenario_name}' requested but {scenario_path} not found.")
        sim.strategy = strategy
        sim.stress_scenario_config = strategy
        sim.world_state.stress_scenario_config = strategy
        sim.central_bank = CentralBank(tracker=sim.tracker, config_module=self.config, strategy=sim.strategy)
        sim.central_bank.deposit(int(self.config.INITIAL_MONEY_SUPPLY))
        self.logger.info(f'GENESIS | Central Bank minted M0: {self.config.INITIAL_MONEY_SUPPLY:,.2f}')
        sim.households = self.households
        sim.firms = self.firms
        sim.goods_data = self.goods_data
        sim.agents: Dict[int, Any] = {h.id: h for h in self.households}
        sim.agents.update({f.id: f for f in self.firms})

        # Determine next available ID (assuming user agents start > 100)
        max_user_id = 0
        if sim.agents:
            max_user_id = max(sim.agents.keys())
        sim.next_agent_id = max(100, max_user_id + 1)

        for agent in sim.agents.values():
            agent.settlement_system = sim.settlement_system
        sim.ai_trainer = self.ai_trainer
        sim.time: int = 0
        credit_scoring_service = CreditScoringService(config_module=self.config)

        # Initialize System Agents with Fixed IDs
        sim.bank = Bank(id=ID_BANK, initial_assets=0, config_manager=self.config_manager, settlement_system=sim.settlement_system, credit_scoring_service=credit_scoring_service, event_bus=sim.event_bus)
        sim.settlement_system.bank = sim.bank
        self.initial_balances[sim.bank.id] = self.config.INITIAL_BANK_ASSETS
        sim.bank.settlement_system = sim.settlement_system
        sim.agents[sim.bank.id] = sim.bank

        gov = Government(id=ID_GOVERNMENT, initial_assets=0.0, config_module=self.config, strategy=sim.strategy)
        sim.world_state.government = gov
        sim.government.settlement_system = sim.settlement_system
        sim.agents[sim.government.id] = sim.government
        sim.bank.set_government(sim.government)

        # Register Central Bank (Created earlier)
        if hasattr(sim, 'central_bank') and sim.central_bank:
             # Central Bank ID is handled internally by the class, but we register it here
             # to ensure it exists in the primary agent lookup table.
             sim.agents[ID_CENTRAL_BANK] = sim.central_bank

        # TD-INIT-RACE: Registry must be linked BEFORE Bootstrapper runs.
        # Now that System Agents (Gov, Bank, CB) are in sim.agents, we link the registry.
        sim.agent_registry.set_state(sim.world_state)

        sim.finance_system = FinanceSystem(government=sim.government, central_bank=sim.central_bank, bank=sim.bank, config_module=self.config_manager, settlement_system=sim.settlement_system)
        sim.government.finance_system = sim.finance_system
        sim.bank.set_finance_system(sim.finance_system)
        sim.real_estate_units: List[RealEstateUnit] = [RealEstateUnit(id=i, estimated_value=self.config.INITIAL_PROPERTY_VALUE, rent_price=self.config.INITIAL_RENT_PRICE) for i in range(self.config.NUM_HOUSING_UNITS)]
        top_20_count = len(sim.households) // 5
        top_households = sorted(sim.households, key=lambda h: h.get_balance(DEFAULT_CURRENCY), reverse=True)[:top_20_count]
        for i, hh in enumerate(top_households):
            if i < len(sim.real_estate_units):
                unit = sim.real_estate_units[i]
                unit.owner_id = hh.id
                hh._econ_state.owned_properties.append(unit.id)
                unit.occupant_id = hh.id
                hh._econ_state.residing_property_id = unit.id
                hh._econ_state.is_homeless = False
        sim.markets: Dict[str, Market] = {good_name: OrderBookMarket(market_id=good_name, config_module=self.config) for good_name in self.config.GOODS}
        sim.markets['labor'] = LaborMarket(market_id='labor', config_module=self.config)
        sim.markets['security_market'] = OrderBookMarket(market_id='security_market', config_module=self.config)
        sim.markets['loan_market'] = LoanMarket(market_id='loan_market', bank=sim.bank, config_module=self.config)
        sim.markets['loan_market'].agents_ref = sim.agents
        if getattr(self.config, 'STOCK_MARKET_ENABLED', False):
            sim.stock_market = StockMarket(config_module=self.config, shareholder_registry=sim.shareholder_registry, logger=self.logger)
            sim.stock_tracker = StockMarketTracker(config_module=self.config)
            sim.markets['stock_market'] = sim.stock_market
            for firm in sim.firms:
                if hasattr(firm, 'init_ipo'):
                    firm.init_ipo(sim.stock_market)
        else:
            sim.stock_market = None
            sim.stock_tracker = None
        sim.markets['housing'] = OrderBookMarket(market_id='housing', config_module=self.config)
        for unit in sim.real_estate_units:
            if unit.owner_id is None:
                sell_order = Order(
                    agent_id=sim.government.id,
                    item_id=f'unit_{unit.id}',
                    price_pennies=unit.estimated_value,
                    price_limit=unit.estimated_value / 100.0,
                    quantity=1.0,
                    market_id='housing',
                    side='SELL'
                )
                if 'housing' in sim.markets:
                    sim.markets['housing'].place_order(sell_order, sim.time)
        self.logger.info('GENESIS | Starting initial wealth distribution...')
        distributed_count = 0
        for agent_id, amount in self.initial_balances.items():
            if agent_id in sim.agents and amount > 0:
                Bootstrapper.distribute_initial_wealth(central_bank=sim.central_bank, target_agent=sim.agents[agent_id], amount=int(amount), settlement_system=sim.settlement_system)
                distributed_count += 1
        self.logger.info(f'GENESIS | Distributed wealth to {distributed_count} agents.')
        Bootstrapper.inject_initial_liquidity(firms=sim.firms, config=self.config, settlement_system=sim.settlement_system, central_bank=sim.central_bank)
        sim.world_state.central_bank = sim.central_bank
        total_money = sim.world_state.calculate_total_money()
        if isinstance(total_money, dict):
            sim.world_state.baseline_money_supply = total_money.get(DEFAULT_CURRENCY, 0.0)
        else:
            sim.world_state.baseline_money_supply = float(total_money)
        self.logger.info(f'Initial baseline money supply established: {sim.world_state.baseline_money_supply:,.2f}')
        Bootstrapper.force_assign_workers(sim.firms, sim.households)
        for agent in sim.households + sim.firms:
            agent.update_needs(sim.time)
            agent.decision_engine.markets = sim.markets
            agent.decision_engine.goods_data = self.goods_data
        sim.inequality_tracker = InequalityTracker(config_module=self.config)
        sim.personality_tracker = PersonalityStatisticsTracker(config_module=self.config)
        sim.ai_training_manager = AITrainingManager(sim.households + sim.firms, self.config)
        sim.ma_manager = MAManager(sim, self.config, settlement_system=sim.settlement_system)
        sim.persistence_manager = PersistenceManager(run_id=0, config_module=self.config, repository=self.repository)
        hh_config_dto = create_config_dto(self.config, HouseholdConfigDTO)
        hh_factory_context = HouseholdFactoryContext(core_config_module=self.config, household_config_dto=hh_config_dto, goods_data=self.goods_data, loan_market=sim.markets.get('loan_market'), ai_training_manager=sim.ai_training_manager, settlement_system=sim.settlement_system, markets=sim.markets, memory_system=sim.persistence_manager, central_bank=sim.central_bank)
        household_factory = HouseholdFactory(hh_factory_context)
        sim.demographic_manager = DemographicManager(config_module=self.config, strategy=sim.strategy, household_factory=household_factory)
        sim.demographic_manager.settlement_system = sim.settlement_system
        household_factory.context.demographic_manager = sim.demographic_manager
        for hh in sim.households:
            if hasattr(hh, 'demographic_manager'):
                hh.demographic_manager = sim.demographic_manager
        sim.demographic_manager.sync_stats(sim.households)
        sim.demographic_manager.set_world_state(sim.world_state)
        sim.world_state.global_registry.set('demographics', sim.demographic_manager, origin=OriginType.SYSTEM)
        sim.immigration_manager = ImmigrationManager(config_module=self.config, settlement_system=sim.settlement_system)
        sim.inheritance_manager = InheritanceManager(config_module=self.config)
        sim.housing_system = HousingSystem(config_module=self.config)
        sim.analytics_system = AnalyticsSystem()
        sim.firm_system = FirmSystem(config_module=self.config, strategy=sim.strategy)
        sim.technology_manager = TechnologyManager(config_module=self.config, logger=self.logger, strategy=sim.strategy)
        sim.generational_wealth_audit = GenerationalWealthAudit(config_module=self.config)
        sim.breeding_planner = VectorizedHouseholdPlanner(self.config)
        sim.housing_service = HousingService(logger=self.logger)
        sim.housing_service.set_real_estate_units(sim.real_estate_units)
        sim.registry = Registry(housing_service=sim.housing_service, logger=self.logger)
        sim.accounting_system = AccountingSystem(logger=self.logger)
        sim.central_bank_system = CentralBankSystem(central_bank_agent=sim.central_bank, settlement_system=sim.settlement_system, logger=self.logger)

        sim.escrow_agent = EscrowAgent(id=ID_ESCROW)
        sim.agents[sim.escrow_agent.id] = sim.escrow_agent

        sim.judicial_system = JudicialSystem(event_bus=sim.event_bus, settlement_system=sim.settlement_system, agent_registry=sim.agent_registry, shareholder_registry=sim.shareholder_registry, config_manager=self.config_manager)
        sim.public_manager = PublicManager(config=self.config)
        # Verify and Register PublicManager
        if hasattr(sim.public_manager, 'id') and sim.public_manager.id == ID_PUBLIC_MANAGER:
            sim.agents[ID_PUBLIC_MANAGER] = sim.public_manager

        sim.world_state.public_manager = sim.public_manager
        sim.transaction_processor = TransactionProcessor(config_module=self.config)
        sim.transaction_processor.register_handler('goods', GoodsTransactionHandler())
        sim.transaction_processor.register_handler('labor', LaborTransactionHandler())
        sim.transaction_processor.register_handler('HIRE', LaborTransactionHandler()) # Phase 4.1: Major-Matching
        sim.transaction_processor.register_handler('wage', LaborTransactionHandler())
        sim.transaction_processor.register_handler('research_labor', LaborTransactionHandler())
        sim.transaction_processor.register_handler('stock', StockTransactionHandler())
        sim.transaction_processor.register_handler('asset_transfer', AssetTransferHandler())
        sim.transaction_processor.register_handler('housing', HousingTransactionHandler())
        monetary_handler = MonetaryTransactionHandler()
        sim.transaction_processor.register_handler('lender_of_last_resort', monetary_handler)
        sim.transaction_processor.register_handler('asset_liquidation', monetary_handler)
        sim.transaction_processor.register_handler('bond_purchase', monetary_handler)
        sim.transaction_processor.register_handler('bond_repayment', monetary_handler)
        sim.transaction_processor.register_handler('omo_purchase', monetary_handler)
        sim.transaction_processor.register_handler('omo_sale', monetary_handler)
        sim.transaction_processor.register_handler('bond_interest', monetary_handler)
        financial_handler = FinancialTransactionHandler()
        sim.transaction_processor.register_handler('interest_payment', financial_handler)
        sim.transaction_processor.register_handler('loan_interest', financial_handler)
        sim.transaction_processor.register_handler('deposit_interest', financial_handler)
        sim.transaction_processor.register_handler('dividend', financial_handler)
        sim.transaction_processor.register_handler('tax', financial_handler)
        sim.transaction_processor.register_handler('deposit', financial_handler)
        sim.transaction_processor.register_handler('withdrawal', financial_handler)
        sim.transaction_processor.register_handler('bank_profit_remittance', financial_handler)
        sim.transaction_processor.register_handler('holding_cost', financial_handler)
        sim.transaction_processor.register_handler('repayment', financial_handler)
        sim.transaction_processor.register_handler('loan_repayment', financial_handler)
        sim.transaction_processor.register_handler('investment', financial_handler)
        sim.transaction_processor.register_handler('escheatment', EscheatmentHandler())
        sim.transaction_processor.register_handler('inheritance_distribution', InheritanceHandler())
        spending_handler = GovernmentSpendingHandler()
        sim.transaction_processor.register_handler('infrastructure_spending', spending_handler)
        sim.transaction_processor.register_handler('welfare', spending_handler)
        sim.transaction_processor.register_handler('marketing', spending_handler)
        sim.transaction_processor.register_handler('emergency_buy', EmergencyTransactionHandler())
        sim.transaction_processor.register_public_manager_handler(PublicManagerTransactionHandler())
        sim.lifecycle_manager = AgentLifecycleManager(config_module=self.config, demographic_manager=sim.demographic_manager, inheritance_manager=sim.inheritance_manager, firm_system=sim.firm_system, settlement_system=sim.settlement_system, public_manager=sim.public_manager, logger=self.logger, shareholder_registry=sim.shareholder_registry, household_factory=household_factory)
        sim.social_system = SocialSystem(self.config)
        sim.event_system = EventSystem(self.config, settlement_system=sim.settlement_system)
        sim.sensory_system = SensorySystem(self.config)
        sim.commerce_system = CommerceSystem(self.config)
        sim.labor_market_analyzer = LaborMarketAnalyzer(self.config)
        sim.crisis_monitor = CrisisMonitor(logger=self.logger, run_id=sim.run_id)
        sim.household_time_allocation: Dict[int, float] = {}
        if isinstance(sim.central_bank, ICurrencyHolder):
            sim.world_state.register_currency_holder(sim.central_bank)
        for agent in sim.agents.values():
            if isinstance(agent, ICurrencyHolder):
                sim.world_state.register_currency_holder(agent)
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
        sim.run_id = self.repository.runs.save_simulation_run(config_hash=config_hash, description='Economic simulation run with DB storage')
        sim.persistence_manager.run_id = sim.run_id
        sim.crisis_monitor.run_id = sim.run_id
        self.logger.info(f'Simulation run started with run_id: {sim.run_id}', extra={'run_id': sim.run_id})

        from modules.analysis.scenario_verifier.engine import ScenarioVerifier
        from modules.analysis.scenario_verifier.judges.sc001_female_labor import FemaleLaborParticipationJudge
        sim.scenario_verifier = ScenarioVerifier(judges=[FemaleLaborParticipationJudge()])
        sim.scenario_verifier.initialize(sim.telemetry_collector)
        sim.world_state.scenario_verifier = sim.scenario_verifier

        # Inject Metrics Service and Panic Recorder (WorldState implements IEconomicMetricsService and IPanicRecorder)
        if hasattr(sim.settlement_system, 'set_metrics_service'):
             sim.settlement_system.set_metrics_service(sim.world_state)
        
        if hasattr(sim.settlement_system, 'set_panic_recorder'):
             sim.settlement_system.set_panic_recorder(sim.world_state)

        # TD-FIN-INVISIBLE-HAND: Ensure system agents are registered before Snapshot
        self.logger.info("LATE_INITIALIZATION | Finalizing AgentRegistry state snapshot.")
        # sim.agent_registry.set_state(sim.world_state) # MOVED up before Bootstrapper

        self.logger.info(f'Simulation fully initialized with run_id: {sim.run_id}')
        return sim