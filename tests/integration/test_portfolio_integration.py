import unittest
from unittest.mock import MagicMock
from simulation.decisions.portfolio_manager import PortfolioManager
from simulation.core_agents import Household
from simulation.bank import Bank

class TestPortfolioIntegration(unittest.TestCase):
    def test_portfolio_manager_logic(self):
        # Case 1: Normal
        # Liquid: 10000
        # Risk Aversion: 1.0
        # Risk Free: 0.05
        # Equity: 0.15
        # Survival: 1000 -> Safety Margin 3000 (1000 Cash, 2000 Deposit)
        # Surplus: 10000 - 3000 = 7000
        # Excess Return: 0.10
        # Sigma^2: 0.04
        # Lambda * Sigma^2 = 0.04
        # Weight: 0.10 / 0.04 = 2.5 -> Cap 1.0
        # Result: Target Equity = 7000. Target Deposit = 2000 + 0 = 2000. Target Cash = 1000.

        cash, deposit, equity = PortfolioManager.optimize_portfolio(
            total_liquid_assets=10000.0,
            risk_aversion=1.0,
            risk_free_rate=0.05,
            equity_return_proxy=0.15,
            survival_cost=1000.0,
            inflation_expectation=0.0
        )

        self.assertEqual(cash, 1000.0)
        self.assertEqual(deposit, 2000.0)
        self.assertEqual(equity, 7000.0)

    def test_portfolio_manager_risk_averse(self):
        # Case 2: Risk Averse (Lambda=10.0)
        # Lambda * Sigma^2 = 10 * 0.04 = 0.4
        # Excess Return: 0.10
        # Excess < Required (0.10 < 0.4) -> No Equity

        cash, deposit, equity = PortfolioManager.optimize_portfolio(
            total_liquid_assets=10000.0,
            risk_aversion=10.0,
            risk_free_rate=0.05,
            equity_return_proxy=0.15,
            survival_cost=1000.0,
            inflation_expectation=0.0
        )

        self.assertEqual(cash, 1000.0)
        self.assertEqual(deposit, 9000.0) # All surplus to deposit
        self.assertEqual(equity, 0.0)

    def test_bank_deposit_balance(self):
        config_manager = MagicMock()
        bank = Bank(1, 100000.0, config_manager=config_manager)
        bank.deposits = {
            "d1": MagicMock(depositor_id=1, amount=100.0),
            "d2": MagicMock(depositor_id=2, amount=200.0),
            "d3": MagicMock(depositor_id=1, amount=50.0)
        }

        balance = bank.get_deposit_balance(1)
        self.assertEqual(balance, 150.0)

        balance_2 = bank.get_deposit_balance(2)
        self.assertEqual(balance_2, 200.0)

        balance_3 = bank.get_deposit_balance(3)
        self.assertEqual(balance_3, 0.0)

if __name__ == '__main__':
    unittest.main()
