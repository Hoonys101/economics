from simulation.systems.settlement_system import SettlementSystem
from simulation.core_agents import Household

class FinancialSentry:
    _is_active = False

    @classmethod
    def unlock(cls):
        cls._is_active = True

    @classmethod
    def lock(cls):
        cls._is_active = False
