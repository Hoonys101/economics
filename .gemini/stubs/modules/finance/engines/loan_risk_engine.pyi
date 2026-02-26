from modules.finance.engine_api import FinancialLedgerDTO as FinancialLedgerDTO, ILoanRiskEngine as ILoanRiskEngine, LoanApplicationDTO as LoanApplicationDTO, LoanDecisionDTO as LoanDecisionDTO

class LoanRiskEngine(ILoanRiskEngine):
    """
    Stateless engine to assess loan applications.
    MIGRATION: Uses integer pennies.
    """
    def assess(self, application: LoanApplicationDTO, ledger: FinancialLedgerDTO) -> LoanDecisionDTO: ...
