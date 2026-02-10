from tests.utils.factories import create_firm_config_dto, create_household_config_dto
import unittest
from unittest.mock import MagicMock
from modules.finance.system import FinanceSystem
from modules.finance.api import InsufficientFundsError, GrantBailoutCommand
from simulation.models import Transaction

# Mock objects that will be passed to FinanceSystem
class MockGovernment:
    def __init__(self, initial_assets):
        self.id = 0
        self._assets = initial_assets
        self.sensory_data = None
    @property
    def assets(self): return self._assets
    def get_debt_to_gdp_ratio(self):
        return 0.5
    # Deprecated methods for Phase 3 but kept for interface compliance
    def deposit(self, amount): self._assets += amount
    def withdraw(self, amount): self._assets -= amount

class MockCentralBank:
    def __init__(self, initial_cash):
        self.id = 999
        self._assets = {"cash": initial_cash, "bonds": []}
    @property
    def assets(self): return self._assets
    def get_base_rate(self):
        return 0.01
    def add_bond_to_portfolio(self, bond):
        self.assets["bonds"].append(bond)
    # Mocking IFinancialEntity behavior loosely
    def deposit(self, amount): self.assets['cash'] += amount
    def withdraw(self, amount): self.assets['cash'] -= amount

class MockBank:
    def __init__(self, initial_assets):
        self.id = 1
        self._assets = initial_assets
    @property
    def assets(self): return self._assets
    def deposit(self, amount): self._assets += amount
    def withdraw(self, amount): self._assets -= amount

class MockFirm:
    def __init__(self, id, initial_cash_reserve):
        self.id = id
        self.cash_reserve = initial_cash_reserve
        # Mock the finance component of the firm
        self.finance = MagicMock()
        self.has_bailout_loan = False
        self.age = 100
    @property
    def assets(self): return self.cash_reserve
    def deposit(self, amount): self.cash_reserve += amount
    def withdraw(self, amount): self.cash_reserve -= amount

class MockConfig:
    QE_INTERVENTION_YIELD_THRESHOLD = 0.05
    DEBT_RISK_PREMIUM_TIERS = {
        1.2: 0.05,
        0.9: 0.02,
        0.6: 0.005,
    }
    BOND_MATURITY_TICKS = 400
    BAILOUT_PENALTY_PREMIUM = 0.05
    BAILOUT_REPAYMENT_RATIO = 0.5

    def get(self, key, default=None):
        if key == "economy_params.BAILOUT_PENALTY_PREMIUM":
            return self.BAILOUT_PENALTY_PREMIUM
        if key == "economy_params.DEBT_RISK_PREMIUM_TIERS":
            return self.DEBT_RISK_PREMIUM_TIERS
        if key == "economy_params.QE_INTERVENTION_YIELD_THRESHOLD":
            return self.QE_INTERVENTION_YIELD_THRESHOLD
        if key == "economy_params.STARTUP_GRACE_PERIOD_TICKS":
            return 24
        if key == "economy_params.ALTMAN_Z_SCORE_THRESHOLD":
            return 1.81
        if key == "economy_params.BOND_MATURITY_TICKS":
            return 400
        return default


class TestDoubleEntry(unittest.TestCase):

    def setUp(self):
        self.mock_config = MockConfig()
        self.mock_gov = MockGovernment(initial_assets=10000)
        self.mock_cb = MockCentralBank(initial_cash=5000)
        self.mock_bank = MockBank(initial_assets=20000)
        self.mock_firm = MockFirm(id=1, initial_cash_reserve=100)

        self.finance_system = FinanceSystem(
            government=self.mock_gov,
            central_bank=self.mock_cb,
            bank=self.mock_bank,
            config_module=self.mock_config
        )

        # Mock FiscalMonitor to redirect to Gov mock method
        self.finance_system.fiscal_monitor = MagicMock()
        self.finance_system.fiscal_monitor.get_debt_to_gdp_ratio.side_effect = lambda gov, dto: gov.get_debt_to_gdp_ratio()

    def test_bailout_loan_generates_command(self):
        """
        Verify that requesting a bailout loan generates a GrantBailoutCommand.
        """
        initial_gov_assets = self.mock_gov.assets
        initial_firm_cash = self.mock_firm.cash_reserve
        bailout_amount = 500

        cmd = self.finance_system.request_bailout_loan(self.mock_firm, bailout_amount)

        # Assertions
        # Assets Unchanged (as command pattern decouples execution)
        self.assertEqual(self.mock_gov.assets, initial_gov_assets)
        self.assertEqual(self.mock_firm.cash_reserve, initial_firm_cash)

        # Command Generated
        self.assertIsNotNone(cmd)
        self.assertIsInstance(cmd, GrantBailoutCommand)
        self.assertEqual(cmd.firm_id, self.mock_firm.id)
        self.assertEqual(cmd.amount, bailout_amount)


    def test_qe_bond_issuance_generates_transaction(self):
        """
        Verify that issuing bonds under QE generates correct transaction.
        """
        # Force high yield to trigger QE
        self.mock_gov.get_debt_to_gdp_ratio = lambda: 1.5

        initial_gov_assets = self.mock_gov.assets
        initial_cb_cash = self.mock_cb.assets['cash']
        bond_amount = 1000

        bonds, txs = self.finance_system.issue_treasury_bonds(bond_amount, current_tick=1)

        # Assertions
        # Assets Unchanged
        self.assertEqual(self.mock_gov.assets, initial_gov_assets)
        self.assertEqual(self.mock_cb.assets['cash'], initial_cb_cash)

        # Transaction Generated (Buyer -> Gov)
        self.assertEqual(len(txs), 1)
        tx = txs[0]
        self.assertEqual(tx.buyer_id, self.mock_cb.id) # Central Bank buys
        self.assertEqual(tx.seller_id, self.mock_gov.id)
        self.assertEqual(tx.price, bond_amount)

    def test_market_bond_issuance_generates_transaction(self):
        """
        Verify that issuing bonds to the market generates correct transaction.
        """
        # Ensure low yield to avoid QE
        self.mock_gov.get_debt_to_gdp_ratio = lambda: 0.5

        initial_gov_assets = self.mock_gov.assets
        initial_bank_assets = self.mock_bank.assets
        bond_amount = 2000

        bonds, txs = self.finance_system.issue_treasury_bonds(bond_amount, current_tick=1)

        # Assertions
        self.assertEqual(self.mock_gov.assets, initial_gov_assets)
        self.assertEqual(self.mock_bank.assets, initial_bank_assets)

        self.assertEqual(len(txs), 1)
        tx = txs[0]
        self.assertEqual(tx.buyer_id, self.mock_bank.id) # Bank buys
        self.assertEqual(tx.seller_id, self.mock_gov.id)
        self.assertEqual(tx.price, bond_amount)

if __name__ == '__main__':
    unittest.main()
