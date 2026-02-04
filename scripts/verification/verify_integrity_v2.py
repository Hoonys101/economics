import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from simulation.systems.transaction_manager import TransactionManager
from simulation.systems.registry import Registry
from simulation.systems.accounting import AccountingSystem
from simulation.systems.central_bank_system import CentralBankSystem
from simulation.systems.settlement_system import SettlementSystem
from simulation.systems.handlers import InheritanceHandler
from simulation.models import Transaction
from modules.system.constants import ID_CENTRAL_BANK

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFICATION")

class MockWallet:
    def __init__(self, agent):
        self.agent = agent
        self.owner_id = agent.id
    def get_balance(self, currency="USD"):
        return self.agent.assets
    def add(self, amount, currency="USD", memo=""):
        pass
    def subtract(self, amount, currency="USD", memo=""):
        pass
    def get_all_balances(self):
        return {"USD": self.agent.assets}

def verify_zero_sum():
    logger.info("Starting Zero-Sum Verification...")

    # 1. Setup Systems
    logger.info("Initializing Systems...")
    settlement = SettlementSystem(logger=logger)
    registry = Registry(logger=logger)
    accounting = AccountingSystem(logger=logger)

    # Mock Central Bank Agent
    cb_agent = MagicMock()
    cb_agent.id = ID_CENTRAL_BANK
    cb_agent.assets = {"cash": 0.0} # Not used by Settlement check for CB

    cb_system = CentralBankSystem(cb_agent, settlement, logger=logger)

    handlers = {
        "inheritance_distribution": InheritanceHandler()
    }

    config = MagicMock()
    config.SALES_TAX_RATE = 0.0 # Simplify
    config.INCOME_TAX_PAYER = "HOUSEHOLD"

    tm = TransactionManager(
        registry=registry,
        accounting_system=accounting,
        settlement_system=settlement,
        central_bank_system=cb_system,
        config=config,
        handlers=handlers,
        logger=logger,
        escrow_agent=MagicMock()
    )

    # 2. Setup Agents
    buyer = MagicMock()
    buyer.id = 1
    buyer.assets = 1000.0
    # Mock withdraw/deposit
    def b_withdraw(amt, currency="USD"): buyer.assets -= amt
    def b_deposit(amt, currency="USD"): buyer.assets += amt
    buyer.withdraw = b_withdraw
    buyer.deposit = b_deposit
    buyer.wallet = MockWallet(buyer)

    seller = MagicMock()
    seller.id = 2
    seller.assets = 500.0
    def s_withdraw(amt, currency="USD"): seller.assets -= amt
    def s_deposit(amt, currency="USD"): seller.assets += amt
    seller.withdraw = s_withdraw
    seller.deposit = s_deposit
    seller.wallet = MockWallet(seller)

    # Government (for tax)
    gov = MagicMock()
    gov.id = "GOV"
    gov.assets = 0.0
    def g_deposit(amt, currency="USD"): gov.assets += amt
    gov.deposit = g_deposit
    gov.wallet = MockWallet(gov)
    # Mock collect_tax to just deposit
    def collect_tax(amount, type, payer, time):
        # We need to transfer from payer to gov
        if settlement.transfer(payer, gov, amount, "tax"):
            return {'success': True}
        return {'success': False}
    gov.collect_tax = collect_tax

    # State
    state = MagicMock()
    state.agents = {1: buyer, 2: seller, "GOV": gov}
    state.government = gov
    state.market_data = {}
    state.time = 0
    state.inactive_agents = {}

    # 3. Execute Transaction (Goods Trade)
    logger.info("Executing Goods Trade (100.0)...")
    tx = Transaction(
        buyer_id=1,
        seller_id=2,
        item_id="item_x",
        price=10.0,
        quantity=10.0,
        market_id="goods",
        transaction_type="goods",
        time=0
    )
    state.transactions = [tx]

    initial_total = buyer.assets + seller.assets + gov.assets
    tm.execute(state)
    final_total = buyer.assets + seller.assets + gov.assets

    logger.info(f"Buyer Assets: {buyer.assets} (Expected 900.0)")
    logger.info(f"Seller Assets: {seller.assets} (Expected 600.0)")
    logger.info(f"Gov Assets: {gov.assets} (Expected 0.0)")
    logger.info(f"Total Money: {initial_total} -> {final_total}")

    if abs(initial_total - final_total) > 0.0001:
        logger.error("ZERO-SUM VIOLATION!")
        sys.exit(1)

    assert buyer.assets == 900.0
    assert seller.assets == 600.0

    # 4. Execute Taxed Trade
    logger.info("Executing Taxed Trade (100.0 + 10% Tax)...")
    config.SALES_TAX_RATE = 0.1
    tx2 = Transaction(
        buyer_id=1,
        seller_id=2,
        item_id="item_y",
        price=10.0,
        quantity=10.0,
        market_id="goods",
        transaction_type="goods",
        time=1
    )
    state.transactions = [tx2]

    initial_total = buyer.assets + seller.assets + gov.assets
    tm.execute(state)
    final_total = buyer.assets + seller.assets + gov.assets

    logger.info(f"Buyer Assets: {buyer.assets} (Expected 790.0 - 100 trade - 10 tax)")
    logger.info(f"Seller Assets: {seller.assets} (Expected 700.0 - +100 trade)")
    logger.info(f"Gov Assets: {gov.assets} (Expected 10.0 - +10 tax)")

    if abs(initial_total - final_total) > 0.0001:
         logger.error("ZERO-SUM VIOLATION WITH TAX!")
         sys.exit(1)

    assert buyer.assets == 790.0
    assert seller.assets == 700.0
    assert gov.assets == 10.0

    logger.info("VERIFICATION SUCCESSFUL")

if __name__ == "__main__":
    verify_zero_sum()
