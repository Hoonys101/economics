from modules.government.components.monetary_ledger import MonetaryLedger
from simulation.models import Transaction
from modules.system.constants import ID_CENTRAL_BANK, DEFAULT_CURRENCY

def test_monetary_ledger_uses_pennies_not_dollars():
    """
    REPRODUCTION TEST: Verifies that MonetaryLedger tracks in Pennies.
    Currently, it incorrectly uses (price * quantity) which is Dollars.
    Expected: 100 Pennies.
    Actual (Bug): 1.0 (Dollars).
    """
    ledger = MonetaryLedger()
    ledger.reset_tick_flow()
    
    # Simulate a 1.00 USD (100 Penny) expansion from Central Bank
    tx = Transaction(
        buyer_id=ID_CENTRAL_BANK,
        seller_id=101, # Public agent
        item_id="mint",
        quantity=1.0,
        price=1.0,
        total_pennies=100, # SSoT
        market_id="monetary_policy",
        transaction_type="money_creation",
        time=1
    )
    
    ledger.process_transactions([tx])
    
    delta = ledger.get_monetary_delta(DEFAULT_CURRENCY)
    
    # If the bug exists, delta will be 1.0.
    # If fixed, delta should be 100.
    assert delta == 100, f"Unit Mismatch! Expected 100 pennies, got {delta}"
