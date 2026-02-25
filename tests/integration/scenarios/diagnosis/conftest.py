
import pytest
from unittest.mock import MagicMock
import logging
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.core_markets import Market
from modules.market.api import IIndexCircuitBreaker
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.ai.api import Personality # Import Personality enum
import config
from tests.utils.factories import create_household_config_dto, create_firm_config_dto, create_household, create_firm

# Disable logging for cleaner test output
logging.getLogger().setLevel(logging.CRITICAL)

@pytest.fixture
def mock_config_module():
    mock_config = MagicMock()
    # Copy essential values from actual config to avoid breaking things
    for key in dir(config):
        if not key.startswith("__"):
            setattr(mock_config, key, getattr(config, key))
    return mock_config

@pytest.fixture
def simple_household(mock_config_module):
    mock_engine = MagicMock(spec=BaseDecisionEngine)
    household = create_household(
        config_dto=create_household_config_dto(),
        id=1,
        engine=mock_engine,
        assets=10000, # 100.00 pennies
        initial_needs={"survival": 50.0},
        goods_data=[],
        personality=Personality.MISER,
        value_orientation="wealth_and_needs"
    )
    return household

@pytest.fixture
def simple_firm(mock_config_module):
    mock_engine = MagicMock(spec=BaseDecisionEngine)
    firm = create_firm(
        config_dto=create_firm_config_dto(),
        id=101,
        engine=mock_engine,
        assets=100000, # 1000.00 pennies
        specialization="basic_food",
        productivity_factor=1.0,
        value_orientation="wealth_and_needs",
        initial_inventory={}
    )
    return firm

@pytest.fixture
def simple_market():
    mock_breaker = MagicMock(spec=IIndexCircuitBreaker)
    mock_breaker.check_market_health.return_value = True
    mock_breaker.is_active.return_value = False
    return OrderBookMarket(market_id="basic_food", circuit_breaker=mock_breaker)
