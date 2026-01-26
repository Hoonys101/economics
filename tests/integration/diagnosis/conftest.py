
import pytest
from unittest.mock import MagicMock
import logging
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.core_markets import Market
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.ai.api import Personality # Import Personality enum
import config

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
    household = Household(
        id=1,
        talent=Talent(1.0, {}),
        goods_data=[], # Simplification
        initial_assets=100.0,
        initial_needs={"survival": 50.0},
        decision_engine=mock_engine,
        value_orientation="wealth_and_needs", # Default
        personality=Personality.MISER, # Default
        config_module=mock_config_module
    )
    return household

@pytest.fixture
def simple_firm(mock_config_module):
    mock_engine = MagicMock(spec=BaseDecisionEngine)
    firm = Firm(
        id=101,
        initial_capital=1000.0,
        initial_liquidity_need=0.0,
        specialization="basic_food",
        productivity_factor=1.0,
        decision_engine=mock_engine,
        value_orientation="wealth_and_needs", # Default
        config_module=mock_config_module
    )
    return firm

@pytest.fixture
def simple_market():
    return OrderBookMarket(market_id="basic_food")
