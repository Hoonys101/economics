import sys
import os
import unittest
import logging
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.firms import Firm
from simulation.systems.ma_manager import MAManager
import config as Config

class MockSimulation:
    def __init__(self, firms, households_dict):
        self.firms = firms
        self.households_dict = households_dict
        self.time = 0

class TestPhase9MA(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.ERROR)
        self.config = Config
        # Enable M&A
        self.config.MA_ENABLED = True
        self.config.VALUATION_PER_MULTIPLIER = 10.0
        self.config.MIN_ACQUISITION_CASH_RATIO = 1.0

        # Create Mock Firms
        self.predator = Firm(
            id=1, 
            initial_capital=100000.0, 
            initial_liquidity_need=100.0,
            specialization="widget",
            productivity_factor=1.0,
            decision_engine=MagicMock(),
            value_orientation="PROFIT",
            config_module=self.config, 
            logger=logging.getLogger("Predator")
        )
        self.predator.name = "Predator Corp"
        self.predator.profit_history = [100.0] * 10
        self.predator.current_profit = 100.0 # Set current profit for logic check
        self.predator.capital_stock = 10.0
        self.predator.inventory = {"widget": 0}
        self.predator.employees = []

        self.prey = Firm(
            id=2, 
            initial_capital=1000.0, 
            initial_liquidity_need=100.0,
            specialization="widget",
            productivity_factor=1.0,
            decision_engine=MagicMock(),
            value_orientation="PROFIT",
            config_module=self.config, 
            logger=logging.getLogger("Prey")
        )
        self.prey.name = "Prey Inc"
        self.prey.profit_history = [-10.0] * 10
        self.prey.capital_stock = 5.0
        self.prey.inventory = {"widget": 20}
        self.prey.founder_id = 999
        self.prey.consecutive_loss_ticks = 25 # Trigger potential bankruptcy risk if threshold hit
        
        # Create Dummy Employee
        emp_mock = MagicMock()
        emp_mock.id = 101
        self.prey.employees = [emp_mock]
        self.prey.employee_wages = {101: 50.0}

        # Mock Households Dict for payout
        self.households_dict = {999: MagicMock()}
        self.households_dict[999].assets = 0.0

        self.sim = MockSimulation([self.predator, self.prey], self.households_dict)
        self.ma_manager = MAManager(self.sim, self.config)

    def test_valuation_calculation(self):
        # Prey Valuation
        # Net Assets = 1000 (Cash) + Value(20 widgets) + Value(5 Capital Stock)
        # Assume widget price 0? Firm.get_inventory_value checks last_prices.
        # Let's set last_prices for Prey
        self.prey.last_prices["widget"] = 10.0
        inventory_value = 20 * 10.0 # 200
        # Capital Stock: logic in calculate_valuation uses capital_stock value? 
        # Code: net_assets = self.capital + self.get_inventory_value() + self.capital_stock
        # Note: capital_stock is a float quantity. If it's just added, 5.0 is small. 
        # But let's stick to implementation logic.
        
        net_assets = 1000.0 + 200.0 + 5.0 # 1205.0
        # Profit Premium: Max(0, -10) * 10 = 0
        expected_valuation = 1205.0
        
        self.prey.calculate_valuation()
        self.assertAlmostEqual(self.prey.valuation, expected_valuation, delta=1.0)

    def test_acquisition_execution(self):
        # Setup conditions for acquisition
        # Predator Cash 100k > Prey Valuation (~1.2k) * 1.1
        self.prey.last_prices["widget"] = 10.0
        
        # Run Manager
        self.ma_manager.process_market_exits_and_entries(current_tick=1)
        
        # Assertions
        # 1. Prey should be inactive
        self.assertFalse(self.prey.is_active, "Prey should be inactive (acquired)")
        
        # 2. Predator Capital should decrease
        # Offer ~ 1205 * 1.1 = 1325.5
        self.assertTrue(self.predator.assets < 100000.0, "Predator capital should decrease")
        
        
        # 3. Predator Inventory/Capital Stock increase
        self.assertEqual(self.predator.inventory.get("widget", 0), 20, "Predator should get inventory")
        self.assertEqual(self.predator.capital_stock, 15.0, "Predator should get capital stock (10+5)")
        
        # 4. Founder Payout
        self.assertTrue(self.households_dict[999].assets > 0, "Founder should receive payout")

    def test_bankruptcy_liquidation(self):
        # Make Prey insolvent and poor so it can't be acquired (or just isolate it)
        self.prey.assets = -500.0
        self.prey.last_prices["widget"] = 10.0
        self.sim.firms = [self.prey] # No predator
        
        
        # Run Manager
        self.ma_manager.process_market_exits_and_entries(current_tick=1)
        
        # Assertions
        self.assertFalse(self.prey.is_active, "Prey should be inactive (liquidated)")
        self.assertTrue(self.prey.is_bankrupt, "Prey should be marked bankrupt")
        # Assets should have been liquidated.
        # Inventory 20 * 10 * 0.5 (discount) = 100
        # Capital 5 * 10 * 0.5 = 25
        # Total recovered = 125.
        # Final Capital = -500 + 125 = -375.
        self.assertAlmostEqual(self.prey.assets, -375.0, delta=1.0)

if __name__ == '__main__':
    unittest.main()
