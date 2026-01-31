import pytest
from unittest.mock import MagicMock, call
from simulation.systems.transaction_manager import TransactionManager
from simulation.models import Transaction

def test_transaction_manager_uses_escrow_for_goods():
    # Setup dependencies
    registry = MagicMock()
    accounting = MagicMock()
    settlement = MagicMock()
    central_bank = MagicMock()
    config = MagicMock()
    config.SALES_TAX_RATE = 0.1
    config.GOODS = {"apple": {}}
    escrow_agent = MagicMock()

    # Initialize Manager
    tm = TransactionManager(
        registry=registry,
        accounting_system=accounting,
        settlement_system=settlement,
        central_bank_system=central_bank,
        config=config,
        escrow_agent=escrow_agent,
        handlers={}
    )

    # Setup State
    state = MagicMock()
    gov = MagicMock()
    state.government = gov
    state.market_data = {}
    state.time = 0
    state.effects_queue = []

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

    # Mock Settlement Success for all steps
    settlement.transfer.return_value = True

    # Execute
    tm.execute(state)

    # Verify 3-Step Escrow Logic
    # 1. Buyer -> Escrow (Total Cost: 10 + 1 = 11)
    # 2. Escrow -> Seller (Trade Value: 10)
    # 3. Escrow -> Gov (Tax: 1)

    assert settlement.transfer.call_count == 3
    calls = settlement.transfer.call_args_list

    # Step 1
    assert calls[0][0][0] == buyer
    assert calls[0][0][1] == escrow_agent
    assert calls[0][0][2] == 11.0

    # Step 2
    assert calls[1][0][0] == escrow_agent
    assert calls[1][0][1] == seller
    assert calls[1][0][2] == 10.0

    # Step 3
    assert calls[2][0][0] == escrow_agent
    assert calls[2][0][1] == gov
    assert calls[2][0][2] == 1.0

    # Verify State Commitment
    registry.update_ownership.assert_called_once()
    accounting.record_transaction.assert_called_once()

    # Verify Gov Revenue Recorded
    gov.record_revenue.assert_called_once()


def test_transaction_manager_escrow_fails_insufficient_funds():
    # Setup dependencies
    registry = MagicMock()
    accounting = MagicMock()
    settlement = MagicMock()
    central_bank = MagicMock()
    config = MagicMock()
    config.SALES_TAX_RATE = 0.1
    config.GOODS = {"apple": {}}
    escrow_agent = MagicMock()

    # Initialize Manager
    tm = TransactionManager(
        registry=registry,
        accounting_system=accounting,
        settlement_system=settlement,
        central_bank_system=central_bank,
        config=config,
        escrow_agent=escrow_agent,
        handlers={}
    )

    # Setup State
    state = MagicMock()
    gov = MagicMock()
    state.government = gov
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

    # Mock Settlement FAILURE (Step 1)
    settlement.transfer.side_effect = [False]

    # Execute
    tm.execute(state)

    # Verify Step 1 Attempted
    settlement.transfer.assert_called_once()
    args = settlement.transfer.call_args
    assert args[0][0] == buyer
    assert args[0][1] == escrow_agent

    # Verify NO further steps
    assert settlement.transfer.call_count == 1

    # Verify NO State Commitment
    registry.update_ownership.assert_not_called()
    accounting.record_transaction.assert_not_called()


def test_transaction_manager_routes_to_central_bank():
    # Setup dependencies
    registry = MagicMock()
    accounting = MagicMock()
    settlement = MagicMock()
    central_bank = MagicMock() # Minting Authority
    config = MagicMock()
    escrow_agent = MagicMock()

    tm = TransactionManager(
        registry=registry,
        accounting_system=accounting,
        settlement_system=settlement,
        central_bank_system=central_bank,
        config=config,
        escrow_agent=escrow_agent
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
    escrow_agent = MagicMock()

    handler = MagicMock() # Specialized Handler
    handler.handle.return_value = True

    tm = TransactionManager(
        registry=registry,
        accounting_system=accounting,
        settlement_system=settlement,
        central_bank_system=central_bank,
        config=config,
        escrow_agent=escrow_agent,
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
