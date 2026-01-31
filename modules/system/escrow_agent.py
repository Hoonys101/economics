from modules.finance.api import IFinancialEntity, InsufficientFundsError

class EscrowAgent(IFinancialEntity):
    """
    Acts as a temporary holding account for atomic transactions.
    Ensures funds are secured before distribution to sellers and government.
    """
    def __init__(self, id: int):
        self._id = id
        self._assets = 0.0

    @property
    def id(self) -> int:
        return self._id

    @property
    def assets(self) -> float:
        return self._assets

    def deposit(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Deposit amount must be positive")
        self._assets += amount

    def withdraw(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Withdraw amount must be positive")
        if self._assets < amount:
            raise InsufficientFundsError(f"EscrowAgent {self.id} has insufficient funds. Needed: {amount}, Has: {self._assets}")
        self._assets -= amount
