import pytest
from unittest.mock import MagicMock
from simulation.systems.transaction_manager import TransactionManager
from simulation.models import Transaction

def test_transaction_manager_uses_settlement_for_goods():
    # Setup dependencies
    registry = MagicMock()
    accounting = MagicMock()
    settlement = MagicMock()
    central_bank = MagicMock()
    config = MagicMock()
    config.SALES_TAX_RATE = 0.1
    config.GOODS = {"apple": {}}

    # Initialize Manager
    tm = TransactionManager(
        registry=registry,
        accounting_system=accounting,
        settlement_system=settlement,
        central_bank_system=central_bank,
        config=config,
        handlers={}
    )

    # Setup State
    state = MagicMock()
    gov = MagicMock()
    state.government = gov
    state.market_data = {}
    state.time = 0
    state.effects_queue = [] # Ensure this exists

    # Setup Agents
    buyer = MagicMock()
    buyer.id = 1
    buyer.assets = 100.0
    buyer.check_solvency = MagicMock()

    seller = MagicMock()
    seller.id = 2

    state.agents = {1: buyer, 2: seller}

    # Setup Transaction
    tx = Transaction(
        buyer_id=1,
        seller_id=2,
        item_id="apple",
        price=10.0,
        quantity=1.0,
        market_id="goods",
        transaction_type="goods",
        time=0
    )
    state.transactions = [tx]

    # Mock Settlement Success
    settlement.transfer.return_value = True

    # Execute
    tm.execute(state)

    # Verify Settlement Called
    settlement.transfer.assert_called_once()
    args = settlement.transfer.call_args
    # args: buyer, seller, amount, memo
    assert args[0][0] == buyer
    assert args[0][1] == seller
    assert args[0][2] == 10.0 # 1.0 * 10.0

    # Verify Tax Collection (0.1 rate)
    gov.collect_tax.assert_called_once()

    # Verify State Commitment
    registry.update_ownership.assert_called_once()
    accounting.record_transaction.assert_called_once()


def test_transaction_manager_skips_state_update_on_failure():
    # Setup dependencies
    registry = MagicMock()
    accounting = MagicMock()
    settlement = MagicMock()
    central_bank = MagicMock()
    config = MagicMock()
    config.SALES_TAX_RATE = 0.1
    config.GOODS = {"apple": {}}

    # Initialize Manager
    tm = TransactionManager(
        registry=registry,
        accounting_system=accounting,
        settlement_system=settlement,
        central_bank_system=central_bank,
        config=config,
        handlers={}
    )

    # Setup State
    state = MagicMock()
    state.government = MagicMock()
    state.market_data = {}
    state.time = 0

    buyer = MagicMock()
    buyer.id = 1
    buyer.assets = 100.0

    seller = MagicMock()
    seller.id = 2

    state.agents = {1: buyer, 2: seller}

    tx = Transaction(
        buyer_id=1,
        seller_id=2,
        item_id="apple",
        price=10.0,
        quantity=1.0,
        market_id="goods",
        transaction_type="goods",
        time=0
    )
    state.transactions = [tx]

    # Mock Settlement FAILURE
    settlement.transfer.return_value = False

    # Execute
    tm.execute(state)

    # Verify Settlement Attempted
    settlement.transfer.assert_called_once()

    # Verify State Commitment SKIPPED
    registry.update_ownership.assert_not_called()
    accounting.record_transaction.assert_not_called()


def test_transaction_manager_routes_to_central_bank():
    # Setup dependencies
    registry = MagicMock()
    accounting = MagicMock()
    settlement = MagicMock()
    central_bank = MagicMock() # Minting Authority
    config = MagicMock()

    tm = TransactionManager(
        registry=registry,
        accounting_system=accounting,
        settlement_system=settlement,
        central_bank_system=central_bank,
        config=config
    )

    state = MagicMock()
    state.market_data = {}
    state.time = 0

    # Buyer is usually Gov/CB for minting ops
    buyer = MagicMock()
    buyer.id = "CENTRAL_BANK"

    seller = MagicMock() # Bank receiving funds
    seller.id = "BANK"

    state.agents = {"CENTRAL_BANK": buyer, "BANK": seller}

    tx = Transaction(
        buyer_id="CENTRAL_BANK",
        seller_id="BANK",
        item_id="cash",
        price=1000.0,
        quantity=1.0,
        market_id="system",
        transaction_type="lender_of_last_resort",
        time=0
    )
    state.transactions = [tx]

    central_bank.mint_and_transfer.return_value = True

    tm.execute(state)

    # Verify routed to CentralBankSystem
    central_bank.mint_and_transfer.assert_called_once()

    # Verify settlement NOT called directly by manager (it's called by CB system)
    settlement.transfer.assert_not_called()


def test_transaction_manager_uses_handler():
    # Setup dependencies
    registry = MagicMock()
    accounting = MagicMock()
    settlement = MagicMock()
    central_bank = MagicMock()
    config = MagicMock()

    handler = MagicMock() # Specialized Handler
    handler.handle.return_value = True

    tm = TransactionManager(
        registry=registry,
        accounting_system=accounting,
        settlement_system=settlement,
        central_bank_system=central_bank,
        config=config,
        handlers={"special_saga": handler}
    )

    state = MagicMock()
    state.market_data = {}
    state.time = 0

    buyer = MagicMock()
    buyer.id = 1
    seller = MagicMock()
    seller.id = 2
    state.agents = {1: buyer, 2: seller}

    tx = Transaction(
        buyer_id=1,
        seller_id=2,
        item_id="thing",
        price=10.0,
        quantity=1.0,
        market_id="saga",
        transaction_type="special_saga",
        time=0
    )
    state.transactions = [tx]

    tm.execute(state)

    # Verify Handler Called
    handler.handle.assert_called_once_with(tx, buyer, seller, state)

    # Verify standard paths skipped
    settlement.transfer.assert_not_called()

    # Verify State Commitment IS called (Phase 2)
    # Even if Registry/Accounting do nothing for this type, they are invoked by the manager.
    registry.update_ownership.assert_called_once()
    accounting.record_transaction.assert_called_once()
