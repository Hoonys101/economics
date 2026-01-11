
import pytest
from unittest.mock import MagicMock, Mock, patch
from collections import deque
import logging

from simulation.ai.household_system2 import HouseholdSystem2Planner, MarketTrend
from simulation.core_agents import Household
from simulation.engine import Simulation
from simulation.models import Order, RealEstateUnit

# Configure logging to capture output
logging.basicConfig(level=logging.DEBUG)

# Concrete Test Class inheriting from Household
# This bypasses __init__ complexity but satisfies isinstance(h, Household)
class TestHousehold(Household):
    def __init__(self, id, assets=0.0):
        self.id = id
        self.assets = assets
        self.owned_properties = []
        self.property_purchase_prices = {}
        self.housing_price_history = deque()
        self.current_wage = 50.0
        self.is_employed = True
        self.expected_wage = 50.0
        self.needs = {"survival": 0.0}
        self.temporary_housing_expiry_tick = 0
        self.residing_property_id = None
        self.is_homeless = False
        self.is_active = True
        self.inventory = {}
        # Mock Decision Engine parts if accessed
        self.decision_engine = MagicMock()

@pytest.fixture
def mock_config():
    """Provides a mock configuration module."""
    config = MagicMock()
    config.REAL_ESTATE_PROFIT_TARGET = 0.2
    config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    config.HOUSING_EXPECTATION_CAP = 0.05
    config.TICKS_PER_YEAR = 100
    config.MORTGAGE_LTV_RATIO = 0.8
    config.MORTGAGE_TERM_TICKS = 300
    config.MORTGAGE_INTEREST_RATE = 0.05
    config.MAINTENANCE_RATE_PER_TICK = 0.001
    config.HOMELESS_PENALTY_PER_TICK = 5.0
    return config

@pytest.fixture
def mock_agent(mock_config):
    """Provides a TestHousehold agent."""
    agent = TestHousehold(id=1, assets=5000.0)
    agent.owned_properties = [101]
    agent.property_purchase_prices = {101: 10000.0}
    agent.housing_price_history = deque([10000.0, 10200.0, 10400.0])
    agent.residing_property_id = 101
    return agent

@pytest.fixture
def planner(mock_agent, mock_config):
    """Provides the System 2 Planner instance."""
    return HouseholdSystem2Planner(mock_agent, mock_config)

class TestRealEstateLiquidity:

    def test_market_trend_detection(self, planner):
        """Test the _detect_market_trend logic."""
        history = deque([100, 110, 120])
        assert planner._detect_market_trend(history) == MarketTrend.RISING

        history = deque([120, 110, 100])
        assert planner._detect_market_trend(history) == MarketTrend.FALLING

        history = deque([100, 120, 110])
        assert planner._detect_market_trend(history) == MarketTrend.FALLING

        history = deque([100, 100, 100])
        assert planner._detect_market_trend(history) == MarketTrend.FLAT

    def test_distress_sale_trigger(self, planner, mock_agent):
        """Test distress sale trigger."""
        market_data = {
            "goods_market": {"basic_food_current_sell_price": 5.0},
            "housing_market": {"avg_sale_price": 20000.0}
        }

        mock_agent.assets = 5000.0
        decision = planner.decide_selling(mock_agent, market_data, current_tick=10)
        assert decision is None

        mock_agent.assets = 100.0
        decision = planner.decide_selling(mock_agent, market_data, current_tick=10)

        assert decision is not None
        action, unit_id, price = decision
        assert action == "SELL"
        assert unit_id == 101
        assert price == 20000.0 * 0.95

    def test_profit_taking_trigger(self, planner, mock_agent):
        """Test profit taking trigger."""
        market_data = {
            "goods_market": {"basic_food_current_sell_price": 5.0},
            "housing_market": {"avg_sale_price": 15000.0, "avg_rent_price": 100.0},
            "loan_market": {"interest_rate": 0.05}
        }

        mock_agent.housing_price_history = deque([13000.0, 14000.0, 15000.0]) # RISING
        decision = planner.decide_selling(mock_agent, market_data, current_tick=10)
        assert decision is None

        mock_agent.housing_price_history = deque([14000.0, 15000.0, 14500.0]) # FALLING

        with patch.object(planner, 'calculate_housing_npv', return_value={'npv_rent': 20000, 'npv_buy': 10000}) as mock_npv:
            decision = planner.decide_selling(mock_agent, market_data, current_tick=10)
            assert decision is not None
            action, unit_id, price = decision
            assert action == "SELL"
            assert price == 15000.0

    def test_transaction_updates(self, mock_config):
        """Test Simulation._process_housing_transaction updates logic using TestHousehold."""
        sim = MagicMock(spec=Simulation)
        sim.config_module = mock_config
        sim.logger = logging.getLogger("test")
        sim.time = 100
        sim.bank = MagicMock()
        sim.bank.grant_loan.return_value = 999

        seller = TestHousehold(id=1)
        seller.owned_properties = [50]
        seller.property_purchase_prices = {50: 5000.0}
        seller.residing_property_id = 50
        seller.is_homeless = False

        buyer = TestHousehold(id=2, assets=10000.0)

        unit = RealEstateUnit(id=50, owner_id=1, occupant_id=1, estimated_value=8000.0)
        sim.real_estate_units = [unit]
        # Important: agents dict must return these instances
        sim.agents = {1: seller, 2: buyer}

        transaction_price = 8000.0

        # Execute (use bound method trick)
        Simulation._process_housing_transaction(sim, MagicMock(item_id="unit_50"), buyer, seller, transaction_price)

        # Verify Seller Updates
        assert 50 not in seller.owned_properties
        assert 50 not in seller.property_purchase_prices
        assert seller.residing_property_id is None
        assert seller.is_homeless is True
        assert seller.temporary_housing_expiry_tick == 102

        # Verify Buyer Updates
        assert 50 in buyer.owned_properties
        assert buyer.property_purchase_prices[50] == transaction_price
        assert buyer.residing_property_id == 50
        assert buyer.is_homeless is False

    def test_grace_period_logic(self, mock_config):
        """Test Simulation._process_housing grace period check using TestHousehold."""
        sim = MagicMock(spec=Simulation)
        sim.config_module = mock_config
        sim.logger = logging.getLogger("test")
        sim.time = 100
        sim.real_estate_units = []

        # Agent in Grace Period
        safe_agent = TestHousehold(id=1)
        safe_agent.residing_property_id = None # Homeless
        safe_agent.is_homeless = True
        safe_agent.temporary_housing_expiry_tick = 101 # Expires next tick

        # Agent Expired
        expired_agent = TestHousehold(id=2)
        expired_agent.residing_property_id = None
        expired_agent.is_homeless = True
        expired_agent.temporary_housing_expiry_tick = 99 # Expired

        sim.households = [safe_agent, expired_agent]
        sim.agents = {1: safe_agent, 2: expired_agent}

        # Run logic
        Simulation._process_housing(sim)

        # Verify Safe Agent (No Penalty)
        assert safe_agent.needs["survival"] == 0.0

        # Verify Expired Agent (Penalty Applied)
        assert expired_agent.needs["survival"] == 5.0
