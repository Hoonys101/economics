import pytest
from unittest.mock import MagicMock
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.models import Transaction

def test_transaction_processor_enforces_settlement():
    config = MagicMock()
    config.SALES_TAX_RATE = 0.1
    config.GOODS = {"apple": {}}

    tp = TransactionProcessor(config)
    state = MagicMock()
    state.settlement_system = None
    # Add a dummy transaction to trigger the loop
    buyer = MagicMock()
    buyer.id = 1
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

    # Should raise RuntimeError if settlement_system is missing
    with pytest.raises(RuntimeError, match="SettlementSystem is required"):
        tp.execute(state)

def test_transaction_processor_uses_settlement():
    config = MagicMock()
    config.SALES_TAX_RATE = 0.1
    config.GOODS = {"apple": {}}

    tp = TransactionProcessor(config)

    state = MagicMock()
    gov = MagicMock()
    state.government = gov
    gov.calculate_income_tax.return_value = 0.0

    settlement = MagicMock()
    settlement.transfer.return_value = True
    state.settlement_system = settlement

    state.market_data = {}
    state.time = 0

    buyer = MagicMock()
    buyer.id = 1
    buyer.assets = 100.0
    buyer.check_solvency = MagicMock()

    seller = MagicMock()
    seller.id = 2
    seller.inventory = {}
    seller.deposit = MagicMock() # Should not be called directly for trade value

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

    tp.execute(state)

    # Verify settlement.transfer called
    settlement.transfer.assert_called_once()
    args = settlement.transfer.call_args
    # args: buyer, seller, amount, memo
    assert args[0][0] == buyer
    assert args[0][1] == seller
    assert args[0][2] == 10.0 # 1.0 * 10.0

    # Verify withdraw/deposit NOT called on agents (since we use settlement)
    # Note: seller.deposit might be called in other logic (e.g. specific minting) but for goods trade it shouldn't
    # In my code I replaced buyer.withdraw and seller.deposit with settlement.transfer
    buyer.withdraw.assert_not_called()
    seller.deposit.assert_not_called()

def test_transaction_processor_skips_on_settlement_failure():
    config = MagicMock()
    config.SALES_TAX_RATE = 0.1
    config.GOODS = {"apple": {}}

    tp = TransactionProcessor(config)
    state = MagicMock()
    state.government = MagicMock()
    state.market_data = {}
    state.time = 0

    settlement = MagicMock()
    settlement.transfer.return_value = False # TRANSFER FAILS
    state.settlement_system = settlement

    buyer = MagicMock()
    buyer.id = 1
    buyer.assets = 1000.0 # Fix TypeError comparison
    buyer.withdraw = MagicMock()
    buyer.check_solvency = MagicMock()

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

    tp.execute(state)

    settlement.transfer.assert_called_once()
    # Fallback should NOT happen
    buyer.withdraw.assert_not_called()
