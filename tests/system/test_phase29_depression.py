
import unittest
import os
import shutil
import csv
from unittest.mock import MagicMock, Mock, PropertyMock
from simulation.initialization.initializer import SimulationInitializer
from modules.common.config_manager.api import ConfigManager
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.db.repository import SimulationRepository
from simulation.ai_model import AIEngineRegistry
from modules.system.api import DEFAULT_CURRENCY
import logging

class TestPhase29Depression(unittest.TestCase):
    def setUp(self):
        # Setup Logger
        self.logger = logging.getLogger("TestPhase29")
        logging.basicConfig(level=logging.INFO)

        # Setup ConfigManager with Mock Config
        self.config_manager = MagicMock(spec=ConfigManager)
        # Mocking get method to return appropriate values
        def config_get_side_effect(key, default=None):
            if key == "bank_defaults.initial_base_annual_rate":
                return 0.05
            if key == "simulation.household_consumable_goods":
                return ["food", "electronics"]
            return default
        self.config_manager.get.side_effect = config_get_side_effect

        self.config_module = MagicMock()

        # Configure Mock using configure_mock to ensure attributes are set correctly
        self.config_module.configure_mock(
            FISCAL_SENSITIVITY_ALPHA=0.5, # Ensure float
            AUTO_COUNTER_CYCLICAL_ENABLED=True,
            GOODS={"food": {"initial_price": 10}, "electronics": {"initial_price": 50}},
            INITIAL_BANK_ASSETS=1000000,
            INITIAL_MONEY_SUPPLY=1000000, # Explicitly set here too, but will enforce below
            INITIAL_PROPERTY_VALUE=10000,
            INITIAL_RENT_PRICE=100,
            NUM_HOUSING_UNITS=10,
            LABOR_MARKET_MIN_WAGE=10,
            MAX_WORK_HOURS=12,
            IMITATION_LEARNING_INTERVAL=10,
            SIMULATION_TICK_LIMIT=100,
            DEFAULT_INFLATION_RATE=0.02,
            SHOPPING_HOURS=2,
            HOURS_PER_TICK=24,
            INFRASTRUCTURE_TFP_BOOST=0.05,
            CRITICAL_CARBS_LEVEL=10,
            CRITICAL_PROTEIN_LEVEL=10,
            CRITICAL_FAT_LEVEL=10,
            DAILY_CARBS_NEED=2,
            DAILY_PROTEIN_NEED=2,
            DAILY_FAT_NEED=2,
            SURVIVAL_DAILY_CALORIES=50,
            MACRO_PORTFOLIO_ADJUSTMENT_ENABLED=False,
            STOCK_MARKET_ENABLED=False,
            ENABLE_VANITY_SYSTEM=False,
            PRODUCTION_TAX_RATE=0.1,
            SALES_TAX_RATE=0.1,
            INCOME_TAX_RATE=0.1,
            CORPORATE_TAX_RATE=0.2,
            BANK_DEFAULTS_RATE=0.05,
            INITIAL_BASE_ANNUAL_RATE=0.05,
            CB_UPDATE_INTERVAL=10,
            CB_INFLATION_TARGET=0.02,
            CB_TAYLOR_ALPHA=1.5,
            CB_TAYLOR_BETA=0.5,
            CB_NEUTRAL_RATE=0.02,
            MIN_BASE_RATE=0.0,
            MAX_BASE_RATE=0.2,
            HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK=1.0,
            GOODS_INITIAL_PRICE={"basic_food": 5.0},
            ANNUAL_WEALTH_TAX_RATE=0.02,
            TICKS_PER_YEAR=100.0,
            WEALTH_TAX_THRESHOLD=50000.0,
            UNEMPLOYMENT_BENEFIT_RATIO=0.8,
            QE_INTERVENTION_YIELD_THRESHOLD=0.10,
            DEBT_RISK_PREMIUM_TIERS={1.2: 0.05, 0.9: 0.02, 0.6: 0.005},
            BOND_MATURITY_TICKS=400,
            SURVIVAL_NEED_DEATH_THRESHOLD=100.0,
            SURVIVAL_NEED_CONSUMPTION_THRESHOLD=50.0,
            FOOD_CONSUMPTION_QUANTITY=1.0,
            FOOD_PURCHASE_MAX_PER_TICK=5.0,
            MAINTENANCE_RATE_PER_TICK=0.001,
            CHILD_MONTHLY_COST=500.0,
            OPPORTUNITY_COST_FACTOR=0.3,
            CHILD_EMOTIONAL_VALUE_BASE=500000.0,
            TECH_CONTRACEPTION_ENABLED=True,
            BIOLOGICAL_FERTILITY_RATE=0.15,
            POPULATION_IMMIGRATION_THRESHOLD=80,
            INFRASTRUCTURE_INVESTMENT_COST=5000.0,
            REPRODUCTION_AGE_START=200, # Prevent births
            REPRODUCTION_AGE_END=45,
            BANKRUPTCY_LOSS_THRESHOLD=10,
            MA_ENABLED=True,
            HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD=0.7,
            MITOSIS_MUTATION_PROBABILITY=0.1,
            INFLATION_MEMORY_WINDOW=10,
            PUBLIC_EDU_BUDGET_RATIO=0.20,
            CONFORMITY_RANGES={},
            INITIAL_HOUSEHOLD_ASSETS_MEAN=1000.0,
            EDUCATION_COST_PER_LEVEL={1: 500},
            SCHOLARSHIP_WEALTH_PERCENTILE=0.20,
            SCHOLARSHIP_POTENTIAL_THRESHOLD=0.7,
            LIQUIDITY_NEED_INCREASE_RATE=1.0,
            ASSETS_CLOSURE_THRESHOLD=0.0,
            FIRM_CLOSURE_TURNS_THRESHOLD=5,
            # Added for WO-023 and DTO compliance
            TARGET_FOOD_BUFFER_QUANTITY=5.0,
            WAGE_DECAY_RATE=0.02,
            RESERVATION_WAGE_FLOOR=0.3,
            SURVIVAL_CRITICAL_TURNS=5,
            PRIMARY_SURVIVAL_GOOD_ID="basic_food",
            HOUSEHOLD_LOW_ASSET_THRESHOLD=100.0,
            HOUSEHOLD_LOW_ASSET_WAGE=8.0,
            HOUSEHOLD_DEFAULT_WAGE=10.0,
            SURVIVAL_NEED_EMERGENCY_THRESHOLD=80.0,
            SURVIVAL_BID_PREMIUM=0.2,
            # Added for FirmConfigDTO completeness
            MARKET_CIRCUIT_BREAKER_BASE_LIMIT=0.15,
            CIRCUIT_BREAKER_MIN_HISTORY=7,
        )

        # Create dummy agents
        self.households = [MagicMock(spec=Household) for _ in range(5)]
        for i, h in enumerate(self.households):
            h.id = i
            h._bio_state = MagicMock() # Needs explicit sub-mock with spec
            h._econ_state = MagicMock()
            h._social_state = MagicMock()
            h._bio_state.is_active = True
            h._econ_state.employer_id = None
            h._econ_state.is_employed = False
            h._bio_state.age = 25
            h.age = 25  # Explicitly set property
            h.income = 100
            h._econ_state.current_consumption = 0.0
            h._econ_state.current_food_consumption = 0.0
            h._econ_state.labor_income_this_tick = 0.0
            h._econ_state.education_level = 1.0
            h._econ_state.aptitude = 0.5
            h._econ_state.current_wage = 10.0
            h.current_wage = 10.0
            h._bio_state.children_ids = []
            h.children_ids = []
            h._bio_state.needs = {"survival": 0.5}
            h._assets = 1000
            h.decision_engine = MagicMock()
            h.decision_engine.ai_engine = MagicMock()
            # make_decision must return (orders, action_vector)
            mock_action_vector = MagicMock()
            mock_action_vector.work_aggressiveness = 0.5
            h.make_decision.return_value = ([], mock_action_vector)
            h._econ_state.inventory = {}
            h._econ_state.owned_properties = []
            h._econ_state.residing_property_id = None
            h._social_state.approval_rating = 1.0
            h._econ_state.wallet = MagicMock()
            h._econ_state.wallet.get_balance.return_value = 1000.0
            h._econ_state.wallet.get_all_balances.return_value = {DEFAULT_CURRENCY: 1000.0}
            h.get_balance.return_value = 1000.0
            h.get_all_balances.return_value = {DEFAULT_CURRENCY: 1000.0}
            h.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 1000.0}
            h.config = self.config_module
            # For numpy array creation in VectorizedHouseholdPlanner
            h.current_wage = 10.0
            h.monthly_income = 1600.0
            h.children_ids = []
            h.age = 25.0
            h.current_wage = 10.0

            # configure_mock with attributes
            h.configure_mock(monthly_income=1600.0, current_wage=10.0, children_ids=[], age=25.0)

            # Ensure magic methods don't return Mocks for len()
            # h.__len__ = Mock(return_value=1)

            # configure_mock with attributes
            h.configure_mock(monthly_income=1600.0, current_wage=10.0, children_ids=[], age=25.0)

            # PropertyMock works on the type, but might conflict if the object spec already has these attributes
            # Let's remove the problematic code and rely on the fact that we fixed the TypeError by other means,
            # or simply try configure_mock again without side effects on magic methods.

            # Since numpy array creation from mocks is notoriously tricky,
            # and we just want to bypass the breeding check, let's stick to mocking the planner call for this test.
            # It's cleaner and avoids fighting the mock system.
            pass

            # Configure get_sensory_snapshot to be callable and return dict
            h.get_sensory_snapshot = MagicMock(return_value={"total_wealth": 1000.0, "approval_rating": 1.0, "is_active": True})

            # Use PropertyMock to force numpy to see the values
            # This must be done AFTER any other configuration that might reset the mock
            p_wage = PropertyMock(return_value=10.0)
            type(h).current_wage = p_wage

            p_income = PropertyMock(return_value=1600.0)
            type(h).monthly_income = p_income

            p_age = PropertyMock(return_value=25.0)
            type(h).age = p_age

            p_children = PropertyMock(return_value=[])
            type(h).children_ids = p_children

        self.firms = [MagicMock(spec=Firm) for _ in range(5)]
        for i, f in enumerate(self.firms):
            f.id = 100 + i
            f.type = "ConsumerGoodFirm"
            f.sector = "consumer_goods"
            f.specialization = "food" if i % 2 == 0 else "electronics"
            f.is_active = True
            f.age = 0
            f._assets = 5000
            f.current_profit = 100
            f.consecutive_loss_turns = 0
            f.valuation = 5000.0
            f.get_market_cap.return_value = 5000.0
            f.current_production = 0.0
            f.sales_volume_this_tick = 0.0
            f.inventory = {"food": 0.0, "electronics": 0.0}
            f.retained_earnings = 1000.0
            f.total_debt = 0.0
            f.decision_engine = MagicMock()
            f.decision_engine.ai_engine = MagicMock()
            # make_decision must return (orders, action_vector)
            f.make_decision.return_value = ([], MagicMock())
            f.inventory = {f.specialization: 10}
            f.get_quantity.side_effect = lambda k: f.inventory.get(k, 0.0)
            f.wallet.get_balance.return_value = 5000.0
            f.needs = {"liquidity_need": 0.0} # Needs initialization
            f.price = 10
            f.productivity_factor = 1.0
            f.hr = MagicMock()
            f.hr.employees = []
            f.hr_state = MagicMock()
            f.hr_state.employees = []
            f.hr_engine = MagicMock()
            f.config = MagicMock()
            f.config.profit_history_ticks = 10
            f.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 5000.0}
            f.get_balance.return_value = 5000.0
            f.get_all_balances.return_value = {DEFAULT_CURRENCY: 5000.0}

            # Phase 29 Refinement: Mock FinanceDepartment
            f.finance = MagicMock()
            f.finance_state = MagicMock()
            f.finance_state.consecutive_loss_turns = 0
            f.finance_engine = MagicMock()
            f.production_state = MagicMock()
            f.sales_state = MagicMock()
            f.finance.balance = 5000.0  # Initialize balance (fix for Bootstrapper)
            f.finance.consecutive_loss_turns = 0
            f.finance.current_profit = 100.0
            f.finance.calculate_altman_z_score.return_value = 3.0
            f.finance.calculate_valuation.return_value = 5000.0
            f.finance_state.valuation = 5000.0
            f.finance.get_inventory_value.return_value = 0.0
            f.finance.check_cash_crunch.return_value = False
            f.get_sensory_snapshot.return_value = {"total_wealth": 5000.0, "approval_rating": 0.0, "is_active": True}

            # Phase 29 Refinement: Mock get_financial_snapshot
            f.get_financial_snapshot.return_value = {
                "total_assets": 5500.0,
                "working_capital": 5500.0,
                "retained_earnings": 1000.0,
                "average_profit": 100.0,
                "total_debt": 0.0
            }

        self.repository = MagicMock(spec=SimulationRepository)
        self.repository.runs = MagicMock()
        self.repository.analytics = MagicMock()
        self.repository.agents = MagicMock()
        self.repository.markets = MagicMock()
        self.repository.runs.save_simulation_run.return_value = "test_run"
        self.ai_trainer = MagicMock(spec=AIEngineRegistry)

        # Create Initializer
        self.initializer = SimulationInitializer(
            config_manager=self.config_manager,
            config_module=self.config_module,
            goods_data=[{"id": "food", "name": "food"}, {"id": "electronics", "name": "electronics"}],
            repository=self.repository,
            logger=self.logger,
            households=self.households,
            firms=self.firms,
            ai_trainer=self.ai_trainer
        )

        # Build Simulation
        self.sim = self.initializer.build_simulation()
        self.sim.run_id = "test_run"

        # Fix: Mock GDP for Taylor Rule to return floats
        # Mocking the property access which might be nested
        self.sim.government.sensory_data = MagicMock()
        # Mock as attributes for direct access if used
        self.sim.government.sensory_data.current_gdp = 1000.0
        self.sim.government.sensory_data.potential_gdp = 1000.0
        # Ensure that it persists on the government instance
        self.sim.government.get_sensory_snapshot = MagicMock(return_value=self.sim.government.sensory_data)

        # Set Government Revenue
        if self.sim.government:
            self.sim.government._deposit(10000)

        # Mock TechnologyManager to avoid config dependency issues
        self.sim.technology_manager = MagicMock()

        # Mock CommerceSystem to avoid VectorizedHouseholdPlanner issues in mock environment
        self.sim.commerce_system = MagicMock()
        self.sim.commerce_system.execute_consumption_and_leisure.return_value = {}
        self.sim.commerce_system.plan_consumption_and_leisure.return_value = ({}, [])

        # Manually fix MAManager config issue
        if self.sim.ma_manager:
            self.sim.ma_manager.bankruptcy_loss_threshold = 10

        # Patch VectorizedHouseholdPlanner to avoid numpy/mock issues in breeding logic
        # We replace the instance used by the lifecycle manager with a mock
        if self.sim.lifecycle_manager:
            mock_planner = MagicMock()
            # decide_breeding_batch returns list of booleans
            mock_planner.decide_breeding_batch.side_effect = lambda agents: [False] * len(agents)
            self.sim.lifecycle_manager.breeding_planner = mock_planner

        # Ensure Phase 29 Scenario is Active and Configured
        if not self.sim.stress_scenario_config.is_active:
             print("WARNING: Scenario not loaded from file during test setup. Manually enabling.")
             self.sim.stress_scenario_config.is_active = True
             self.sim.stress_scenario_config.scenario_name = "phase29_depression"
             self.sim.stress_scenario_config.start_tick = 50
             self.sim.stress_scenario_config.monetary_shock_target_rate = 0.08
             self.sim.stress_scenario_config.fiscal_shock_tax_rate = 0.30

    def tearDown(self):
        # Cleanup reports
        if hasattr(self.sim, 'run_id'):
            report_file = f"reports/crisis_monitor_{self.sim.run_id}.csv"
            if os.path.exists(report_file):
                os.remove(report_file)

    def test_depression_scenario_triggers(self):
        """Test that shocks are applied at start_tick."""

        # Verify initial state
        initial_base_rate = self.sim.bank.base_rate
        initial_tax_rate = self.sim.government.corporate_tax_rate
        print(f"Initial State: Base Rate={initial_base_rate}, Tax Rate={initial_tax_rate}")

        # Run until before shock
        start_tick = self.sim.stress_scenario_config.start_tick
        print(f"Running until tick {start_tick}...")

        for _ in range(start_tick):
            self.sim.run_tick()

        # Verify shock applied
        current_base_rate = self.sim.bank.base_rate
        current_tax_rate = self.sim.government.corporate_tax_rate

        print(f"Tick {self.sim.time} State: Base Rate={current_base_rate}, Tax Rate={current_tax_rate}")

        self.assertAlmostEqual(current_base_rate, 0.08, delta=0.005, msg="Monetary Shock failed")
        self.assertAlmostEqual(current_tax_rate, 0.30, delta=0.001, msg="Fiscal Shock failed")

    def test_crisis_monitor_logging(self):
        """Test that crisis monitor logs data."""
        self.sim.run_tick() # Tick 1
        self.sim.run_tick() # Tick 2

        report_file = f"reports/crisis_monitor_{self.sim.run_id}.csv"
        self.assertTrue(os.path.exists(report_file), "Crisis Monitor report file not created.")

        with open(report_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertGreater(len(rows), 2, "Report should have header and at least 2 ticks of data.")

            last_row = rows[-1]
            print(f"Monitor Log Entry: {last_row}")
            self.assertEqual(int(last_row[4]), 5)

if __name__ == "__main__":
    unittest.main()
