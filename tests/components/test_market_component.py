import pytest
from unittest.mock import MagicMock
from simulation.components.market_component import MarketComponent
from simulation.systems.api import MarketInteractionContext


@pytest.fixture
def market_component():
    owner = MagicMock()
    # Default preferences
    owner.brand_loyalty = {}
    owner.quality_preference = 0.5

    config = MagicMock()
    config.BRAND_SENSITIVITY_BETA = 0.5
    return MarketComponent(owner, config)


def test_choose_best_seller_utility(market_component):
    # Setup
    # Seller 1: Price 10, Quality 1.0, Awareness 0.0
    # Seller 2: Price 12, Quality 1.5, Awareness 0.0

    ask1 = MagicMock()
    ask1.price = 10.0
    ask1.agent_id = 1
    ask1.brand_info = {"perceived_quality": 1.0, "brand_awareness": 0.0}

    ask2 = MagicMock()
    ask2.price = 12.0
    ask2.agent_id = 2
    ask2.brand_info = {"perceived_quality": 1.5, "brand_awareness": 0.0}

    market = MagicMock()
    market.get_all_asks.return_value = [ask1, ask2]

    context: MarketInteractionContext = {"markets": {"good_x": market}}

    # Execute
    best_seller, best_price = market_component.choose_best_seller("good_x", context)

    # Calc Utility
    # U1 = (1.0^0.5 * 1.0^0.5 * 1.0) / 10 = 0.1
    # U2 = (1.5^0.5 * 1.0^0.5 * 1.0) / 12 = 1.22 / 12 = 0.102

    # U2 > U1
    assert best_seller == 2
    assert best_price == 12.0


def test_choose_best_seller_no_market(market_component):
    context = {"markets": {}}
    best_seller, _ = market_component.choose_best_seller("missing_good", context)
    assert best_seller is None
