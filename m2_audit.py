from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import IMonetaryLedger
import logging

class MockLedger(IMonetaryLedger):
    def __init__(self):
        self.expansions = []
        self.contractions = []

    def record_monetary_expansion(self, amount, source, currency="USD"):
        self.expansions.append((amount, source, currency))

    def record_monetary_contraction(self, amount, source, currency="USD"):
        self.contractions.append((amount, source, currency))

    def get_total_m2_pennies(self, currency="USD"): return 0
    def get_expected_m2_pennies(self, currency="USD"): return 0
    def set_expected_m2(self, amount, currency="USD"): pass
    def get_system_debt_pennies(self, currency="USD"): return 0
    def record_system_debt_increase(self, amount, source, currency="USD"): pass
    def record_system_debt_decrease(self, amount, source, currency="USD"): pass
    def record_credit_expansion(self, amount, saga_id, loan_id, reason): pass
    def record_credit_destruction(self, amount, saga_id, loan_id, reason): pass

ledger = MockLedger()
s = SettlementSystem()
s.set_monetary_ledger(ledger)

class DummyAgent:
    def __init__(self, id_val, is_m2):
        self.id = id_val
        self._is_m2 = is_m2
        self.balance_pennies = 1000

    def get_balance(self, currency="USD"): return self.balance_pennies

a1 = DummyAgent(1, True)
a2 = DummyAgent(2, False)

# Patching _is_m2_agent
s._is_m2_agent = lambda x: x._is_m2

from simulation.systems.handlers.transfer_handler import DefaultTransferHandler
handler = DefaultTransferHandler()
from simulation.models import Transaction
tx = Transaction(buyer_id=a1.id, seller_id=a2.id, item_id="usd", quantity=1.0, price=10.0, total_pennies=1000, market_id="m", transaction_type="transfer", time=0)
handler.handle(tx, a1, a2, None)
print("Expansions:", ledger.expansions)
print("Contractions:", ledger.contractions)
