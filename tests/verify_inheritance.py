
import unittest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.models import RealEstateUnit
from simulation.portfolio import Portfolio

class TestInheritance(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.INHERITANCE_TAX_RATE = 0.4
        self.config.INHERITANCE_DEDUCTION = 10000

        self.manager = InheritanceManager(self.config)
        self.simulation = MagicMock()
        self.government = MagicMock()
        self.government.assets = 0.0
        self.simulation.government = self.government

        # Deceased
        self.deceased = MagicMock(spec=Household)
        self.deceased.id = 1
        self.deceased.assets = 50000.0
        self.deceased.portfolio = Portfolio(1)
        self.deceased.shares_owned = {}
        self.deceased.owned_properties = []
        self.deceased.children_ids = [2]

        # Heir
        self.heir = MagicMock(spec=Household)
        self.heir.id = 2
        self.heir.assets = 0.0
        self.heir.portfolio = Portfolio(2)
        self.heir.shares_owned = {}
        self.heir.is_active = True
        self.heir.owned_properties = []

        self.simulation.agents = {2: self.heir}
        self.simulation.stock_market = MagicMock()
        self.simulation.stock_market.get_daily_avg_price.return_value = 100.0
        self.simulation.real_estate_units = []

    def test_standard_inheritance(self):
        """Rich parent dies, tax paid, heir gets remaining."""
        self.manager.process_death(self.deceased, self.government, self.simulation)

        # Wealth: 50k
        # Taxable: 50k - 10k = 40k
        # Tax: 40k * 0.4 = 16k
        # Net: 50k - 16k = 34k

        self.government.collect_tax.assert_called()
        # Check heir assets ~ 34k
        self.assertAlmostEqual(self.heir.assets, 34000.0)

    def test_liquidation_stocks(self):
        """Cash poor, Stock rich. Stocks sold to pay tax."""
        self.deceased.assets = 1000.0 # Low cash
        self.deceased.portfolio.add(99, 100, 100.0) # 100 shares of Firm 99 @ 100.0
        # Value = 10000.0
        # Total Wealth = 11000.0
        # Taxable = 11000 - 10000 = 1000
        # Tax = 1000 * 0.4 = 400

        # Current Cash 1000 > Tax 400. No liquidation needed.
        # Let's increase Tax.
        self.config.INHERITANCE_DEDUCTION = 0
        # Total Wealth = 11000
        # Tax = 11000 * 0.4 = 4400
        # Cash 1000 < 4400. Shortfall 3400.

        self.manager.process_death(self.deceased, self.government, self.simulation)

        # Should have sold stocks.
        # Logic: Sells ALL stocks if cash < tax?
        # My implementation: "if deceased.assets < tax_amount and stock_value > 0: ... Sell all"
        # So stocks sold -> 10000 proceeds. Cash = 11000.
        # Paid 4400.
        # Remaining 6600.

        self.assertAlmostEqual(self.heir.assets, 6600.0)
        self.assertEqual(len(self.heir.portfolio.holdings), 0) # No stocks inherited (Sold)

    def test_portfolio_merge(self):
        """Heir inherits stocks with Cost Basis calculation."""
        self.config.INHERITANCE_TAX_RATE = 0.0 # No tax for simplicity

        # Deceased: 100 shares @ 100.0
        self.deceased.portfolio.add(99, 100, 100.0)
        self.deceased.shares_owned[99] = 100

        # Heir: 100 shares @ 50.0 (Already owns)
        self.heir.portfolio.add(99, 100, 50.0)
        self.heir.shares_owned[99] = 100

        self.manager.process_death(self.deceased, self.government, self.simulation)

        # Merged: 200 shares.
        # Cost: (100*100 + 100*50) / 200 = 15000 / 200 = 75.0

        share = self.heir.portfolio.holdings[99]
        self.assertEqual(share.quantity, 200)
        self.assertEqual(share.acquisition_price, 75.0)

        # Check Legacy Sync
        self.assertEqual(self.heir.shares_owned[99], 200)

if __name__ == '__main__':
    unittest.main()
