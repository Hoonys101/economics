
import sys
import os
import unittest
from unittest.mock import MagicMock, ANY

# Adjust path to allow imports
sys.path.append(os.getcwd())

from simulation.systems.inheritance_manager import InheritanceManager
from simulation.models import Transaction
from simulation.systems.api import TransactionContext
from modules.system.api import DEFAULT_CURRENCY

class TestInheritanceLeaks(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.INHERITANCE_DEDUCTION = 0.0
        self.config.INHERITANCE_TAX_RATE = 0.4

        self.manager = InheritanceManager(config_module=self.config)
        self.government = MagicMock()
        self.government.id = 1

        self.deceased = MagicMock()
        self.deceased.id = 99
        self.deceased._econ_state = MagicMock()
        self.deceased._econ_state.assets = 100.0
        self.deceased._econ_state.portfolio = MagicMock()
        self.deceased._econ_state.portfolio.holdings = {}
        self.deceased._bio_state = MagicMock()
        self.deceased._bio_state.children_ids = [101] # 1 Heir

        # Ensure wallet returns float
        self.deceased.wallet = MagicMock()
        self.deceased.wallet.get_balance.return_value = 0.0

        self.simulation = MagicMock()
        self.simulation.time = 0
        self.simulation.stock_market = None
        self.simulation.real_estate_units = []
        self.simulation.agents = {101: MagicMock()}

        # TransactionProcessor mock
        self.simulation.transaction_processor = MagicMock()
        self.simulation.transaction_processor.execute.return_value = [MagicMock(success=True)]

    def test_inheritance_tax_failure_leak(self):
        """
        Scenario: Agent dies with assets. Tax payment fails.
        """
        def mock_execute(state, txs):
            tx = txs[0]
            if tx.transaction_type == "tax":
                return [MagicMock(success=False)] # FAIL TAX
            return [MagicMock(success=True)] # Pass others

        self.simulation.transaction_processor.execute.side_effect = mock_execute

        # Execute
        txs = self.manager.process_death(self.deceased, self.government, self.simulation)

        # Check transactions
        tax_tx = next((tx for tx in txs if tx.transaction_type == "tax"), None)
        dist_tx = next((tx for tx in txs if tx.transaction_type == "inheritance_distribution"), None)

        self.assertIsNone(tax_tx, "Failed tax transaction should not be reported as executed")

        if dist_tx:
            self.assertEqual(dist_tx.price, 100.0)
            print("OBSERVATION: If tax fails, full amount is distributed. No asset leak.")

    def test_liquidation_leak_fix(self):
        """
        Scenario: Agent has illiquid assets. Liquidation succeeds, but subsequent steps fail.
        Expected: Fallback escheatment should be attempted.
        """
        self.deceased._econ_state.assets = 0.0 # No cash
        self.deceased.wallet.get_balance.return_value = 0.0

        share = MagicMock()
        share.quantity = 10
        share.acquisition_price = 10.0
        self.deceased._econ_state.portfolio.holdings = {
            'firm_1': share
        }

        self.simulation.stock_market = MagicMock()
        self.simulation.stock_market.get_daily_avg_price.return_value = 10.0

        # Simulate: Liquidation Succeeds -> Tax Fails -> Distribution Fails
        def mock_execute(state, txs):
            tx = txs[0]
            if tx.transaction_type == "asset_liquidation":
                return [MagicMock(success=True)]
            if tx.transaction_type == "tax":
                return [MagicMock(success=False)]
            if tx.transaction_type == "inheritance_distribution":
                 return [MagicMock(success=False)] # Distribution FAIL
            if tx.transaction_type == "escheatment":
                 return [MagicMock(success=True)] # Fallback Success!
            return [MagicMock(success=True)]

        self.simulation.transaction_processor.execute.side_effect = mock_execute

        # Execute
        txs = self.manager.process_death(self.deceased, self.government, self.simulation)

        escheat_tx = next((tx for tx in txs if tx.transaction_type == "escheatment"), None)
        self.assertIsNotNone(escheat_tx, "Fallback Escheatment should be reported")

        if escheat_tx:
            # Should sweep the cash (100.0 from liquidation)
            # 10 shares * 10.0 price = 100.0 proceeds
            self.assertEqual(escheat_tx.price, 100.0)
            print("\nAUDIT PASS: Leak plugged! Fallback escheatment successfully captured stranded assets.")

    def test_final_sweep_leak_check(self):
        """
        Scenario: After all processing, agent still has funds (simulating drift).
        Expected: Final sweep escheatment.
        """
        self.deceased._econ_state.assets = 0.0

        # Simulate: Everything seems fine, BUT wallet reports money at the end
        self.deceased.wallet.get_balance.return_value = 5.55 # LEFTOVER

        self.simulation.transaction_processor.execute.return_value = [MagicMock(success=True)]
        self.simulation.transaction_processor.execute.side_effect = None # Reset side effect

        # Execute
        txs = self.manager.process_death(self.deceased, self.government, self.simulation)

        # Should find a final_sweep transaction
        sweep_tx = next((tx for tx in txs if tx.item_id == "final_sweep"), None)
        self.assertIsNotNone(sweep_tx)
        self.assertEqual(sweep_tx.price, 5.55)
        print("AUDIT PASS: Final sweep captured leftover wallet balance.")

if __name__ == '__main__':
    unittest.main()
