
import unittest
from unittest.mock import MagicMock
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY

class TestInheritancePrecision(unittest.TestCase):
    def test_inheritance_float_leak_prevention(self):
        # Setup
        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.4
        config.INHERITANCE_DEDUCTION = 0.0

        manager = InheritanceManager(config)

        simulation = MagicMock()
        simulation.time = 100

        # Mock Deceased Agent with fractional assets
        deceased = MagicMock()
        deceased.id = 666
        # Simulate wallet balance
        deceased.wallet = MagicMock()
        # 100.005 dollars -> 10000.5 pennies -> 10000 pennies (int truncation) if we were converting from float
        # BUT wallet returns int pennies directly.
        # So let's say wallet has 10000 pennies.
        deceased.wallet.get_balance.return_value = 10000

        # Also setup assets dict fallback for robustness check (though wallet takes precedence)
        deceased.assets = {DEFAULT_CURRENCY: 10000}

        deceased._econ_state.portfolio.holdings = {}
        deceased._bio_state.children_ids = []

        # Government
        government = MagicMock()
        government.id = 1

        simulation.real_estate_units = []
        simulation.stock_market = None
        simulation.bank = None

        # Mock TransactionProcessor
        simulation.transaction_processor = MagicMock()
        simulation.transaction_processor.execute.return_value = [MagicMock(success=True)]

        # Execute
        transactions = manager.process_death(deceased, government, simulation)

        # Verify Tax Transaction
        # Assets: 10000 pennies.
        # Tax Rate: 0.4
        # Tax: 10000 * 0.4 = 4000 pennies.

        tax_tx = None
        for tx in transactions:
            if tx.transaction_type == "tax":
                tax_tx = tx
                break

        self.assertIsNotNone(tax_tx, "Tax transaction should exist")
        self.assertEqual(tax_tx.total_pennies, 4000, f"Expected 4000 pennies tax, got {tax_tx.total_pennies}")

        # Verify Escheatment (Remaining)
        # 10000 - 4000 = 6000 pennies.
        escheat_tx = None
        for tx in transactions:
            if tx.transaction_type == "escheatment":
                escheat_tx = tx
                break

        self.assertIsNotNone(escheat_tx, "Escheatment transaction should exist")
        self.assertEqual(escheat_tx.total_pennies, 6000, f"Expected 6000 pennies escheatment, got {escheat_tx.total_pennies}")

    def test_inheritance_rounding_robustness(self):
        # Setup similar to above but with fractional math potential
        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.3333333333 # 1/3
        config.INHERITANCE_DEDUCTION = 0.0

        manager = InheritanceManager(config)
        simulation = MagicMock()
        simulation.time = 100

        deceased = MagicMock()
        deceased.id = 777
        # 100 pennies
        deceased.wallet.get_balance.return_value = 100
        deceased._econ_state.portfolio.holdings = {}
        deceased._bio_state.children_ids = []

        government = MagicMock()
        government.id = 1

        simulation.real_estate_units = []
        simulation.stock_market = None
        simulation.bank = None
        simulation.transaction_processor.execute.return_value = [MagicMock(success=True)]

        transactions = manager.process_death(deceased, government, simulation)

        # Tax: 100 * 0.3333333333 = 33.3333 -> 33 pennies (int)
        tax_tx = next((tx for tx in transactions if tx.transaction_type == "tax"), None)
        self.assertIsNotNone(tax_tx)
        self.assertEqual(tax_tx.total_pennies, 33)

        # Remaining: 100 - 33 = 67 pennies
        escheat_tx = next((tx for tx in transactions if tx.transaction_type == "escheatment"), None)
        self.assertIsNotNone(escheat_tx)
        self.assertEqual(escheat_tx.total_pennies, 67)

        # Verification: 33 + 67 = 100. Zero Sum preserved.

if __name__ == '__main__':
    unittest.main()
