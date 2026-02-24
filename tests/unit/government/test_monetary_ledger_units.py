from modules.government.components.monetary_ledger import MonetaryLedger
from simulation.models import Transaction
from modules.system.constants import ID_CENTRAL_BANK
from modules.system.api import DEFAULT_CURRENCY

def test_monetary_ledger_uses_pennies_source_and_returns_pennies():
    """
    Verifies that MonetaryLedger uses tx.total_pennies (SSoT) as source
    and returns the delta in Pennies.
    """
    ledger = MonetaryLedger()
    ledger.reset_tick_flow()
    
    # Simulate a 1.00 USD (100 Penny) expansion from Central Bank
    # We set quantity/price such that price*quantity != total_pennies/100
    # to ensure SSoT is used.
    tx = Transaction(
        buyer_id=ID_CENTRAL_BANK,
        seller_id=101, # Public agent
        item_id="mint",
        quantity=999.0, # Irrelevant
        price=1.0,      # Irrelevant
        total_pennies=100, # SSoT: 100 pennies = 1.00 USD
        market_id="monetary_policy",
        transaction_type="money_creation",
        time=1
    )
    
    ledger.process_transactions([tx])
    
    delta = ledger.get_monetary_delta(DEFAULT_CURRENCY)
    
    # Expected: 100 pennies
    assert delta == 100, f"Unit Mismatch! Expected 100 pennies, got {delta}"
