import unittest
from unittest.mock import MagicMock

# Mock necessary modules and classes that FinanceSystem depends on
from modules.finance.system import FinanceSystem

# Mock objects that will be passed to FinanceSystem
class MockGovernment:
    def __init__(self, initial_assets):
        self.assets = initial_assets
    def get_debt_to_gdp_ratio(self):
        return 0.5
    def deposit(self, amount): self.assets += amount
    def withdraw(self, amount): self.assets -= amount

class MockCentralBank:
    def __init__(self, initial_cash):
        self.assets = {"cash": initial_cash, "bonds": []}
    def get_base_rate(self):
        return 0.01
    def purchase_bonds(self, bond):
        self.assets["bonds"].append(bond)
    def deposit(self, amount): self.assets['cash'] += amount
    def withdraw(self, amount): self.assets['cash'] -= amount

class MockBank:
    def __init__(self, initial_assets):
        self.assets = initial_assets
    def deposit(self, amount): self.assets += amount
    def withdraw(self, amount): self.assets -= amount

class MockFirm:
    def __init__(self, id, initial_cash_reserve):
        self.id = id
        self.cash_reserve = initial_cash_reserve
        # Mock the finance component of the firm
        self.finance = MagicMock()
        self.has_bailout_loan = False
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

    def test_bailout_loan_maintains_money_supply(self):
        """
        Verify that granting a bailout loan correctly transfers assets
        without changing the total money supply.
        """
        initial_total_assets = self.mock_gov.assets + self.mock_firm.cash_reserve
        bailout_amount = 500

        self.finance_system.grant_bailout_loan(self.mock_firm, bailout_amount)

        # Assertions
        self.assertEqual(self.mock_gov.assets, 10000 - bailout_amount)
        self.assertEqual(self.mock_firm.cash_reserve, 100 + bailout_amount)

        final_total_assets = self.mock_gov.assets + self.mock_firm.cash_reserve
        self.assertEqual(initial_total_assets, final_total_assets)
        self.assertTrue(self.mock_firm.has_bailout_loan)
        self.mock_firm.finance.add_liability.assert_called_once()

    def test_qe_bond_issuance_maintains_money_supply(self):
        """
        Verify that issuing bonds under QE correctly transfers assets
        from the Central Bank to the Government.
        """
        # Force high yield to trigger QE
        self.mock_gov.get_debt_to_gdp_ratio = lambda: 1.5

        initial_total_assets = self.mock_gov.assets + self.mock_cb.assets['cash']
        bond_amount = 1000

        self.finance_system.issue_treasury_bonds(bond_amount, current_tick=1)

        # Assertions
        self.assertEqual(self.mock_gov.assets, 10000 + bond_amount)
        self.assertEqual(self.mock_cb.assets['cash'], 5000 - bond_amount)

        final_total_assets = self.mock_gov.assets + self.mock_cb.assets['cash']
        self.assertEqual(initial_total_assets, final_total_assets)
        self.assertEqual(len(self.mock_cb.assets['bonds']), 1)

    def test_market_bond_issuance_maintains_money_supply(self):
        """
        Verify that issuing bonds to the market correctly transfers assets
        from the commercial bank to the Government.
        """
        # Ensure low yield to avoid QE
        self.mock_gov.get_debt_to_gdp_ratio = lambda: 0.5

        initial_total_assets = self.mock_gov.assets + self.mock_bank.assets
        bond_amount = 2000

        self.finance_system.issue_treasury_bonds(bond_amount, current_tick=1)

        # Assertions
        self.assertEqual(self.mock_gov.assets, 10000 + bond_amount)
        self.assertEqual(self.mock_bank.assets, 20000 - bond_amount)

        final_total_assets = self.mock_gov.assets + self.mock_bank.assets
        self.assertEqual(initial_total_assets, final_total_assets)


if __name__ == '__main__':
    unittest.main()
