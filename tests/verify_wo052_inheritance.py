
import unittest
from unittest.mock import MagicMock
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.core_agents import Household
from simulation.agents.government import Government

class TestInheritanceNoHeir(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.INHERITANCE_TAX_RATE = 0.4
        self.config.INHERITANCE_DEDUCTION = 100000.0  # High deduction to avoid tax/liquidation logic
        
        self.manager = InheritanceManager(self.config)
        self.simulation = MagicMock()
        self.simulation.time = 1
        
        # Setup Agents
        self.deceased = MagicMock()
        self.deceased.id = 1
        self.deceased.assets = 1000.0
        self.deceased.children_ids = [] # No Heirs
        self.deceased.portfolio = MagicMock()
        self.deceased.portfolio.holdings = {
            101: MagicMock(quantity=10, acquisition_price=10.0)
        }
        self.deceased.shares_owned = {101: 10}
        self.deceased.owned_properties = [500]
        
        self.government = MagicMock()
        self.government.id = 999
        self.government.assets = 100000.0  # Start with enough to buy assets
        
        def collect_tax_side_effect(amount, tax_type, agent_id, time):
            self.government.assets += amount
            
        self.government.collect_tax.side_effect = collect_tax_side_effect
        self.simulation.government = self.government
        
        # Setup Markets
        self.simulation.stock_market = MagicMock()
        self.simulation.stock_market.get_daily_avg_price.return_value = 20.0
        
        # Setup Real Estate
        self.unit = MagicMock()
        self.unit.id = 500
        self.unit.estimated_value = 5000.0
        self.unit.owner_id = 1
        self.simulation.real_estate_units = [self.unit]
        
        self.simulation.agents = {
            999: self.government
        }
        
    def test_no_heir_confiscation(self):
        # Run process_death
        self.manager.process_death(self.deceased, self.government, self.simulation)
        
        print(f"DEBUG | Deceased Assets: {self.deceased.assets}")
        print(f"DEBUG | Government Assets: {self.government.assets}")
        
        # Verification 1: Cash Confiscation
        self.assertEqual(self.deceased.assets, 0.0, "Deceased cash should be 0")
        self.assertGreater(self.government.assets, 0.0, "Government should receive cash")
        
        # Verification 2: Stock Confiscation
        # Should call update_shareholder for Government with qty 10
        self.simulation.stock_market.update_shareholder.assert_any_call(999, 101, 10)
        self.simulation.stock_market.update_shareholder.assert_any_call(1, 101, 0)

        # Portfolio cleared?
        self.assertEqual(len(self.deceased.portfolio.holdings), 0, "Portfolio holdings should be empty")
        self.assertEqual(len(self.deceased.shares_owned), 0, "Shares owned should be empty")
        
        # Verification 3: Real Estate Confiscation
        self.assertEqual(self.unit.owner_id, 999, "Property owner should be Government")
        self.assertEqual(len(self.deceased.owned_properties), 0, "Owned properties list should be empty")

if __name__ == '__main__':
    unittest.main()
