import pytest
from unittest.mock import MagicMock, Mock
from simulation.systems.central_bank_system import CentralBankSystem
from simulation.systems.transaction_manager import TransactionManager
from simulation.systems.settlement_system import SettlementSystem
from simulation.models import Order, Transaction
from modules.finance.api import OMOInstructionDTO
from modules.system.constants import ID_CENTRAL_BANK

class MockAgent:
    def __init__(self, agent_id, assets=0.0):
        self.id = agent_id
        self.assets = float(assets)
        self.total_money_issued = 0.0
        self.total_money_destroyed = 0.0
        self._econ_state = MagicMock()
        self._econ_state.assets = self.assets

    def deposit(self, amount, currency="USD"):
        self.assets += amount
        self._econ_state.assets = self.assets

    def withdraw(self, amount, currency="USD"):
        if self.id != ID_CENTRAL_BANK and self.assets < amount:
            from modules.finance.api import InsufficientFundsError
            raise InsufficientFundsError("Insufficient Funds")
        self.assets -= amount
        self._econ_state.assets = self.assets

@pytest.fixture
def omo_setup():
    # SettlementSystem checks for "CENTRAL_BANK" ID or "CentralBank" class name to allow overdraft (Minting)
    cb_agent = MockAgent(agent_id=ID_CENTRAL_BANK, assets=0.0)
    gov_agent = MockAgent(agent_id=0, assets=1000.0)
    household = MockAgent(agent_id=1, assets=500.0)

    logger = MagicMock()
    settlement = SettlementSystem(logger=logger)

    cb_system = CentralBankSystem(
        central_bank_agent=cb_agent,
        settlement_system=settlement,
        security_market_id="security_market",
        logger=logger
    )

    # Mock Simulation State
    state = MagicMock()
    state.agents = {
        cb_agent.id: cb_agent, # Use dynamic ID
        0: gov_agent,
        1: household
    }
    state.government = gov_agent
    state.transactions = []

    tx_manager = TransactionManager(
        registry=MagicMock(),
        accounting_system=MagicMock(),
        settlement_system=settlement,
        central_bank_system=cb_system,
        config=MagicMock(),
        escrow_agent=MagicMock(),
        logger=logger
    )

    return cb_system, tx_manager, state, cb_agent, gov_agent, household

def test_execute_omo_purchase_order_creation(omo_setup):
    cb_system, _, _, _, _, _ = omo_setup

    instruction: OMOInstructionDTO = {
        "operation_type": "purchase",
        "target_amount": 100.0
    }

    orders = cb_system.execute_open_market_operation(instruction)

    assert len(orders) == 1
    assert orders[0].agent_id == cb_system.id
    assert orders[0].order_type == "buy"
    assert orders[0].quantity == 100.0
    assert orders[0].price > 0 # High price for purchase
    assert orders[0].market_id == "security_market"

def test_execute_omo_sale_order_creation(omo_setup):
    cb_system, _, _, _, _, _ = omo_setup

    instruction: OMOInstructionDTO = {
        "operation_type": "sale",
        "target_amount": 50.0
    }

    orders = cb_system.execute_open_market_operation(instruction)

    assert len(orders) == 1
    assert orders[0].agent_id == cb_system.id
    assert orders[0].order_type == "sell"
    assert orders[0].quantity == 50.0
    assert orders[0].price == 0 # Market order
    assert orders[0].market_id == "security_market"

def test_process_omo_purchase_transaction(omo_setup):
    cb_system, tx_manager, state, cb_agent, gov_agent, household = omo_setup

    # Household sells bond to CB (OMO Purchase by CB)
    # CB pays Household
    trade_price = 100.0
    tx = Transaction(
        buyer_id=cb_agent.id,
        seller_id=household.id,
        item_id="government_bond",
        quantity=10.0,
        price=10.0, # Unit price 10.0 * Qty 10.0 = 100.0
        market_id="security_market",
        transaction_type="omo_purchase",
        time=1
    )
    state.transactions = [tx]

    initial_hh_assets = household._econ_state.assets
    initial_money_issued = gov_agent.total_money_issued

    tx_manager.execute(state)

    # Verify Household got paid
    assert household._econ_state.assets == initial_hh_assets + trade_price

    # Verify Gov Ledger Updated (Minting)
    assert gov_agent.total_money_issued == initial_money_issued + trade_price

def test_process_omo_sale_transaction(omo_setup):
    cb_system, tx_manager, state, cb_agent, gov_agent, household = omo_setup

    # Household buys bond from CB (OMO Sale by CB)
    # Household pays CB
    trade_price = 100.0
    tx = Transaction(
        buyer_id=household.id,
        seller_id=cb_agent.id,
        item_id="government_bond",
        quantity=5.0,
        price=20.0, # Unit price 20.0 * Qty 5.0 = 100.0
        market_id="security_market",
        transaction_type="omo_sale",
        time=1
    )
    state.transactions = [tx]

    initial_hh_assets = household._econ_state.assets
    initial_money_destroyed = gov_agent.total_money_destroyed

    tx_manager.execute(state)

    # Verify Household paid
    assert household._econ_state.assets == initial_hh_assets - trade_price

    # Verify Gov Ledger Updated (Burning)
    assert gov_agent.total_money_destroyed == initial_money_destroyed + trade_price
