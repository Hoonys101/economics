from modules.finance.engine_api import FinancialLedgerDTO as FinancialLedgerDTO, IInterestRateEngine as IInterestRateEngine

class InterestRateEngine(IInterestRateEngine):
    """
    Stateless engine to update interest rates.
    """
    def update_rates(self, economic_indicators: dict, ledger: FinancialLedgerDTO) -> FinancialLedgerDTO: ...
