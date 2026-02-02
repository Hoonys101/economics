import unittest
from unittest.mock import MagicMock, Mock
from typing import List, Dict, Any

from simulation.systems.liquidation_manager import LiquidationManager, Claim
from simulation.firms import Firm
from simulation.core_agents import Household
from simulation.dtos.api import SimulationState

class TestLiquidationManager(unittest.TestCase):
    def setUp(self):
        self.mock_settlement = MagicMock()
        self.manager = LiquidationManager(self.mock_settlement)

        # Mock State
        self.mock_state = MagicMock(spec=SimulationState)
        self.mock_state.time = 1000
        self.mock_state.households = []
        self.mock_state.government = MagicMock()
        self.mock_state.government.id = "government"
        self.mock_state.agents = {"government": self.mock_state.government}

        # Mock Firm
        self.mock_firm = MagicMock(spec=Firm)
        self.mock_firm.id = 1
        self.mock_firm.config = MagicMock()
        self.mock_firm.config.ticks_per_year = 365
        self.mock_firm.config.severance_pay_weeks = 2.0
        self.mock_firm.config.corporate_tax_rate = 0.2
        self.mock_firm.finance = MagicMock()
        self.mock_firm.finance.balance = 0.0
        self.mock_firm.finance.current_profit = 0.0
        self.mock_firm.hr = MagicMock()
        self.mock_firm.hr.employees = []
        self.mock_firm.hr.unpaid_wages = {}
        self.mock_firm.hr.employee_wages = {}
        self.mock_firm.total_shares = 100.0
        self.mock_firm.treasury_shares = 0.0
        self.mock_firm.total_debt = 0.0

    def test_calculate_claims_severance(self):
        # Setup Employee with 2 years tenure
        emp1 = MagicMock(spec=Household)
        emp1.id = 101
        emp1._econ_state = MagicMock()
        emp1._econ_state.employment_start_tick = 1000 - (365 * 2) # 2 years ago

        self.mock_firm.hr.employees = [emp1]
        self.mock_firm.hr.employee_wages = {101: 100.0} # Wage 100

        # Severance = 2 years * 2 weeks * (365/52) ticks/week * 100 wage
        # ticks_per_week = 7.01923
        # severance_ticks = 2.0 * 2.0 * 7.01923 = 28.0769
        # amount = 28.0769 * 100.0 = 2807.69

        claims = self.manager.calculate_claims(self.mock_firm, self.mock_state)

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].tier, 1)
        self.assertEqual(claims[0].creditor_id, 101)
        self.assertIn("Severance", claims[0].description)
        self.assertAlmostEqual(claims[0].amount, 2807.69, delta=1.0)

    def test_calculate_claims_unpaid_wages(self):
        # Current tick 1000. Cutoff 1000 - 91 = 909.
        self.mock_firm.hr.unpaid_wages = {
            102: [(900, 50.0), (950, 50.0)] # 900 filtered out. Total 50.
        }

        claims = self.manager.calculate_claims(self.mock_firm, self.mock_state)

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].tier, 1)
        self.assertEqual(claims[0].creditor_id, 102)
        self.assertEqual(claims[0].amount, 50.0) # Filtered result
        self.assertEqual(claims[0].description, "Unpaid Wages")

    def test_calculate_claims_debt_and_tax(self):
        self.mock_firm.total_debt = 5000.0
        self.mock_firm.finance.current_profit = 1000.0
        # Tax = 1000 * 0.2 = 200.0

        claims = self.manager.calculate_claims(self.mock_firm, self.mock_state)

        # Claims: Debt (Tier 2), Tax (Tier 3)
        self.assertEqual(len(claims), 2)

        debt_claim = next(c for c in claims if c.tier == 2)
        self.assertEqual(debt_claim.amount, 5000.0)

        tax_claim = next(c for c in claims if c.tier == 3)
        self.assertEqual(tax_claim.amount, 200.0)
        self.assertEqual(tax_claim.creditor_id, "government")

    def test_execute_waterfall_full_payment(self):
        claims = [
            Claim(101, 100.0, 1, "Severance"),
            Claim("bank", 200.0, 2, "Loan"),
        ]
        available_cash = 400.0 # Enough for all + equity

        self.mock_firm.finance.balance = available_cash
        self.mock_state.agents[101] = MagicMock()
        self.mock_state.agents["bank"] = MagicMock()

        # Mock shareholders to return 0 shares to avoid Equity loop failing on MagicMock > 0
        self.mock_state.households = []
        self.mock_state.government = MagicMock()
        self.mock_state.government.shares_owned.get.return_value = 0.0

        self.manager.execute_waterfall(self.mock_firm, claims, available_cash, self.mock_state)

        # Verify calls to settlement system
        # Tier 1
        self.mock_settlement.transfer.assert_any_call(self.mock_firm, self.mock_state.agents[101], 100.0, "Liquidation Payout: Severance")
        # Tier 2
        self.mock_settlement.transfer.assert_any_call(self.mock_firm, self.mock_state.agents["bank"], 200.0, "Liquidation Payout: Loan")

        # Remaining 100 to equity?
        # We need mock shareholders
        # But this test didn't setup shareholders in state.households properly to verify equity,
        # but verified tiers 1 and 2.

    def test_execute_waterfall_pro_rata(self):
        claims = [
            Claim(101, 100.0, 1, "Severance"),
            Claim(102, 100.0, 1, "Severance"),
            Claim("bank", 500.0, 2, "Loan"),
        ]
        available_cash = 150.0
        # Tier 1 Total: 200. Cash: 150.
        # Pro-rata: 150 / 200 = 0.75
        # Each gets 75.0

        self.mock_state.agents[101] = MagicMock()
        self.mock_state.agents[102] = MagicMock()

        self.manager.execute_waterfall(self.mock_firm, claims, available_cash, self.mock_state)

        self.mock_settlement.transfer.assert_any_call(self.mock_firm, self.mock_state.agents[101], 75.0, "Liquidation Payout: Severance (Partial)")
        self.mock_settlement.transfer.assert_any_call(self.mock_firm, self.mock_state.agents[102], 75.0, "Liquidation Payout: Severance (Partial)")

        # Tier 2 gets nothing
        # Check call args to ensure bank wasn't paid
        transfers = self.mock_settlement.transfer.call_args_list
        # Should be 2 calls
        self.assertEqual(len(transfers), 2)

if __name__ == '__main__':
    unittest.main()
