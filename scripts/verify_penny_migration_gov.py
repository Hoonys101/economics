import unittest
from unittest.mock import MagicMock, Mock
from modules.government.tax.service import TaxService
from modules.government.taxation.system import TaxationSystem
from modules.government.welfare.manager import WelfareManager
from modules.government.components.fiscal_policy_manager import FiscalPolicyManager
from modules.government.dtos import FiscalPolicyDTO, TaxBracketDTO
from modules.government.taxation.system import TaxIntent
from simulation.dtos.api import MarketSnapshotDTO
from modules.system.api import DEFAULT_CURRENCY
from modules.government.constants import DEFAULT_WEALTH_TAX_THRESHOLD, DEFAULT_BASIC_FOOD_PRICE

class TestPennyMigrationGov(unittest.TestCase):

    def setUp(self):
        self.config = MagicMock()
        # Mock Config Constants
        self.config.ANNUAL_WEALTH_TAX_RATE = 0.02
        self.config.TICKS_PER_YEAR = 100
        # DEFAULT_WEALTH_TAX_THRESHOLD should be 5000000 (pennies)
        self.config.WEALTH_TAX_THRESHOLD = 5000000
        self.config.SALES_TAX_RATE = 0.05
        self.config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        # DEFAULT_BASIC_FOOD_PRICE should be 500 (pennies)
        self.config.GOODS_INITIAL_PRICE = {"basic_food": 500}
        self.config.TAX_BRACKETS = [(1.0, 0.0), (3.0, 0.10), (float('inf'), 0.20)]
        self.config.TAX_MODE = "PROGRESSIVE"
        self.config.TAX_RATE_BASE = 0.1
        self.config.INCOME_TAX_PAYER = "HOUSEHOLD"
        self.config.UNEMPLOYMENT_BENEFIT_RATIO = 0.8
        self.config.STIMULUS_TRIGGER_GDP_DROP = -0.05

    def test_tax_service_wealth_tax(self):
        """Verify wealth tax uses int thresholds and returns int."""
        service = TaxService(self.config)

        # Threshold: 5,000,000 pennies
        # Net Worth: 6,000,000 pennies
        # Taxable: 1,000,000 pennies
        # Rate per tick: 0.02 / 100 = 0.0002
        # Tax: 1,000,000 * 0.0002 = 200 pennies

        tax = service.calculate_wealth_tax(6000000)
        self.assertIsInstance(tax, int)
        self.assertEqual(tax, 200)

        # Below threshold
        tax = service.calculate_wealth_tax(4000000)
        self.assertEqual(tax, 0)

    def test_fiscal_policy_manager_survival_cost(self):
        """Verify survival cost calculation handles float/int inputs correctly."""
        fpm = FiscalPolicyManager(self.config)

        # Case 1: Market data gives float dollars (e.g. 5.0)
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        # Mocking generic dict access for market_data
        # We need to mimic the structure accessed by FPM
        snapshot.market_signals = {}
        snapshot.market_data = {
            "goods_market": {"basic_food_current_sell_price": 5.0}
        }

        # determine_fiscal_stance calls internal logic to calc survival cost
        # 5.0 dollars -> 500 pennies
        policy = fpm.determine_fiscal_stance(snapshot)

        # Check brackets. Survival cost should be 500 (5.0 * 100 * 1.0)
        # Bracket 1: 1.0 * 500 = 500 ceiling
        bracket0 = policy.progressive_tax_brackets[0]
        self.assertEqual(bracket0.ceiling, 500)
        self.assertIsInstance(bracket0.ceiling, int)
        self.assertIsInstance(bracket0.floor, int)

    def test_taxation_system_calculate_income_tax(self):
        """Verify income tax calculation uses ints."""
        ts = TaxationSystem(self.config)

        # Income: 2000 pennies
        # Survival Cost: 500 pennies
        # Brackets: 0-500 (0%), 500-1500 (10%), 1500+ (20%)

        # Taxable chunks:
        # 0-500: 500 * 0.0 = 0
        # 500-1500: 1000 * 0.1 = 100
        # 1500-2000: 500 * 0.2 = 100
        # Total: 200 pennies

        # Need to set current_income_tax_rate = 0.1 (same as base to avoid adjustment)
        tax = ts.calculate_income_tax(2000, 500, 0.1, "PROGRESSIVE")
        self.assertIsInstance(tax, int)
        self.assertEqual(tax, 200)

    def test_taxation_system_calculate_tax_intents_food_price(self):
        """Verify calculate_tax_intents handles food price correctly."""
        ts = TaxationSystem(self.config)
        gov = MagicMock()
        gov.id = 1
        gov.income_tax_rate = 0.1

        tx = MagicMock()
        tx.transaction_type = "labor"
        tx.quantity = 1.0
        tx.price = 2000 # 2000 pennies wage

        buyer = MagicMock()
        buyer.id = 2
        seller = MagicMock()
        seller.id = 3

        # Market data with float dollars
        # Use 12.0 ($12) -> 1200 pennies to exceed the 1000 floor
        market_data = {
            "goods_market": {"basic_food_current_sell_price": 12.0}
        }

        # Survival cost = 1200 * 1.0 = 1200
        # Income 2000
        # Brackets (based on config):
        # 0-1200 (1x): 0%
        # 1200-3600 (3x): 10%
        # Income 2000 falls into 2nd bracket.
        # Taxable: 2000 - 1200 = 800
        # Tax: 800 * 0.1 = 80

        intents = ts.calculate_tax_intents(tx, buyer, seller, gov, market_data)

        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].amount, 80)
        self.assertIsInstance(intents[0].amount, int)

    def test_welfare_manager_survival_cost(self):
        """Verify welfare manager gets correct survival cost in pennies."""
        wm = WelfareManager(self.config)

        # Market data with float dollars
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        snapshot.market_data = {
            "goods_market": {"basic_food_current_sell_price": 5.0}
        }

        # 5.0 dollars -> 500 pennies
        # WelfareManager enforces max(..., 1000)
        # So expect 1000
        cost = wm.get_survival_cost(snapshot)
        self.assertIsInstance(cost, int)
        self.assertEqual(cost, 1000)

if __name__ == '__main__':
    unittest.main()
