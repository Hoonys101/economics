from modules.finance.engine_api import BankStateDTO as BankStateDTO, DepositStateDTO as DepositStateDTO, EngineOutputDTO as EngineOutputDTO, FinancialLedgerDTO as FinancialLedgerDTO, ILoanBookingEngine as ILoanBookingEngine, LoanApplicationDTO as LoanApplicationDTO, LoanDecisionDTO as LoanDecisionDTO, LoanStateDTO as LoanStateDTO
from modules.simulation.api import AgentID as AgentID
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY

class LoanBookingEngine(ILoanBookingEngine):
    """
    Stateless engine to book approved loans.
    MIGRATION: Uses integer pennies.
    """
    def grant_loan(self, application: LoanApplicationDTO, decision: LoanDecisionDTO, ledger: FinancialLedgerDTO) -> EngineOutputDTO: ...
