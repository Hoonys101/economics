
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
from modules.system.api import IConfigurationRegistry, IAgentRegistry
from tests.utils.factories import create_household_config_dto, create_firm_config_dto, create_household, create_firm

# Disable logging for cleaner test output
logging.getLogger().setLevel(logging.CRITICAL)

@pytest.fixture(autouse=True)
def clean_room_teardown():
    yield
    # Safely clear any global states or caches if necessary.

@pytest.fixture
def mock_config_registry():
    mock_registry = MagicMock(spec=IConfigurationRegistry)
    # Define minimal safe defaults required for diagnosis scenarios
    mock_registry.get.return_value = None
    return mock_registry

@pytest.fixture
def mock_agent_registry():
    return MagicMock(spec=IAgentRegistry)

@pytest.fixture
def simple_household(mock_config_registry, mock_agent_registry):
    mock_engine = MagicMock(spec=BaseDecisionEngine)
    household = create_household(
        config_dto=create_household_config_dto(),
        id=1,
        engine=mock_engine,
        assets=10000, # 100.00 pennies
        initial_needs={"survival": 50.0},
        goods_data=[],
        personality=Personality.MISER,
        value_orientation="wealth_and_needs",
        registry=mock_agent_registry,
        config_registry=mock_config_registry
    )
    return household

@pytest.fixture
def simple_firm(mock_config_registry, mock_agent_registry):
    mock_engine = MagicMock(spec=BaseDecisionEngine)
    firm = create_firm(
        config_dto=create_firm_config_dto(),
        id=101,
        engine=mock_engine,
        assets=100000, # 1000.00 pennies
        specialization="basic_food",
        productivity_factor=1.0,
        value_orientation="wealth_and_needs",
        initial_inventory={},
        registry=mock_agent_registry,
        config_registry=mock_config_registry
    )
    return firm

@pytest.fixture
def simple_market():
    mock_breaker = MagicMock(spec=IIndexCircuitBreaker)
    mock_breaker.check_market_health.return_value = True
    mock_breaker.is_active.return_value = False
    return OrderBookMarket(market_id="basic_food", circuit_breaker=mock_breaker)
