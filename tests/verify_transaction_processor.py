from simulation.systems.transaction_processor import TransactionProcessor
from simulation.models import Transaction
from unittest.mock import MagicMock
import logging

def test_tax_collection_args():
    config = MagicMock()
    config.SALES_TAX_RATE = 0.1
    config.GOODS = {"apple": {}}

    tp = TransactionProcessor(config)

    state = MagicMock()
    gov = MagicMock()
    state.government = gov
    # Mock calculate_income_tax for other paths, though we test 'goods' here
    gov.calculate_income_tax.return_value = 0.0

    state.settlement_system = None # Force fallback or direct call logic
    state.market_data = {}
    state.time = 0

    # Buyer Object
    buyer = MagicMock()
    buyer.id = 1
    buyer.assets = 100.0
    # Add check_solvency mock
    buyer.check_solvency = MagicMock()

    # Seller Object
    seller = MagicMock()
    seller.id = 2
    seller.inventory = {}
    seller.deposit = MagicMock()

    state.agents = {1: buyer, 2: seller}

    # Transaction
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

    # Execute
    tp.execute(state)

    # Verify collect_tax call
    # gov.collect_tax(tax_amount, tax_type, payer, tick)
    # Expected: payer is buyer (object), not buyer.id

    if not gov.collect_tax.called:
        print("collect_tax not called!")
        return

    args = gov.collect_tax.call_args
    print(f"Call args: {args}")
    # args[0] is positional args tuple: (amount, type, payer, tick)
    payer_arg = args[0][2] # 3rd arg

    if payer_arg == buyer:
        print("SUCCESS: Payer passed as object.")
    elif payer_arg == buyer.id:
        print("FAILURE: Payer passed as ID.")
    else:
        print(f"FAILURE: Unknown payer arg: {payer_arg}")

if __name__ == "__main__":
    test_tax_collection_args()
