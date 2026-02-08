from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from modules.finance.api import IDepositManager, DepositDTO
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY


# Default fallback
_DEFAULT_TICKS_PER_YEAR = 365.0

@dataclass
class _Deposit:
    depositor_id: int
    amount: float
    annual_interest_rate: float
    currency: CurrencyCode = DEFAULT_CURRENCY
    ticks_per_year: float = _DEFAULT_TICKS_PER_YEAR

    @property
    def tick_interest_rate(self) -> float:
        return self.annual_interest_rate / self.ticks_per_year

class DepositManager(IDepositManager):
    """
    Manages agent deposit accounts and interest calculations.
    """
    def __init__(self, config: Any = None):
        self._deposits: Dict[str, _Deposit] = {}
        self._next_deposit_id = 0
        self.config = config

        if hasattr(config, "get"):
            self.ticks_per_year = config.get("finance.ticks_per_year", _DEFAULT_TICKS_PER_YEAR)
        else:
            self.ticks_per_year = getattr(config, "TICKS_PER_YEAR", _DEFAULT_TICKS_PER_YEAR) if config else _DEFAULT_TICKS_PER_YEAR

    def create_deposit(self, owner_id: int, amount: float, interest_rate: float, currency: str = DEFAULT_CURRENCY) -> str:
        deposit_id = f"dep_{self._next_deposit_id}"
        self._next_deposit_id += 1

        deposit = _Deposit(
            depositor_id=owner_id,
            amount=amount,
            annual_interest_rate=interest_rate,
            currency=currency,
            ticks_per_year=self.ticks_per_year
        )
        self._deposits[deposit_id] = deposit
        return deposit_id

    def get_balance(self, agent_id: int) -> float:
        total = 0.0
        for deposit in self._deposits.values():
            if deposit.depositor_id == agent_id and deposit.currency == DEFAULT_CURRENCY:
                total += deposit.amount
        return total

    def get_total_deposits(self) -> float:
        """Returns total value of all deposits in DEFAULT_CURRENCY."""
        return sum(d.amount for d in self._deposits.values() if d.currency == DEFAULT_CURRENCY)

    def get_deposit_dto(self, agent_id: int) -> Optional[DepositDTO]:
        deposits = [d for d in self._deposits.values() if d.depositor_id == agent_id]
        if not deposits:
            return None

        total_balance = sum(d.amount for d in deposits)
        if total_balance == 0:
            avg_rate = 0.0
        else:
            avg_rate = sum(d.amount * d.annual_interest_rate for d in deposits) / total_balance

        return DepositDTO(
            owner_id=agent_id,
            balance=total_balance,
            interest_rate=avg_rate
        )

    def calculate_interest(self, current_tick: int) -> List[Tuple[int, float]]:
        """
        Calculates interest for all deposits.
        Returns list of (depositor_id, interest_amount).
        """
        interest_payments = []
        for deposit in self._deposits.values():
            interest = deposit.amount * deposit.tick_interest_rate
            if interest > 0:
                interest_payments.append((deposit.depositor_id, interest))
        return interest_payments

    def withdraw(self, agent_id: int, amount: float) -> bool:
        """
        Reduces deposit balance for a withdrawal.
        Returns True if successful, False if insufficient funds.
        """
        current_bal = self.get_balance(agent_id)
        if current_bal < amount:
            return False

        remaining_to_withdraw = amount
        deposits_to_remove = []

        # Iterate safely
        for dep_id, deposit in self._deposits.items():
            if deposit.depositor_id == agent_id and deposit.currency == DEFAULT_CURRENCY:
                if remaining_to_withdraw <= 0:
                    break

                take = min(deposit.amount, remaining_to_withdraw)
                deposit.amount -= take
                remaining_to_withdraw -= take

                if deposit.amount <= 1e-9:
                    deposits_to_remove.append(dep_id)

        for dep_id in deposits_to_remove:
            if dep_id in self._deposits:
                del self._deposits[dep_id]

        return True

    def terminate_deposit_by_id(self, deposit_id: str) -> None:
        if deposit_id in self._deposits:
            del self._deposits[deposit_id]

    def remove_deposit_match(self, owner_id: int, amount: float) -> bool:
        """
        Removes a deposit matching the owner and amount (approx).
        Used for loan rollback (void_loan).
        """
        for dep_id, deposit in self._deposits.items():
            if deposit.depositor_id == owner_id and abs(deposit.amount - amount) < 1e-9:
                del self._deposits[dep_id]
                return True
        return False
