
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

import config
from simulation.bank import Bank, Loan, Deposit
from simulation.loan_market import LoanMarket
from simulation.models import Order

class TestBankingSystemVerification(unittest.TestCase):
    def setUp(self):
        self.bank = Bank(id=999, initial_assets=1000000.0, config_module=config)
        self.loan_market = LoanMarket(market_id="loan_market", bank=self.bank, config_module=config)

        self.agent1_id = 1
        self.agent2_id = 2

    def test_deposit_and_interest_circulation(self):
        print("\nTesting: Deposit and Interest Circulation")

        # 1. Deposit
        deposit_amount = 1000.0
        deposit_order = Order(
            agent_id=self.agent2_id,
            order_type="DEPOSIT",
            item_id="cash",
            quantity=deposit_amount,
            price=1.0,
            market_id="loan_market"
        )

        txs = self.loan_market.place_order(deposit_order, current_tick=1)

        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0].transaction_type, "deposit")
        self.assertEqual(txs[0].buyer_id, self.agent2_id) # Agent gives money
        self.assertEqual(txs[0].seller_id, self.bank.id) # Bank receives

        # Check Bank State
        # Bank methods no longer modify assets directly. Assets are moved by Engine via Transactions.
        # We manually simulate the transaction effect on bank assets here for verification.
        bank_assets = 1000000.0
        if txs:
            # Deposit Transaction: Agent -> Bank
            # Bank is Seller, Agent is Buyer? No.
            # LoanMarket: buyer_id=agent (pays), seller_id=bank (receives)
            bank_assets += txs[0].quantity

        self.assertEqual(bank_assets, 1000000.0 + deposit_amount)
        self.assertEqual(len(self.bank.deposits), 1)

        # 2. Loan
        loan_amount = 1000.0
        loan_order = Order(
            agent_id=self.agent1_id,
            order_type="LOAN_REQUEST",
            item_id="cash",
            quantity=loan_amount,
            price=0.07, # Requested rate, ignored by bank logic which uses base+spread
            market_id="loan_market"
        )

        txs = self.loan_market.place_order(loan_order, current_tick=1)

        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0].transaction_type, "loan")
        self.assertEqual(txs[0].buyer_id, self.bank.id) # Bank gives money
        self.assertEqual(txs[0].seller_id, self.agent1_id) # Agent receives

        # Check Bank State (Simulated)
        if txs:
            # Loan Transaction: Bank (Buyer) -> Agent (Seller)
            bank_assets -= txs[0].quantity

        self.assertEqual(bank_assets, 1000000.0 + deposit_amount - loan_amount)

        # 3. Interest Logic (Manual Check)
        # Bank.run_tick would modify assets if agents_dict passed.
        # Here we verify the rates are scaled.
        loan = list(self.bank.loans.values())[0]
        deposit = list(self.bank.deposits.values())[0]

        ticks_per_year = 100.0
        expected_loan_interest = (loan.remaining_balance * loan.annual_interest_rate) / ticks_per_year
        expected_deposit_interest = (deposit.amount * deposit.annual_interest_rate) / ticks_per_year

        self.assertGreater(expected_loan_interest, 0)
        self.assertGreater(expected_deposit_interest, 0)
        self.assertGreater(expected_loan_interest, expected_deposit_interest) # Spread

        print("✅ Deposit & Loan Flow Verified")

if __name__ == '__main__':
    unittest.main()
