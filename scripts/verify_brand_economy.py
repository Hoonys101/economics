
import logging
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.markets.order_book_market import OrderBookMarket
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.models import Order
from simulation.ai.api import Personality
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai.household_ai import HouseholdAI
from simulation.ai_model import AIDecisionEngine
import config

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY_BRAND")

def verify_brand_economy():
    logger.info("=== START: Brand Economy Verification ===")
    
    # 1. Setup Market
    market = OrderBookMarket("goods_market", logger)
    
    # 2. Setup Config Mock
    class MockConfig:
        MARKETING_DECAY_RATE = 0.8
        MARKETING_EFFICIENCY = 0.05
        PERCEIVED_QUALITY_ALPHA = 0.2
        QUALITY_SENSITIVITY_MEAN = 0.5
        BRAND_LOYALTY_DECAY = 0.95
        NETWORK_EFFECT_WEIGHT = 0.5
        AI_VALUATION_MULTIPLIER = 1000.0
        
        # Base Agent Configs
        INITIAL_FIRM_LIQUIDITY_NEED = 50.0
        FIRM_MIN_PRODUCTION_TARGET = 10.0
        FIRM_DEFAULT_TOTAL_SHARES = 1000.0
        PROFIT_HISTORY_TICKS = 10
        DIVIDEND_RATE = 0.1
        CAPITAL_DEPRECIATION_RATE = 0.0
        LABOR_ALPHA = 0.7
        INVENTORY_HOLDING_COST_RATE = 0.0
        LABOR_MARKET_MIN_WAGE = 10.0
        LIQUIDITY_NEED_INCREASE_RATE = 0
        ASSETS_CLOSURE_THRESHOLD = -1000
        FIRM_CLOSURE_TURNS_THRESHOLD = 999
        
    mock_config = MockConfig()
    
    # --- Mock AI Dependencies ---
    class MockActionProposalEngine:
        def get_all_actions(self): return []
    
    class MockStateBuilder:
        def build_state(self, *args): return {}

    mock_action_engine = MockActionProposalEngine()
    mock_state_builder = MockStateBuilder()

    # 3. Setup Firms (Brand vs Generic)
    # Firm A: Premium Brand
    firm_a_ai = AIDecisionEngine("firm_a", mock_action_engine, mock_state_builder) 
    firm_a = Firm(1, 1000.0, 50.0, "widget", 20.0, firm_a_ai, "profit", mock_config, loan_market=None, logger=logger)
    
    # Firm B: Generic
    firm_b_ai = AIDecisionEngine("firm_b", mock_action_engine, mock_state_builder) 
    firm_b = Firm(2, 1000.0, 50.0, "widget", 10.0, firm_b_ai, "profit", mock_config, loan_market=None, logger=logger)
    
    # --- Step A: Brand Building ---
    logger.info("--- Step A: Building Brand for Firm A ---")
    # Force Firm A to spend on marketing (High Awareness, Same Quality)
    # Direct injection into Brand Manager
    firm_a.brand_manager.update(100.0, 2.0) # Spend 100, Quality 2.0 -> Perceived Quality ~0.4
    firm_b.brand_manager.update(0.0, 2.0)   # Spend 0, Quality 2.0 (SAME QUALITY) -> Perceived ~0.4
                                            # Awareness = 0 for B
    
    logger.info(f"Firm A Awareness: {firm_a.brand_manager.brand_awareness:.4f}, Perceived Quality: {firm_a.brand_manager.perceived_quality:.4f}")
    logger.info(f"Firm B Awareness: {firm_b.brand_manager.brand_awareness:.4f}, Perceived Quality: {firm_b.brand_manager.perceived_quality:.4f}")
    
    assert firm_a.brand_manager.brand_awareness > firm_b.brand_manager.brand_awareness, "Firm A should have higher awareness"
    
    # --- Step B: Market Offering ---
    logger.info("--- Step B: Firms Place Sell Orders ---")
    # Firm A sells at Premium (Price 15) with Brand Metadata
    # Firm B sells at Discount (Price 10) with Generic Metadata
    brand_info_a = {
        "brand_awareness": firm_a.brand_manager.brand_awareness,
        "perceived_quality": firm_a.brand_manager.perceived_quality
    }
    brand_info_b = {
        "brand_awareness": firm_b.brand_manager.brand_awareness,
        "perceived_quality": firm_b.brand_manager.perceived_quality
    }
    order_a = Order(1, "SELL", "widget", 10.0, 15.0, "goods_market", brand_info=brand_info_a)
    order_b = Order(2, "SELL", "widget", 10.0, 10.0, "goods_market", brand_info=brand_info_b)
    
    market.place_order(order_a, 1)
    market.place_order(order_b, 1)
    
    # --- Step C: Household Choice ---
    logger.info("--- Step C: Household Selection ---")
    
    # Household 1: Quality Seeker (Snob)
    hh_ai = AIDecisionEngine("hh", mock_action_engine, mock_state_builder) # Dummy
    # Need proper init
    talent = Talent(1.0, {})
    hh_snob = Household(101, talent, [], 100.0, {}, hh_ai, "status", Personality.STATUS_SEEKER, mock_config, logger=logger)
    hh_snob.quality_preference = 1.0 # Max quality pref
    
    # Household 2: Miser
    hh_miser = Household(102, talent, [], 100.0, {}, hh_ai, "needs", Personality.MISER, mock_config, logger=logger)
    hh_miser.quality_preference = 0.0 # Price only
    
    # Check Choice
    # Use choose_best_seller directly
    target_snob, price_snob = hh_snob.choose_best_seller({"goods_market": market}, "widget")
    target_miser, price_miser = hh_miser.choose_best_seller({"goods_market": market}, "widget")
    
    logger.info(f"Snob chose Firm {target_snob} at {price_snob}")
    logger.info(f"Miser chose Firm {target_miser} at {price_miser}")
    
    # Verify: Snob should choose Firm A (High Quality/Brand) even if price is 15 vs 10
    # U_A = (2.0 * (1 + 0.63*1) * 1) / 15 = (2 * 1.63) / 15 = 3.26 / 15 = 0.217
    # U_B = (1.0 * (1 + 0) * 1) / 10 = 0.1
    # 0.217 > 0.1 -> Choose A.
    
    if target_snob == 1:
        logger.info("PASS: Snob chose Premium Brand (Firm A).")
    else:
        logger.error(f"FAIL: Snob chose Firm {target_snob}. Expected Firm 1.")
        
    if target_miser == 2:
        logger.info("PASS: Miser chose Cheapest (Firm B).")
    else:
        logger.error(f"FAIL: Miser chose Firm {target_miser}. Expected Firm 2.")
        
    # --- Step D: Execution ---
    logger.info("--- Step D: Execution (Targeted Orders) ---")
    
    # Place targeted buy orders
    buy_snob = Order(101, "BUY", "widget", 1.0, 20.0, "goods_market", target_agent_id=target_snob)
    buy_miser = Order(102, "BUY", "widget", 1.0, 20.0, "goods_market", target_agent_id=target_miser)
    
    market.place_order(buy_snob, 1)
    market.place_order(buy_miser, 1)
    
    txs = market.match_orders(1)
    
    assert len(txs) == 2, f"Expected 2 transactions, got {len(txs)}"
    
    for tx in txs:
        logger.info(f"Transaction: Buyer {tx.buyer_id} -> Seller {tx.seller_id} @ {tx.price}")
        if tx.buyer_id == 101:
            assert tx.seller_id == 1, "Snob matched wrong seller"
            assert tx.price == 15.0, "Snob paid wrong price (should be Seller Ask)"
        if tx.buyer_id == 102:
            assert tx.seller_id == 2, "Miser matched wrong seller"
            assert tx.price == 10.0, "Miser paid wrong price"
            
    logger.info("=== VERIFICATION SUCCESS ===")

if __name__ == "__main__":
    verify_brand_economy()
