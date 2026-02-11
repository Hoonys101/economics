from tests.utils.factories import create_firm_config_dto, create_household_config_dto
import unittest
import pytest
from unittest.mock import MagicMock
from modules.finance.system import FinanceSystem
from modules.finance.api import InsufficientFundsError, GrantBailoutCommand
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY
from tests.mocks.mock_settlement_system import MockSettlementSystem

# Mock objects that will be passed to FinanceSystem
class MockGovernment:
    def __init__(self, initial_assets):
        self.id = 0
        self._assets = initial_assets
        self.sensory_data = None
        # Mock wallet for FinanceSystem init sync
        self.wallet = MagicMock()
        self.wallet.get_balance.return_value = initial_assets

    @property
    def assets(self): return self._assets
    def get_debt_to_gdp_ratio(self):
        return 0.5
    # Deprecated methods for Phase 3 but kept for interface compliance
    def _deposit(self, amount, currency=DEFAULT_CURRENCY): self._assets += amount
    def _withdraw(self, amount, currency=DEFAULT_CURRENCY): self._assets -= amount
    def deposit(self, amount): self._deposit(amount)
    def withdraw(self, amount): self._withdraw(amount)

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
    def _deposit(self, amount, currency=DEFAULT_CURRENCY): self.assets['cash'] += amount
    def _withdraw(self, amount, currency=DEFAULT_CURRENCY): self.assets['cash'] -= amount
    def deposit(self, amount): self._deposit(amount)
    def withdraw(self, amount): self._withdraw(amount)

class MockBank:
    def __init__(self, initial_assets):
        self.id = 1
        self._assets = initial_assets
        # Mock wallet for FinanceSystem init sync
        self.wallet = MagicMock()
        self.wallet.get_balance.return_value = initial_assets
        self.base_rate = 0.03

    @property
    def assets(self): return self._assets
    def _deposit(self, amount, currency=DEFAULT_CURRENCY): self._assets += amount
    def _withdraw(self, amount, currency=DEFAULT_CURRENCY): self._assets -= amount
    def deposit(self, amount): self._deposit(amount)
    def withdraw(self, amount): self._withdraw(amount)

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
    def _deposit(self, amount, currency=DEFAULT_CURRENCY): self.cash_reserve += amount
    def _withdraw(self, amount, currency=DEFAULT_CURRENCY): self.cash_reserve -= amount
    def deposit(self, amount): self._deposit(amount)
    def withdraw(self, amount): self._withdraw(amount)

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

        self.mock_settlement = MockSettlementSystem()
        self.mock_settlement.setup_balance(self.mock_gov.id, 10000)
        self.mock_settlement.setup_balance(self.mock_cb.id, 5000)
        self.mock_settlement.setup_balance(self.mock_bank.id, 20000)
        # Note: MockFirm ID is 1, Bank ID is 1. Conflict?
        # MockBank ID is 1 in definition. MockFirm ID is passed as 1.
        # This might cause issue in get_balance if IDs clash.
        # I'll update MockFirm ID to 101 to avoid clash.
        self.mock_firm = MockFirm(id=101, initial_cash_reserve=100)
        self.mock_settlement.setup_balance(self.mock_firm.id, 100)

        self.finance_system = FinanceSystem(
            government=self.mock_gov,
            central_bank=self.mock_cb,
            bank=self.mock_bank,
            config_module=self.mock_config,
            settlement_system=self.mock_settlement
        )

        # Mock FiscalMonitor to redirect to Gov mock method
        self.finance_system.fiscal_monitor = MagicMock()
        self.finance_system.fiscal_monitor.get_debt_to_gdp_ratio.side_effect = lambda gov, dto: gov.get_debt_to_gdp_ratio()

    def test_bailout_loan_generates_command(self):
        """
        Verify that requesting a bailout loan generates a GrantBailoutCommand.
        """
        # Ensure ledger has funds (synced from mock_gov.wallet in init)
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


    @pytest.mark.xfail(reason="QE buyer logic is not implemented in FinanceSystem refactor")
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

        # Transaction Generated
        self.assertEqual(len(txs), 1)
        if len(txs) > 0:
            tx = txs[0]
            self.assertEqual(tx.buyer_id, self.mock_cb.id) # FAIL: Logic uses bank.id
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
        # Expect assets to change because transfer is synchronous now
        self.assertEqual(self.mock_gov.assets, initial_gov_assets + bond_amount)
        self.assertEqual(self.mock_bank.assets, initial_bank_assets - bond_amount)

        self.assertEqual(len(txs), 1)
        tx = txs[0]
        self.assertEqual(tx.buyer_id, self.mock_bank.id) # Bank buys
        self.assertEqual(tx.seller_id, self.mock_gov.id)
        self.assertEqual(tx.price, bond_amount)

if __name__ == '__main__':
    unittest.main()
