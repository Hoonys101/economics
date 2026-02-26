from modules.finance.engine_api import EngineOutputDTO as EngineOutputDTO, FinancialLedgerDTO as FinancialLedgerDTO, IDebtServicingEngine as IDebtServicingEngine
from modules.finance.utils.currency_math import round_to_pennies as round_to_pennies

class DebtServicingEngine(IDebtServicingEngine):
    """
    Stateless engine to service debts (interest payments).
    MIGRATION: Uses integer pennies and Decimal math.
    """
    def service_all_debt(self, ledger: FinancialLedgerDTO) -> EngineOutputDTO: ...
