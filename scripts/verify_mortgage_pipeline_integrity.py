import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from simulation.bank import Bank
from simulation.systems.settlement_system import SettlementSystem
from simulation.loan_market import LoanMarket
from modules.finance.saga_handler import HousingTransactionSagaHandler
from modules.market.housing_planner_api import MortgageApplicationDTO
from simulation.models import RealEstateUnit
from simulation.core_agents import Household
from modules.common.config_manager.api import ConfigManager
from simulation.engine import Simulation
from simulation.db.repository import SimulationRepository
from unittest.mock import MagicMock

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

def verify_pipeline():
    logger.info("--- Starting Mortgage Pipeline Integrity Verification ---")

    # 1. Setup Environment
    config_manager = MagicMock()
    config_manager.get.side_effect = lambda key, default=None: default

    config_mock = MagicMock()
    config_mock.TICKS_PER_YEAR = 100
    config_mock.housing.max_ltv = 0.8
    config_mock.housing.max_dti = 0.5
    config_mock.DEFAULT_MORTGAGE_INTEREST_RATE = 0.05
    config_mock.DEFAULT_LOAN_TERM_TICKS = 3600

    # Mock Simulation State
    sim_mock = MagicMock()
    sim_mock.config_module = config_mock
    sim_mock.time = 1
    sim_mock.markets = {}

    # Create Systems
    settlement = SettlementSystem()
    bank = Bank(id=999, initial_assets=100000.0, config_manager=config_manager)
    # Ensure base_rate is set
    if bank.base_rate is None:
        bank.base_rate = 0.05
    bank.settlement_system = settlement # Circular dep usually handled by initializer
    settlement.bank = bank

    loan_market = LoanMarket("loan", bank, config_mock)
    sim_mock.markets["loan"] = loan_market
    sim_mock.settlement_system = settlement
    sim_mock.bank = bank

    # Registry Mock
    registry_mock = MagicMock()
    sim_mock.registry = registry_mock

    # Agents
    buyer = MagicMock(spec=Household)
    buyer.id = 101
    buyer.assets = 20000.0 # Cash for down payment

    # State update side effects for Buyer
    def buyer_deposit(amount):
        buyer.assets += amount
    def buyer_withdraw(amount):
        buyer.assets -= amount
    buyer.deposit.side_effect = buyer_deposit
    buyer.withdraw.side_effect = buyer_withdraw

    buyer.current_wage = 1000.0

    seller = MagicMock(spec=Household)
    seller.id = 102
    seller.assets = 0.0

    # State update side effects for Seller
    def seller_deposit(amount):
        seller.assets += amount
    seller.deposit.side_effect = seller_deposit

    agents = {101: buyer, 102: seller}
    sim_mock.agents = agents

    # Properties
    prop = RealEstateUnit(id=500, owner_id=102, condition=1.0)
    prop.estimated_value = 100000.0

    sim_mock.real_estate_units = [prop]
    sim_mock.world_state.real_estate_units = [prop]
    sim_mock.world_state.transactions = []

    # Saga Handler
    saga_handler = HousingTransactionSagaHandler(sim_mock)

    # 2. Execute Saga
    # Offer Price: 100,000
    # Down Payment: 20,000 (20%)
    # Principal: 80,000
    # LTV: 0.8 (OK)
    # Income: 8333/mo.
    # Loan Payment: ~430/mo (Interest only approx). DTI = 430/8333 = 0.05 (OK).

    saga_state = {
        "saga_id": "test_saga_1",
        "status": "INITIATED",
        "buyer_id": 101,
        "seller_id": -1, # Resolve
        "property_id": 500,
        "offer_price": 100000.0,
        "down_payment_amount": 20000.0,
        "loan_application": None,
        "mortgage_approval": None,
        "error_message": None
    }

    logger.info("Executing Saga Step: INITIATED -> COMPLETED")
    result_saga = saga_handler.execute_step(saga_state)

    # 3. Assertions
    logger.info(f"Saga Status: {result_saga['status']}")
    if result_saga['status'] != "COMPLETED":
        logger.error(f"Saga Failed: {result_saga.get('error_message')}")
        sys.exit(1)

    # Check Balances
    # Buyer: Started 20000. Paid 20000 (Down) + 80000 (Principal from Bank).
    # But Bank paid Principal directly to Buyer?
    # Logic:
    # 1. Bank -> Buyer (80000). Buyer has 20000+80000=100000.
    # 2. Buyer -> Seller (100000). Buyer has 0.

    # Mock objects don't update state automatically unless configured.
    # We rely on SettlementSystem.transfer calls.
    # Since we passed Real objects (Bank, Settlement) but Mocks for Buyer/Seller?
    # Wait, SettlementSystem calls `deposit`/`withdraw` on agents.
    # Mocks need to support this.

    # Re-run with simple objects or configure mocks.
    # SettlementSystem uses `agent.deposit` and `agent.withdraw`.
    # Let's verify method calls on Mocks.

    # Bank is REAL.
    # Buyer/Seller are MOCK.

    # Check Bank Assets
    # Started 100,000. Should be 20,000. (Paid out 80,000).
    logger.info(f"Bank Assets: {bank.assets}")
    assert bank.assets == 20000.0, f"Bank Assets mismatch: {bank.assets} != 20000.0"

    # Check Buyer Calls
    # Received 80000 (deposit). Withdrew 100000 (withdraw).
    # Net flow handled by Settlement?
    # Settlement:
    # 1. Bank -> Buyer (80000). Buyer.deposit(80000).
    # 2. Buyer -> Seller (100000). Buyer.withdraw(100000).

    buyer.deposit.assert_called_with(80000.0)
    buyer.withdraw.assert_called_with(100000.0)

    # Check Seller Calls
    # Received 100000.
    seller.deposit.assert_called_with(100000.0)

    # Check Loan Creation
    assert len(bank.loans) == 1, "Loan not created in Bank"
    loan = list(bank.loans.values())[0]
    assert loan.principal == 80000.0
    assert loan.borrower_id == 101
    assert loan.created_deposit_id is None, "Atomic Loan should not have created_deposit_id"

    logger.info("VERIFICATION SUCCESSFUL: Atomic Mortgage Pipeline Integrity Verified.")

if __name__ == "__main__":
    verify_pipeline()
