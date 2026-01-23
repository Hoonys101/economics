import sys
from pathlib import Path
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from simulation.bank import Bank, Loan, Deposit
from simulation.loan_market import LoanMarket
from simulation.models import Order


class TestBankingTransactionLogic(unittest.TestCase):
    def setUp(self):
        self.bank = Bank(id=999, initial_assets=1000000.0, config_module=config)
        self.loan_market = LoanMarket(
            market_id="loan_market", bank=self.bank, config_module=config
        )

        self.agent_id = 101

    def test_repayment_transaction_direction(self):
        print("\nTesting: Repayment Transaction Direction")

        # Setup: Grant a loan so we have something to repay
        loan_amount = 1000.0
        loan_id = self.bank.grant_loan(self.agent_id, loan_amount, term_ticks=50)

        # Create Repayment Order
        repay_amount = 100.0
        repay_order = Order(
            agent_id=self.agent_id,
            order_type="REPAYMENT",
            item_id=loan_id,
            quantity=repay_amount,
            price=1.0,
            market_id="loan_market",
        )

        txs = self.loan_market.place_order(repay_order, current_tick=2)

        self.assertEqual(len(txs), 1)
        tx = txs[0]

        # Verify Direction
        # Buyer PAYS -> Seller RECEIVES
        # Repayment: Agent PAYS Bank
        print(
            f"Transaction: Buyer={tx.buyer_id}, Seller={tx.seller_id}, Amt={tx.quantity}"
        )

        self.assertEqual(tx.buyer_id, self.agent_id, "Buyer should be Agent (Paying)")
        self.assertEqual(
            tx.seller_id, self.bank.id, "Seller should be Bank (Receiving)"
        )
        self.assertEqual(tx.quantity, repay_amount)

        print("✅ Repayment Transaction Direction Verified")


if __name__ == "__main__":
    unittest.main()
