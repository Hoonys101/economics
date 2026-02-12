import sys
import os
import logging
from unittest.mock import MagicMock
from typing import List, Tuple

# Add project root to path
sys.path.append(os.getcwd())

from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import IFinancialAgent

class MockAgent(IFinancialAgent):
    def __init__(self, id, initial_balance=0):
        self.id = id
        self._balance = initial_balance

    def get_balance(self, currency="USD"):
        return self._balance

    def _deposit(self, amount, currency="USD"):
        self._balance += amount

    def _withdraw(self, amount, currency="USD"):
        if self._balance < amount:
            raise ValueError("Insufficient funds")
        self._balance -= amount

def audit_sales_tax_atomicity():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("AuditSalesTax")
    logger.info("Starting Audit: Sales Tax Atomicity")

    # Setup
    settlement_system = SettlementSystem(logger=logger)

    buyer = MockAgent(1, initial_balance=100) # 100 pennies
    seller = MockAgent(2, initial_balance=0)
    government = MockAgent(3, initial_balance=0)

    # Scenario: Trade 100, Tax 10. Total 110. Buyer has 100.
    # Should fail atomically.

    credits: List[Tuple[IFinancialAgent, int, str]] = [
        (seller, 100, "goods_trade"),
        (government, 10, "sales_tax")
    ]

    logger.info("Executing settle_atomic with insufficient funds...")
    result = settlement_system.settle_atomic(buyer, credits, tick=1)

    # Verification
    errors = []

    if result:
        msg = "FAILURE: Transaction succeeded despite insufficient funds."
        logger.error(msg)
        errors.append(msg)
    else:
        logger.info("SUCCESS: Transaction failed as expected.")

    # Check Balances (Rollback verification)
    if buyer.get_balance() != 100:
        msg = f"FAILURE: Buyer balance changed. Expected 100, got {buyer.get_balance()}"
        logger.error(msg)
        errors.append(msg)

    if seller.get_balance() != 0:
        msg = f"FAILURE: Seller received funds. Expected 0, got {seller.get_balance()}"
        logger.error(msg)
        errors.append(msg)

    if government.get_balance() != 0:
        msg = f"FAILURE: Government received tax. Expected 0, got {government.get_balance()}"
        logger.error(msg)
        errors.append(msg)

    if errors:
        logger.error(f"Audit Failed with {len(errors)} errors.")
        sys.exit(1)

    logger.info("Audit Completed Successfully: Atomicity Preserved.")

if __name__ == "__main__":
    audit_sales_tax_atomicity()
