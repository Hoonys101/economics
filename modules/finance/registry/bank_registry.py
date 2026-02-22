from typing import Dict, List, Optional
from modules.simulation.api import AgentID
from modules.finance.api import IBankRegistry
from modules.finance.engine_api import BankStateDTO, DepositStateDTO, LoanStateDTO

class BankRegistry(IBankRegistry):
    """
    Implementation of the Bank Registry service.
    Manages the collection of bank states within the financial system.
    """

    def __init__(self, initial_banks: Optional[Dict[AgentID, BankStateDTO]] = None):
        """
        Initializes the bank registry.

        Args:
            initial_banks: Optional initial dictionary of bank states.
                           If provided, it uses this dictionary directly (by reference).
        """
        self._banks: Dict[AgentID, BankStateDTO] = initial_banks if initial_banks is not None else {}

    @property
    def banks_dict(self) -> Dict[AgentID, BankStateDTO]:
        """
        Returns the underlying dictionary of banks.
        Required for integration with FinancialLedgerDTO.
        """
        return self._banks

    def register_bank(self, bank_state: BankStateDTO) -> None:
        """Registers a bank state."""
        self._banks[bank_state.bank_id] = bank_state

    def get_bank(self, bank_id: AgentID) -> Optional[BankStateDTO]:
        """Retrieves a bank state by ID."""
        return self._banks.get(bank_id)

    def get_all_banks(self) -> List[BankStateDTO]:
        """Returns all registered banks."""
        return list(self._banks.values())

    def get_deposit(self, bank_id: AgentID, deposit_id: str) -> Optional[DepositStateDTO]:
        """Retrieves a specific deposit state."""
        bank = self.get_bank(bank_id)
        if bank:
            return bank.deposits.get(deposit_id)
        return None

    def get_loan(self, bank_id: AgentID, loan_id: str) -> Optional[LoanStateDTO]:
        """Retrieves a specific loan state."""
        bank = self.get_bank(bank_id)
        if bank:
            return bank.loans.get(loan_id)
        return None
