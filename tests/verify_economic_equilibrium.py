
import logging
import sys
import os

# Ensure we can import simulation modules
sys.path.append(os.getcwd())

from simulation.engine import Simulation
from simulation.db.repository import SimulationRepository
from simulation.core_agents import Household
from simulation.firms import Firm
import config
from app import create_simulation, simulation_instance, get_or_create_simulation

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EconomyCheck")

def run_verification():
    print(">>> Initializing Simulation...")
    
    # Use app's creator to ensure consistency
    create_simulation()
    from app import simulation_instance as sim
    
    if not sim:
        print("!! Failed to create simulation.")
        return

    print(f"Start: Households={len(sim.households)}, Firms={len(sim.firms)}")
    
    print("\n>>> Running 5 Ticks (Diagnostic Mode)...")
    print(f"{'Tick':<5} | {'GDP':<10} | {'Deaths':<8} | {'Food Price':<10} | {'H0 Assets':<10} | {'H0 Food':<8} | {'H0 SurvStatus':<12}")
    print("-" * 100)

    for i in range(1, 6):
        sim.run_tick()
        
        # Get Indicators
        indicators = sim.tracker.get_latest_indicators()
        gdp = indicators.get("total_production", 0)
        
        # Count deaths
        dead_h = sum(1 for h in sim.households if not h.is_active)
        
        # Check Food Market
        food_market = sim.markets.get("basic_food")
        last_price = food_market.daily_avg_price.get("basic_food", 0) if food_market else 0
        
        # Check Agent 0
        h0 = sim.agents.get(0) # Household 0
        h0_assets = h0.assets if h0 else -1
        h0_food = h0.inventory.get("basic_food", 0) if h0 else -1
        h0_surv = h0.needs.get("survival", 0) if h0 else -1
        
        print(f"{i:<5} | {gdp:<10.1f} | {dead_h:<8} | {last_price:<10.1f} | {h0_assets:<10.1f} | {h0_food:<8.1f} | {h0_surv:<12.1f}")
        
        # Debug Order Book at Tick 1
        if i == 1:
            print(f"  [Tick 1 Debug] Market 'basic_food':")
            bids = food_market.buy_orders.get("basic_food", [])
            asks = food_market.sell_orders.get("basic_food", [])
            print(f"    Bids ({len(bids)}): {[f'{o.price:.2f} (qty {o.quantity})' for o in bids]}")
            print(f"    Asks ({len(asks)}): {[f'{o.price:.2f} (qty {o.quantity})' for o in asks]}")
            
            # Check if H0 tried to buy
            if h0:
                print(f"    H0 State: Active={h0.is_active}, Decision Engine Recommends: ?")

    print("\n>>> Diagnosis Complete")

if __name__ == "__main__":
    run_verification()
