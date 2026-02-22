import pytest
from unittest.mock import MagicMock, call
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from simulation.models import Transaction
from modules.finance.api import IFinancialAgent
from simulation.dtos.api import SimulationState

def test_transaction_processor_dispatch_to_handler():
    # Setup
    config = MagicMock()
    tp = TransactionProcessor(config_module=config)

    # Mock Handler
    handler = MagicMock()
    handler.handle.return_value = True
    tp.register_handler("test_type", handler)

    # Setup State
    state = MagicMock(spec=SimulationState)
    state.agents = {1: MagicMock(), 2: MagicMock()}
    state.transactions = [
        Transaction(
            buyer_id=1, seller_id=2, item_id="item", price=10, quantity=1,
            market_id="m", transaction_type="test_type", time=0
        , total_pennies=1000)
    ]
    state.taxation_system = MagicMock()
    state.public_manager = None
    state.bank = MagicMock()
    state.central_bank = MagicMock()
    state.settlement_system = MagicMock()
    state.primary_government = MagicMock()
    state.stock_market = MagicMock()
    state.real_estate_units = []
    state.market_data = {}
    state.logger = MagicMock()
    state.time = 0
    state.inactive_agents = {}
    state.shareholder_registry = MagicMock()
    state.effects_queue = []

    # Execute
    tp.execute(state)

    # Verify Dispatch
    handler.handle.assert_called_once()
    args = handler.handle.call_args
    assert args[0][0] == state.transactions[0] # tx
    assert args[0][1] == state.agents[1] # buyer
    assert args[0][2] == state.agents[2] # seller
    # args[0][3] is context

def test_transaction_processor_ignores_credit_creation():
    config = MagicMock()
    tp = TransactionProcessor(config_module=config)

    state = MagicMock(spec=SimulationState)
    state.transactions = [
        Transaction(
            buyer_id=1, seller_id=2, item_id="credit", price=10, quantity=1,
            market_id="m", transaction_type="credit_creation", time=0
        , total_pennies=1000)
    ]
    state.agents = {1: MagicMock(), 2: MagicMock()}
    state.public_manager = None
    state.bank = MagicMock()
    state.central_bank = MagicMock()
    state.settlement_system = MagicMock()
    state.primary_government = MagicMock()
    state.stock_market = MagicMock()
    state.real_estate_units = []
    state.market_data = {}
    state.logger = MagicMock()
    state.time = 0
    state.inactive_agents = {}
    state.shareholder_registry = MagicMock()
    state.effects_queue = []

    # No handler registered
    # Execute
    tp.execute(state)

    # Should not raise warning or error
    state.logger.warning.assert_not_called()

def test_goods_handler_uses_atomic_settlement():
    # Setup Context
    context = MagicMock()
    context.taxation_system.calculate_tax_intents.return_value = []
    context.settlement_system.settle_atomic.return_value = True
    context.config_module.GOODS = {"apple": {}}

    handler = GoodsTransactionHandler()

    buyer = MagicMock(spec=IFinancialAgent)
    buyer.id = 1
    # Solvency check requires enough assets.
    # Price is 10.0, so 1000 pennies.
    # Buyer balance must be >= 1000 pennies.
    buyer.get_balance.return_value = 10000 # 10000 pennies ($100)
    buyer.inventory = {}
    seller = MagicMock()
    seller.id = 2
    seller.inventory = {}

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="apple", price=10.0, quantity=1.0,
        market_id="goods", transaction_type="goods", time=0,
        total_pennies=1000 # Explicitly set pennies
    )

    # Execute
    handler.handle(tx, buyer, seller, context)

    # Verify settle_atomic called
    context.settlement_system.settle_atomic.assert_called_once()
    args = context.settlement_system.settle_atomic.call_args
    # args: (buyer, credits, time)
    assert args[0][0] == buyer
    credits = args[0][1]
    # Expect [(seller, 1000, ...)] - integer pennies
    assert len(credits) == 1
    assert credits[0][0] == seller
    assert credits[0][1] == 1000

def test_public_manager_routing():
    config = MagicMock()
    tp = TransactionProcessor(config_module=config)

    pm_handler = MagicMock()
    tp.register_public_manager_handler(pm_handler)

    state = MagicMock(spec=SimulationState)
    state.public_manager = MagicMock() # Ensure PM exists

    # Fill required fields
    state.bank = MagicMock()
    state.central_bank = MagicMock()
    state.settlement_system = MagicMock()
    state.primary_government = MagicMock()
    state.stock_market = MagicMock()
    state.real_estate_units = []
    state.market_data = {}
    state.logger = MagicMock()
    state.time = 0
    state.inactive_agents = {}
    state.shareholder_registry = MagicMock()
    state.effects_queue = []

    # Transaction with PM as seller
    tx = Transaction(
        buyer_id=1, seller_id="PUBLIC_MANAGER", item_id="item", price=10, quantity=1,
        market_id="m", transaction_type="any_type", time=0
    , total_pennies=1000)
    state.transactions = [tx]
    state.agents = {1: MagicMock()}

    tp.execute(state)

    pm_handler.handle.assert_called_once()

def test_transaction_processor_dispatches_housing():
    config = MagicMock()
    tp = TransactionProcessor(config_module=config)

    housing_handler = MagicMock()
    tp.register_handler("housing", housing_handler)

    state = MagicMock(spec=SimulationState)
    state.transactions = [
        Transaction(
            buyer_id=1, seller_id=2, item_id="unit_1", price=100, quantity=1,
            market_id="housing", transaction_type="housing", time=0
        , total_pennies=10000)
    ]
    state.agents = {1: MagicMock(), 2: MagicMock()}
    state.taxation_system = MagicMock()
    state.public_manager = None
    state.bank = MagicMock()
    state.central_bank = MagicMock()
    state.settlement_system = MagicMock()
    state.primary_government = MagicMock()
    state.stock_market = MagicMock()
    state.real_estate_units = []
    state.market_data = {}
    state.logger = MagicMock()
    state.time = 0
    state.inactive_agents = {}
    state.shareholder_registry = MagicMock()
    state.effects_queue = []

    tp.execute(state)

    housing_handler.handle.assert_called_once()
