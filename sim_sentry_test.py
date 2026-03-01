from modules.finance.api import IFinancialEntity
class DummyAgent:
    def __init__(self):
        self._cash = 0

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, value):
        from simulation.systems.settlement_system import FinancialSentry
        if not FinancialSentry._is_active:
            raise RuntimeError("Direct mutation of .cash is FORBIDDEN. Use SettlementSystem.")
        self._cash = value
