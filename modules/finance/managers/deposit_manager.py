from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import config
from modules.finance.api import IDepositManager, DepositDTO
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

TICKS_PER_YEAR = config.TICKS_PER_YEAR

@dataclass
class _Deposit:
    depositor_id: int
    amount: float
    annual_interest_rate: float
    currency: CurrencyCode = DEFAULT_CURRENCY

    @property
    def tick_interest_rate(self) -> float:
        return self.annual_interest_rate / TICKS_PER_YEAR

class DepositManager(IDepositManager):
    """
    Manages agent deposit accounts and interest calculations.
    """
    def __init__(self):
        self._deposits: Dict[str, _Deposit] = {}
        self._next_deposit_id = 0

    def create_deposit(self, owner_id: int, amount: float, interest_rate: float, currency: str = DEFAULT_CURRENCY) -> str:
        deposit_id = f"dep_{self._next_deposit_id}"
        self._next_deposit_id += 1

        deposit = _Deposit(
            depositor_id=owner_id,
            amount=amount,
            annual_interest_rate=interest_rate,
            currency=currency
        )
        self._deposits[deposit_id] = deposit
        return deposit_id

    def get_balance(self, agent_id: int) -> float:
        total = 0.0
        for deposit in self._deposits.values():
            if deposit.depositor_id == agent_id and deposit.currency == DEFAULT_CURRENCY:
                total += deposit.amount
        return total

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
        # Find deposits for agent
        target_deposit = None
        target_dep_id = None

        # Simple strategy: Find first deposit with enough funds or partial?
        # Bank implementation: "if target_deposit is None or target_deposit.amount < amount: return False"
        # It implies it only checks ONE deposit (the last one iterated or random).
        # Better to iterate and find one that fits, or take from multiple.
        # But for exact parity with Bank logic:

        for dep_id, deposit in self._deposits.items():
            if deposit.depositor_id == agent_id and deposit.currency == DEFAULT_CURRENCY:
                target_deposit = deposit
                target_dep_id = dep_id
                # Bank code used `break` after finding matches.
                # "if deposit.depositor_id == depositor_id ... target_deposit = deposit ... break"
                # So it takes the FIRST one found.
                break

        if target_deposit is None or target_deposit.amount < amount:
            return False

        target_deposit.amount -= amount
        if target_deposit.amount <= 0:
            # If empty, remove it
            if target_dep_id in self._deposits:
                del self._deposits[target_dep_id]

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
