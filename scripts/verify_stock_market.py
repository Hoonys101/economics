
import sys
from pathlib import Path
import os
import logging
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config as global_config # Root config module

from simulation.engine import Simulation
from simulation.models import Order
from simulation.firms import Firm
from simulation.core_agents import Household
from simulation.markets.stock_market import StockMarket
from simulation.decisions.corporate_manager import CorporateManager

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("VERIFY_STOCK")

class MockConfig:
    # Mimic config module structure
    NUM_HOUSEHOLDS = 20
    NUM_FIRMS = 2
    STOCK_BOOK_VALUE_MULTIPLIER = 1.0
    STOCK_PRICE_LIMIT_RATE = 0.30
    DIVIDEND_RATE_MIN = 0.0
    DIVIDEND_RATE_MAX = 0.5
    
    # Copy essential dicts
    GOODS = getattr(global_config, 'GOODS', {})
    LABOR_MARKET_MIN_WAGE = getattr(global_config, 'LABOR_MARKET_MIN_WAGE', 10.0)
    # Add other needed configs
    FIRM_DEFAULT_TOTAL_SHARES = getattr(global_config, 'FIRM_DEFAULT_TOTAL_SHARES', 1000.0)
    FIRM_MIN_PRODUCTION_TARGET = getattr(global_config, 'FIRM_MIN_PRODUCTION_TARGET', 10.0)
    INITIAL_FIRM_LIQUIDITY_NEED = getattr(global_config, 'INITIAL_FIRM_LIQUIDITY_NEED', 500.0)
    INVENTORY_HOLDING_COST_RATE = getattr(global_config, 'INVENTORY_HOLDING_COST_RATE', 0.01)
    
    # Add R&D productivity multiplier if needed
    RND_PRODUCTIVITY_MULTIPLIER = getattr(global_config, 'RND_PRODUCTIVITY_MULTIPLIER', 0.1)
    MAX_SELL_QUANTITY = getattr(global_config, 'MAX_SELL_QUANTITY', 100.0)

def run_verification():
    print(">>> STARTING STOCK MARKET VERIFICATION <<<")
    
    # 1. Init Simulation
    config = MockConfig()
    sim = Simulation(
        households=[], firms=[], ai_trainer=None, repository=None, config_module=config, goods_data=[]
    )
    # Manually populate for control
    sim.households = [Household(i, 1000.0, [], 'BALANCED', config) for i in range(config.NUM_HOUSEHOLDS)]
    sim.firms = [Firm(1, 10000.0, 500.0, "food", 1.0, None, 'BALANCED', config)]
    
    # Give some shares to households
    firm = sim.firms[0]
    total_shares_start = firm.total_shares
    shares_per_hh = total_shares_start / config.NUM_HOUSEHOLDS
    
    for h in sim.households:
        h.shares_owned[firm.id] = shares_per_hh
        # Set risk aversion: 10 Value Investors, 10 Momentum Traders
        if h.id < 10:
            h.risk_aversion = 2.0 # Value (High Aversion)
        else:
            h.risk_aversion = 0.5 # Momentum (Low Aversion)

    # Init Stock Market
    sim.stock_market = StockMarket(config, logger)
    sim.markets["stock_market"] = sim.stock_market
    
    # Correctly register firm in market if needed (mitosis registry?)
    # StockMarket usually auto-registers or uses get_daily_avg_price(firm.id) which handles missing.
    
    # 2. Market Run Scenarios
    
    # Scene 1: Bubble Formation (Ticks 1-5)
    print("\n[Phase 1] Bubble Formation (High Dividends)")
    firm.current_profit = 5000.0 
    firm.dividend_rate = 0.5
    
    # Pre-seed price
    sim.stock_market.daily_prices[firm.id] = 10.0
    
    for t in range(5):
        # Force dividend distribution manually to trigger signals
        sim.time = t
        firm.distribute_dividends(sim.households, sim.government, t)
        
        # Prepare Market Data
        market_data = {
            "stock_market": {
                f"stock_{firm.id}": {
                    "avg_price": sim.stock_market.get_daily_avg_price(firm.id) or 10.0, 
                    "dividend_yield": 0.05
                }
            }
        }
        
        # Agents generate orders
        for h in sim.households:
            # Inject cash to fuel bubble
            h.assets += 100.0 
            # Portfolio Manager call
            orders = h.portfolio_manager.generate_stock_orders(
                h.id, h.shares_owned, h.assets * 0.5, h.assets, market_data, h.risk_aversion, 0.02
            )
            for o in orders:
                sim.stock_market.place_order(o, t)
                
        sim.stock_market.match_orders(t)
        price = sim.stock_market.get_daily_avg_price(firm.id)
        print(f"Tick {t}: Price = {price:.2f}")

    peak_price = sim.stock_market.get_daily_avg_price(firm.id)
    
    # Scene 2: Crash (Ticks 6-10)
    print("\n[Phase 2] Crash (Earnings Shock)")
    firm.current_profit = 0.0
    firm.dividend_rate = 0.0
    
    for t in range(6, 11):
        sim.time = t
        market_data = {
            "stock_market": {
                f"stock_{firm.id}": {
                    "avg_price": sim.stock_market.get_daily_avg_price(firm.id), 
                    "dividend_yield": 0.0
                }
            }
        }
        
        for h in sim.households:
            orders = h.portfolio_manager.generate_stock_orders(
                h.id, h.shares_owned, h.assets * 0.5, h.assets, market_data, h.risk_aversion, 0.02
            )
            for o in orders:
                sim.stock_market.place_order(o, t)
        
        sim.stock_market.match_orders(t)
        price = sim.stock_market.get_daily_avg_price(firm.id)
        print(f"Tick {t}: Price = {price:.2f}")
        
    crash_price = sim.stock_market.get_daily_avg_price(firm.id)
    
    # Scene 3: Buyback (Tick 15)
    print("\n[Phase 3] Treasury Buyback")
    firm.assets = 100000.0 # Massive cash injection for buyback
    firm.needs["liquidity_need"] = 100.0 # Low need
    
    initial_shares = firm.total_shares
    print(f"Shares Before Buyback: {initial_shares}")
    
    # Instantiate CorporateManager
    cm = CorporateManager(config, logger)
    
    # Updated Market Data with Low Price (Crash Price)
    market_data = {"stock_market": {f"stock_{firm.id}": {"avg_price": crash_price}}}
    
    # 1. Generate Buyback Orders
    buyback_orders = cm._manage_buybacks(firm, market_data, 15)
    print(f"Buyback Orders Generated: {len(buyback_orders)}")
    
    if buyback_orders:
        buy_order = buyback_orders[0]
        print(f"Buy Order: {buy_order.quantity:.1f} shares @ {buy_order.price:.2f}")
        
        # Place Buy Order
        sim.stock_market.place_order(buy_order, 15)
        
        # Place Matches Sell Order (from Households)
        # Force a household to sell at a lower price to ensure match
        sell_qty = buy_order.quantity
        sim.stock_market.place_order(
            Order(agent_id=sim.households[0].id, side="SELL", item_id=f"stock_{firm.id}", quantity=sell_qty, price_limit=buy_order.price * 0.9, market_id="stock"),
            15
        )
        
        # Match Orders
        txs = sim.stock_market.match_orders(15)
        print(f"Matched {len(txs)} transactions.")
        
        # 2. Process Transactions (Logic Verification)
        # We need to manually invoke logic because we aren't running full sim step loop
        # But we can verify if engine's process_transactions works by mocking it or calling it?
        # Sim object has _process_transactions method.
        sim._process_transactions(txs)
        
    final_shares = firm.total_shares
    print(f"Shares After Buyback: {final_shares}")
    
    burnt_amount = initial_shares - final_shares
    if burnt_amount > 0:
        print(f">>> SUCCESS: {burnt_amount:.1f} Shares Retired (Buyback & Burn Verified)")
    else:
        print(">>> FAILURE: Shares NOT Reduced")

    if peak_price > 10.0 and crash_price < peak_price:
        print(">>> SUCCESS: Bubble & Crash Verified")
    else:
        print(f">>> FAILURE: Price Dynamics ambiguous (Start:10, Peak:{peak_price:.2f}, Crash:{crash_price:.2f})")

if __name__ == "__main__":
    run_verification()
