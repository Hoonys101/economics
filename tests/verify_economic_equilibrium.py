
import logging
import sys
import os
import unittest

# Ensure we can import simulation modules
sys.path.append(os.getcwd())

from simulation.engine import Simulation
from simulation.db.repository import SimulationRepository
from simulation.core_agents import Household
from simulation.firms import Firm
import config
from dashboard.app import create_simulation, simulation_instance, get_or_create_simulation

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EconomyCheck")

class TestEconomicConservation(unittest.TestCase):
    def setUp(self):
        self.original_config = {}
        
    def test_conservation_of_money(self):
        print("\n>>> Initializing Simulation for Conservation Check...")
        
        create_simulation()
        from dashboard.app import simulation_instance as sim
        
        if not sim:
            self.fail("Failed to create simulation.")

        def calculate_total_money(simulation):
            h_assets = sum(h.assets for h in simulation.households)
            f_assets = sum(f.assets for f in simulation.firms)
            b_assets = simulation.bank.assets
            g_assets = simulation.government.assets
            r_bal = simulation.reflux_system.balance
            return h_assets + f_assets + b_assets + g_assets + r_bal

        initial_money = calculate_total_money(sim)
        print(f"Initial Money Supply: {initial_money:,.2f}")
        
        ticks_to_run = 100
        prev_money = initial_money
        
        print(f"{'Tick':<5} | {'Total Money':<15} | {'Diff':<10}")
        print("-" * 35)

        for i in range(1, ticks_to_run + 1):
            sim.run_tick()

            current_money = calculate_total_money(sim)
            diff = current_money - prev_money
            
            # Print periodically or on error
            if i % 10 == 0 or diff < -0.01:
                print(f"{i:<5} | {current_money:<15,.2f} | {diff:<10.4f}")

            # Allow for floating point errors (epsilon)
            # Fail only if money decreases significantly (Leak)
            # Increases are allowed (Central Bank injection, Deficit Spending)
            if diff < -1.0:
                 self.fail(f"Money Leakage Detected at Tick {i}. Diff: {diff}")

            prev_money = current_money

        print("\n>>> Conservation Test Passed.")
        print(f"Final Money: {prev_money:,.2f}")
        print(f"Net Change: {prev_money - initial_money:,.2f}")

if __name__ == "__main__":
    unittest.main()
