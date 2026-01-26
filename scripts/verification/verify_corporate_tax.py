import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


import unittest
from unittest.mock import MagicMock
import logging
from simulation.firms import Firm
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.decisions.base_decision_engine import BaseDecisionEngine
import config

class TestCorporateTax(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.CORPORATE_TAX_RATE = 0.2
        self.mock_config.FIRM_MAINTENANCE_FEE = 50.0
        self.mock_config.LIQUIDATION_DISCOUNT_RATE = 0.5
        self.mock_config.FIRM_DEFAULT_TOTAL_SHARES = 100.0
        self.mock_config.PROFIT_HISTORY_TICKS = 10
        
        self.mock_logger = logging.getLogger("Test")
        self.mock_decision_engine = MagicMock(spec=BaseDecisionEngine)
        
        # Setup Government
        self.government = Government(
            id=0,
            initial_assets=0.0,
            config_module=self.mock_config
        )
        
        # Setup Firm
        self.firm = Firm(
            id=1,
            initial_capital=1000.0,
            initial_liquidity_need=100.0,
            specialization="test_spec",
            productivity_factor=10.0,
            decision_engine=self.mock_decision_engine,
            value_orientation="neutral",
            config_module=self.mock_config,
            logger=self.mock_logger
        )
        self.firm.employees = [] # Start with no employees

    def test_pay_maintenance(self):
        """Test if maintenance fee is deducted and tax is collected."""
        initial_assets = self.firm.assets
        initial_gov_assets = self.government.assets
        
        # Execute private method via name mangling or just mocking context?
        # Since I added it as _pay_maintenance, I should test it directly or via update_needs
        # Let's test via direct call for unit test
        self.firm._pay_maintenance(self.government, None, current_time=1)
        
        expected_fee = 50.0
        self.assertEqual(self.firm.assets, initial_assets - expected_fee)
        self.assertEqual(self.government.assets, initial_gov_assets + expected_fee)
        self.assertEqual(self.government.tax_revenue["firm_maintenance"], expected_fee)

    def test_pay_corporate_tax(self):
        """Test if corporate tax is paid on profit."""
        self.firm.revenue_this_turn = 1000.0
        self.firm.cost_this_turn = 500.0 # Expenses
        
        # Expected Net Profit = 1000 - 500 = 500
        # Expected Tax = 500 * 0.2 = 100.0
        
        initial_assets = self.firm.assets
        initial_gov_assets = self.government.assets
        
        self.firm._pay_taxes(self.government, current_time=1)
        
        expected_tax = 100.0
        self.assertEqual(self.firm.assets, initial_assets - expected_tax)
        self.assertEqual(self.government.assets, initial_gov_assets + expected_tax)
        self.assertEqual(self.government.tax_revenue["corporate_tax"], expected_tax)

    def test_liquidation_money_conservation(self):
        """Test critical fix: Liquidation should not create money."""
        self.firm.inventory = {"goods": 100.0} # Value shouldn't matter
        self.firm.capital_stock = 50.0 # Value shouldn't matter
        self.firm._assets = 500.0 # Only this should be returned
        
        initial_total_money = self.firm.assets
        
        # Execute liquidation
        recovered_cash = self.firm.liquidate_assets()
        
        # Assertions
        self.assertEqual(recovered_cash, 500.0) # Should be equal to assets
        self.assertEqual(self.firm.assets, 500.0)
        self.assertEqual(len(self.firm.inventory), 0)
        self.assertEqual(self.firm.capital_stock, 0.0)
        self.assertTrue(self.firm.is_bankrupt)
        
        # Conservation Check
        # Money inside Firm should not change (just assets returned)
        # Inventory and Capital disappeared (Real Assets lost), but Money (Financial Asset) conserved.
        self.assertEqual(self.firm.assets, initial_total_money)

if __name__ == '__main__':
    unittest.main()
