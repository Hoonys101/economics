import sys
import os
import random
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.core_agents import Household, Talent
from simulation.ai.api import Personality
from simulation.models import Order
from simulation.core_markets import Market
from simulation.dtos import DecisionContext

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockConfig:
    # Brand Economy Constants
    BRAND_SENSITIVITY_BETA = 0.5
    QUALITY_PREF_SNOB_MIN = 0.7
    QUALITY_PREF_SNOB_MAX = 1.0
    QUALITY_PREF_MISER_MIN = 0.0
    QUALITY_PREF_MISER_MAX = 0.3
    QUALITY_PREF_AVG_MIN = 0.3
    QUALITY_PREF_AVG_MAX = 0.7
    
    # Needs
    INITIAL_HOUSEHOLD_ASSETS_MEAN = 1000.0
    BASE_DESIRE_GROWTH = 1.0
    MAX_DESIRE_VALUE = 100.0
    SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 50.0
    NEED_MEDIUM_THRESHOLD = 50.0
    ASSETS_DEATH_THRESHOLD = 0.0
    HOUSEHOLD_DEATH_TURNS_THRESHOLD = 10
    SURVIVAL_NEED_DEATH_THRESHOLD = 100.0
    LEISURE_COEFFS = {}
    SOCIAL_STATUS_ASSET_WEIGHT = 0.5
    SOCIAL_STATUS_LUXURY_WEIGHT = 0.5

def create_mock_market_with_orders(item_id="phone"):
    market = MagicMock()
    market.get_all_asks = MagicMock(return_value=[])
    return market

def test_brand_economy_scenarios():
    """
    Scenario A (Snob): High Pref Household buys from High Brand Firm (Price 15, Awareness 0.9, Quality 1.0)
    Scenario B (Miser): Low Pref Household buys from Low Brand Firm (Price 10, Awareness 0.1, Quality 0.5)
    """
    config = MockConfig()
    
    # 1. Setup Firms (Asks)
    # Firm A: "Apple" (High Price, High Brand)
    ask_a = Order(agent_id=1, order_type="SELL", item_id="phone", quantity=10, price=15.0, market_id="goods_market")
    ask_a.brand_info = {"perceived_quality": 1.0, "brand_awareness": 0.9}
    
    # Firm B: "Daiso" (Low Price, Low Brand)
    ask_b = Order(agent_id=2, order_type="SELL", item_id="phone", quantity=10, price=10.0, market_id="goods_market")
    ask_b.brand_info = {"perceived_quality": 0.5, "brand_awareness": 0.1}
    
    # Market setup
    market = MagicMock()
    # Return list of Asks
    market.get_all_asks.return_value = [ask_a, ask_b]
    
    markets = {"goods_market": market}
    
    # 2. Setup Households
    # Snob: Status Seeker, High Preference
    talent = Talent(0.1, {})
    snob = Household(
        id=101,
        talent=talent,
        goods_data=[],
        initial_assets=5000.0,
        initial_needs={},
        decision_engine=MagicMock(),
        value_orientation="status",
        personality=Personality.STATUS_SEEKER,
        config_module=config
    )
    # Force preference to 0.9 for deterministic test
    snob.quality_preference = 0.9
    
    # Miser: Frugal, Low Preference
    miser = Household(
        id=102,
        talent=talent,
        goods_data=[],
        initial_assets=100.0,
        initial_needs={},
        decision_engine=MagicMock(),
        value_orientation="survival",
        personality=Personality.MISER,
        config_module=config
    )
    # Force preference to 0.1 for deterministic test
    miser.quality_preference = 0.1

    # 3. Execute Selection Logic
    
    # Snob Check
    logger.info("--- Testing Snob (Pref=0.9) ---")
    best_seller_snob, price_snob = snob.choose_best_seller(markets, "phone")
    logger.info(f"Snob selected Agent {best_seller_snob} at Price {price_snob}")
    
    # Calculate Utility manually for verification
    # U = Q^alpha * (1+A)^0.5 / P
    # Firm A: 1.0^0.9 * (1.9)^0.5 / 15 = 1 * 1.378 / 15 = 0.0918
    # Firm B: 0.5^0.9 * (1.1)^0.5 / 10 = 0.535 * 1.048 / 10 = 0.0561
    # Expectation: Firm A (Agent 1)
    
    # Miser Check
    logger.info("--- Testing Miser (Pref=0.1) ---")
    best_seller_miser, price_miser = miser.choose_best_seller(markets, "phone")
    logger.info(f"Miser selected Agent {best_seller_miser} at Price {price_miser}")
    
    # Calculate Utility manually for verification
    # Firm A: 1.0^0.1 * (1.9)^0.5 / 15 = 1 * 1.378 / 15 = 0.0918 (Same numerator part for Q=1)
    # Firm B: 0.5^0.1 * (1.1)^0.5 / 10 = 0.933 * 1.048 / 10 = 0.0977
    # Expectation: Firm B (Agent 2) is HIGHER utility (0.0977 > 0.0918)
    
    # Assertions
    if best_seller_snob == 1:
        logger.info("PASS: Snob selected Firm A (Apple)")
    else:
        logger.error(f"FAIL: Snob selected Firm {best_seller_snob}, expected 1")
        
    if best_seller_miser == 2:
        logger.info("PASS: Miser selected Firm B (Daiso)")
    else:
        logger.error(f"FAIL: Miser selected Firm {best_seller_miser}, expected 2")
        
    assert best_seller_snob == 1, "Snob should prefer Quality/Brand"
    assert best_seller_miser == 2, "Miser should prefer Low Price"

if __name__ == "__main__":
    test_brand_economy_scenarios()
