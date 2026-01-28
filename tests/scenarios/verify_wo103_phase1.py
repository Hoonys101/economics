import sys
import unittest
from unittest.mock import MagicMock
import logging

# Configure logging to swallow output during tests
logging.basicConfig(level=logging.CRITICAL)

from simulation.firms import Firm
from simulation.components.finance_department import FinanceDepartment
from simulation.components.hr_department import HRDepartment

class TestWO103Phase1(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        # Ensure float values for config to prevent MagicMock propagation into math
        self.mock_config.INITIAL_FIRM_LIQUIDITY_NEED = 50.0
        self.mock_config.FIRM_MIN_PRODUCTION_TARGET = 10.0
        self.mock_config.IPO_INITIAL_SHARES = 1000.0
        self.mock_config.BANKRUPTCY_CONSECUTIVE_LOSS_THRESHOLD = 5
        self.mock_config.INVENTORY_HOLDING_COST_RATE = 0.1
        self.mock_config.LIQUIDITY_NEED_INCREASE_RATE = 1.0
        self.mock_config.ASSETS_CLOSURE_THRESHOLD = -100.0
        self.mock_config.FIRM_CLOSURE_TURNS_THRESHOLD = 10
        self.mock_config.PROFIT_HISTORY_TICKS = 10
        self.mock_config.GOODS = {"food": {"initial_price": 10.0}}
        self.mock_config.FIRM_MAINTENANCE_FEE = 0.0 # Simplify
        self.mock_config.CORPORATE_TAX_RATE = 0.0 # Simplify
        self.mock_config.RAW_MATERIAL_SECTORS = []
        # Add BrandManager specific configs just in case, though we mock it
        self.mock_config.BRAND_DECAY = 0.95
        self.mock_config.BRAND_SENSITIVITY = 0.1

        self.mock_decision_engine = MagicMock()
        self.mock_decision_engine.loan_market = None

        self.firm = Firm(
            id=1,
            initial_capital=1000.0,
            initial_liquidity_need=50.0,
            specialization="food",
            productivity_factor=1.0,
            decision_engine=self.mock_decision_engine,
            value_orientation="PROFIT",
            config_module=self.mock_config
        )

        # Mock HR process_payroll returns 0.0
        self.firm.hr.process_payroll = MagicMock(return_value=0.0)

        # Mock BrandManager to prevent formatting errors and internal logic
        self.firm.brand_manager = MagicMock()
        self.firm.brand_manager.brand_awareness = 0.5
        self.firm.brand_manager.perceived_quality = 1.0

    def test_initialization(self):
        print("\nTest Initialization...")
        self.assertEqual(self.firm.assets, 1000.0)
        self.assertEqual(self.firm.finance.balance, 1000.0)
        print("Initialization Passed.")

    def test_assets_property_setter(self):
        print("\nTest Assets Property Setter (External Update)...")
        # Emulate TransactionProcessor adding money
        self.firm._assets += 500.0
        self.assertEqual(self.firm.assets, 1500.0)
        self.assertEqual(self.firm.finance.balance, 1500.0)

        # Emulate TransactionProcessor removing money
        self.firm._assets -= 200.0
        self.assertEqual(self.firm.assets, 1300.0)
        self.assertEqual(self.firm.finance.balance, 1300.0)
        print("Property Setter Passed.")

    def test_transactional_methods(self):
        print("\nTest Transactional Methods (Deposit/Withdraw)...")
        self.firm.deposit(100.0)
        self.assertEqual(self.firm.assets, 1100.0)

        self.firm.withdraw(100.0)
        self.assertEqual(self.firm.assets, 1000.0)
        print("Transactional Methods Passed.")

    def test_holding_costs(self):
        print("\nTest Holding Costs...")
        # Reset assets to 1000
        self.firm._assets = 1000.0

        # Setup inventory
        self.firm.inventory = {"food": 10.0}
        self.firm.last_prices = {"food": 10.0} # Value = 100.0
        # Cost rate 0.1 -> Cost = 10.0

        # Marketing Logic:
        # Assets 1000 > 100
        # Revenue 0.
        # Marketing = max(10.0, 0 * 0.05) = 10.0.

        initial_assets = self.firm.assets

        self.firm.update_needs(current_time=1)

        expected_deduction = 10.0 + 10.0 # Holding + Marketing
        self.assertAlmostEqual(self.firm.assets, initial_assets - expected_deduction, delta=0.1)

        # Verify finance recorded expenses
        self.assertGreater(self.firm.finance.expenses_this_tick, 0)
        print("Holding Costs Passed.")

if __name__ == '__main__':
    unittest.main()
