
import pytest
from unittest.mock import Mock, MagicMock
from simulation.engine import Simulation
from simulation.core_agents import Household
from simulation.systems.immigration_manager import ImmigrationManager
from simulation.ai.system2_planner import System2Planner
import config

class TestPhase20Integration:

    @pytest.fixture
    def mock_config(self):
        conf = MagicMock()
        # Copy relevant config
        conf.POPULATION_IMMIGRATION_THRESHOLD = 80
        conf.IMMIGRATION_BATCH_SIZE = 5
        conf.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 2.0
        conf.SYSTEM2_HORIZON = 100
        conf.SYSTEM2_DISCOUNT_RATE = 0.98
        conf.SYSTEM2_TICKS_PER_CALC = 1
        conf.FORMULA_TECH_LEVEL = 0.0
        # Need to provide real values for choices/weights
        conf.EDUCATION_LEVEL_DISTRIBUTION = [0.4, 0.3, 0.15, 0.1, 0.04, 0.01]

        # Phase 17-4: Vanity - Conformity (Biased Randomization)
        # CONFORMITY_RANGES needs to be mocked
        conf.CONFORMITY_RANGES = {
            "STATUS_SEEKER": (0.7, 0.95),
            "CONSERVATIVE": (0.5, 0.7),
            "MISER": (0.1, 0.3),
            "IMPULSIVE": (0.4, 0.6),
            None: (0.3, 0.7)
        }

        # Add INITIAL_HOUSEHOLD_ASSETS_MEAN as float, not mock
        conf.INITIAL_HOUSEHOLD_ASSETS_MEAN = 5000.0
        return conf

    def test_immigration_trigger(self, mock_config):
        """Test if immigration is triggered under correct conditions."""

        # Setup ImmigrationManager
        manager = ImmigrationManager(mock_config)

        # Mock Engine
        engine = MagicMock()
        engine.time = 100
        engine.next_agent_id = 100
        # Mock households list with MagicMock objects, but ensure is_active is boolean
        engine.households = []
        for i in range(50):
            h = MagicMock()
            h.is_active = True # Boolean, not Mock
            engine.households.append(h)
        engine.goods_data = []
        engine.ai_trainer = MagicMock()

        # Mock Tracker Indicators
        engine.tracker.get_latest_indicators.return_value = {
            "unemployment_rate": 0.01 # < 0.05 (Labor Shortage)
        }

        # Mock Market Data (Vacancies)
        engine._prepare_market_data.return_value = {
            "job_vacancies": 10 # > 0
        }

        # Execute
        new_immigrants = manager.process_immigration(engine)

        # Assert
        assert len(new_immigrants) == 5
        assert engine.next_agent_id == 105

    def test_immigration_conditions_not_met(self, mock_config):
        manager = ImmigrationManager(mock_config)
        engine = MagicMock()
        engine.households = [MagicMock() for _ in range(50)]
        for h in engine.households: h.is_active = True

        # Case 1: High Unemployment
        engine.tracker.get_latest_indicators.return_value = {"unemployment_rate": 0.10}
        engine._prepare_market_data.return_value = {"job_vacancies": 10}
        assert len(manager.process_immigration(engine)) == 0

        # Case 2: No Vacancies
        engine.tracker.get_latest_indicators.return_value = {"unemployment_rate": 0.01}
        engine._prepare_market_data.return_value = {"job_vacancies": 0}
        assert len(manager.process_immigration(engine)) == 0

        # Case 3: Overpopulation
        mock_config.POPULATION_IMMIGRATION_THRESHOLD = 40
        assert len(manager.process_immigration(engine)) == 0

    def test_system2_housing_cost_renter(self, mock_config):
        """Test System2Planner deducting rent for non-owners."""
        agent = MagicMock()
        agent.assets = 1000.0
        agent.expected_wage = 10.0 # Make sure this is float
        agent.residing_property_id = None # Homeless/Renter
        agent.owned_properties = []
        agent.spouse_id = None
        agent.children_ids = []

        planner = System2Planner(agent, mock_config)

        market_data = {
            "goods_market": {"basic_food_current_sell_price": 5.0},
            "housing_market": {"avg_rent_price": 50.0},
            "debt_data": {}
        }

        # Mock time allocation
        agent.decision_engine.ai_engine.decide_time_allocation.return_value = {"total_obligated": 0.0}

        result = planner.project_future(1, market_data)

        # Net Flow = Wage*Hours - Food - Rent
        # Wage=10 (default), Hours=8, Food=5*2=10, Rent=50
        # Flow = 80 - 10 - 50 = 20
        # NPV should be positive but reduced by rent

        # Let's verify by manually calculating
        # Discounted sum of 20 for 100 ticks
        assert result["npv_wealth"] > 1000.0

        # Compare with High Rent
        market_data_high = market_data.copy()
        market_data_high["housing_market"] = {"avg_rent_price": 200.0}
        planner.cached_projection = {} # Clear cache

        result_high = planner.project_future(2, market_data_high)
        # Flow = 80 - 10 - 200 = -130
        # Should go bankrupt
        assert result_high["bankruptcy_tick"] is not None

    def test_system2_housing_cost_owner(self, mock_config):
        """Test System2Planner deducting mortgage interest for owners."""
        agent = MagicMock()
        agent.assets = 1000.0
        agent.expected_wage = 10.0 # Make sure this is float
        agent.residing_property_id = 1
        agent.owned_properties = [1]
        agent.id = 1
        agent.spouse_id = None
        agent.children_ids = []

        planner = System2Planner(agent, mock_config)

        market_data = {
            "goods_market": {"basic_food_current_sell_price": 5.0},
            "housing_market": {"avg_rent_price": 50.0},
            "debt_data": {
                1: {"daily_interest_burden": 30.0}
            }
        }

        agent.decision_engine.ai_engine.decide_time_allocation.return_value = {"total_obligated": 0.0}

        result = planner.project_future(1, market_data)

        # Flow = 80 (Income) - 10 (Food) - 30 (Interest) = 40
        # Should be better than renting at 50

        # Verify calculation indirectly or by mocking project logic specifics if needed
        # Here just ensuring it runs without error and returns reasonable NPV
        assert result["npv_wealth"] > 1000.0
