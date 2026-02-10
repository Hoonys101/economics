
import unittest
import os
import shutil
import csv
from unittest.mock import MagicMock, Mock
from simulation.initialization.initializer import SimulationInitializer
from modules.common.config_manager.api import ConfigManager
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.db.repository import SimulationRepository
from simulation.ai_model import AIEngineRegistry
import logging

class TestPhase29DepressionRepro(unittest.TestCase):
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
            GOODS={"food": {"initial_price": 10}, "electronics": {"initial_price": 50}},
            INITIAL_BANK_ASSETS=1000000,
            INITIAL_MONEY_SUPPLY=1000000,
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
            FIRM_CLOSURE_TURNS_THRESHOLD=5
        )

        # Create dummy agents
        self.households = [MagicMock(spec=Household) for _ in range(5)]
        for i, h in enumerate(self.households):
            h.id = i
            h._bio_state = MagicMock()
            h._econ_state = MagicMock()
            h._social_state = MagicMock()
            h._bio_state.is_active = True
            # h.get_assets_by_currency.return_value = {"USD": 1000.0} # Explicit mock

        self.firms = [MagicMock(spec=Firm) for _ in range(5)]
        for i, f in enumerate(self.firms):
            f.id = 100 + i
            # f.get_assets_by_currency.return_value = {"USD": 5000.0} # Explicit mock

        self.repository = MagicMock(spec=SimulationRepository)
        self.repository.runs = MagicMock()
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
        print("Building simulation...")
        print(f"DEBUG: h._econ_state.assets type: {type(self.households[0]._econ_state.assets)}")
        try:
             print(f"DEBUG: h._econ_state.assets value: {self.households[0]._econ_state.assets}")
             print(f"DEBUG: h._econ_state.assets.get: {getattr(self.households[0]._econ_state.assets, 'get', 'MISSING')}")
        except Exception as e:
             print(f"DEBUG: Error accessing assets: {e}")
        self.sim = self.initializer.build_simulation()
        print("Simulation built.")

    def test_repro(self):
        pass

if __name__ == "__main__":
    unittest.main()
