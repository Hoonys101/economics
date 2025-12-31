
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

import config
from simulation.bank import Bank, Loan, Deposit
from simulation.ai.household_ai import HouseholdAI

class TestBankingSystem(unittest.TestCase):
    def setUp(self):
        # Initialize Bank
        self.bank = Bank(id=999, initial_assets=1000000.0, config_module=config)

        # Mock Agents
        self.agent1 = MagicMock()
        self.agent1.id = 1
        self.agent1.assets = 1000.0
        self.agent1.is_active = True

        self.agent2 = MagicMock()
        self.agent2.id = 2
        self.agent2.assets = 1000.0
        self.agent2.is_active = True

        self.agents_dict = {1: self.agent1, 2: self.agent2}

    def test_interest_scaling_and_circulation(self):
        print("\nTesting Banking: Interest Scaling & Circulation")

        # 1. Grant Loan to Agent 1
        # Loan Amount: 1000, Annual Rate: 5% + 2% (spread) = 7%
        # Term: 50 ticks
        loan_amount = 1000.0
        loan_id = self.bank.grant_loan(self.agent1, loan_amount, term_ticks=50)

        self.assertIsNotNone(loan_id)
        self.assertEqual(self.agent1.assets, 2000.0) # 1000 + 1000

        loan = self.bank.loans[loan_id]
        expected_annual_rate = 0.05 + 0.02
        self.assertAlmostEqual(loan.annual_interest_rate, expected_annual_rate)

        # 2. Deposit from Agent 2
        # Deposit Amount: 1000
        # Rate: Loan Rate - Margin = 7% - 2% = 5%
        deposit_amount = 1000.0
        deposit_id = self.bank.deposit(self.agent2, deposit_amount)

        self.assertIsNotNone(deposit_id)
        self.assertEqual(self.agent2.assets, 0.0) # 1000 - 1000

        deposit = self.bank.deposits[deposit_id]
        expected_deposit_rate = expected_annual_rate - 0.02
        self.assertAlmostEqual(deposit.annual_interest_rate, expected_deposit_rate)

        # 3. Simulate 100 Ticks (1 Year)
        # Interest Per Tick (Loan) = (1000 * 0.07) / 100 = 0.7
        # Interest Per Tick (Deposit) = (1000 * 0.05) / 100 = 0.5
        # Net Bank Profit Per Tick = 0.2

        initial_bank_assets = self.bank.assets
        # Assets changed by operations:
        # Initial: 1,000,000
        # Loan Out: -1000 -> 999,000
        # Deposit In: +1000 -> 1,000,000

        self.assertEqual(self.bank.assets, 1000000.0)

        ticks_per_year = 100
        for _ in range(ticks_per_year):
            self.bank.run_tick(self.agents_dict)

        # Verify Loan Interest Collected
        # Total Interest = 1000 * 0.07 = 70.0
        # Agent 1 Assets should decrease by 70.0
        # Note: Agent 1 had 2000.0. Should be 1930.0
        self.assertAlmostEqual(self.agent1.assets, 2000.0 - 70.0, delta=0.01)

        # Verify Deposit Interest Paid
        # Total Interest = 1000 * 0.05 = 50.0
        # Agent 2 Assets should increase by 50.0
        # Note: Agent 2 had 0.0. Should be 50.0
        self.assertAlmostEqual(self.agent2.assets, 50.0, delta=0.01)

        # Verify Bank Profit
        # Bank collected 70, paid 50. Net +20.
        # Bank Assets: 1,000,000 + 20 = 1,000,020
        self.assertAlmostEqual(self.bank.assets, 1000020.0, delta=0.01)

        print(f"✅ Circulation Verified. Bank Profit: {self.bank.assets - 1000000.0}")

    def test_ai_debt_awareness(self):
        print("\nTesting AI Awareness: Debt Perception")

        # Mock Decision Engine
        mock_decision_engine = MagicMock()
        mock_decision_engine.config_module = config

        ai = HouseholdAI(agent_id="test_ai", ai_decision_engine=mock_decision_engine)

        # State 1: No Debt
        agent_data_clean = {
            "assets": 1000.0,
            "needs": {"survival": 20.0},
            "liabilities": 0.0
        }
        market_data = {}

        state_clean = ai._get_common_state(agent_data_clean, market_data)

        # State 2: High Debt
        agent_data_debt = {
            "assets": 1000.0,
            "needs": {"survival": 20.0},
            "liabilities": 800.0 # 80% Debt Ratio
        }

        state_debt = ai._get_common_state(agent_data_debt, market_data)

        print(f"State (No Debt): {state_clean}")
        print(f"State (High Debt): {state_debt}")

        # Verify States are Different
        self.assertNotEqual(state_clean, state_debt)

        # Verify Tuple Length (should be 4 now)
        self.assertEqual(len(state_clean), 4)

        # Verify Debt Index (3rd element) is higher in debt state
        # debt_idx for 0.0 ratio -> likely 0
        # debt_idx for 0.8 ratio -> likely high index
        self.assertGreater(state_debt[2], state_clean[2])

        print("✅ AI Awareness Verified: Agent perceives debt level.")

if __name__ == '__main__':
    unittest.main()
