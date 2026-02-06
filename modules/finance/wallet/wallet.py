from __future__ import annotations
import copy
from collections import defaultdict
from typing import Dict, List, Optional
from .api import IWallet, WalletOpLogDTO, CurrencyCode, DEFAULT_CURRENCY
from .audit import GLOBAL_WALLET_LOG
from modules.finance.api import InsufficientFundsError

class Wallet(IWallet):
    """
    An encapsulated, auditable container for an agent's multi-currency assets.
    """
    def __init__(
        self,
        owner_id: int,
        initial_balances: Optional[Dict[CurrencyCode, float]] = None,
        audit_log: Optional[List[WalletOpLogDTO]] = None,
        allow_negative_balance: bool = False
    ):
        self.owner_id = owner_id
        if initial_balances is None:
            initial_balances = {}
        self._balances: Dict[CurrencyCode, float] = defaultdict(float, initial_balances)
        self._audit_log = audit_log if audit_log is not None else GLOBAL_WALLET_LOG
        self.allow_negative_balance = allow_negative_balance

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        return self._balances[currency]

    def get_all_balances(self) -> Dict[CurrencyCode, float]:
        return copy.copy(self._balances)

    def add(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "", tick: int = -1) -> None:
        if amount < 0:
            raise ValueError("Cannot add a negative amount. Use subtract.")
        self._balances[currency] += amount
        self._log_operation(tick, currency, amount, memo)

    def subtract(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "", tick: int = -1) -> None:
        if amount < 0:
            raise ValueError("Cannot subtract a negative amount. Use add.")

        if not self.allow_negative_balance:
            current_balance = self._balances[currency]
            if current_balance < amount:
                # Use a small epsilon for float comparison if needed, but keeping simple for now
                raise InsufficientFundsError(
                    f"Agent {self.owner_id}: Cannot subtract {amount} {currency}. "
                    f"Balance is only {current_balance}."
                )

        self._balances[currency] -= amount
        self._log_operation(tick, currency, -amount, memo)

    def _log_operation(self, tick: int, currency: CurrencyCode, delta: float, memo: str):
        log_entry = WalletOpLogDTO(
            tick=tick,
            agent_id=self.owner_id,
            currency=currency,
            delta=delta,
            memo=memo,
            resulting_balance=self._balances[currency]
        )
        self._audit_log.append(log_entry)

    # --- Operator Overloading ---
    def __add__(self, other: IWallet) -> IWallet:
        # Returns a new wallet with summed balances?
        # The design document had these signatures but didn't specify behavior.
        # Assuming it returns a new generic wallet with combined balances.
        # This is rarely used in core logic, mostly for reporting or temp calculations.
        new_balances = self.get_all_balances()
        other_balances = other.get_all_balances()
        for curr, amt in other_balances.items():
            new_balances[curr] = new_balances.get(curr, 0.0) + amt

        return Wallet(0, new_balances) # 0 ID for temp wallet

    def __sub__(self, other: IWallet) -> IWallet:
        new_balances = self.get_all_balances()
        other_balances = other.get_all_balances()
        for curr, amt in other_balances.items():
            new_balances[curr] = new_balances.get(curr, 0.0) - amt

        return Wallet(0, new_balances)

    def __iadd__(self, other: IWallet) -> IWallet:
        # Merges other wallet into this one (transfer in?)
        # BUT this bypasses atomic logging if we just iterate.
        # Should we log? The spec is for readability.
        # "maintain readability in agent logic".
        # I will implement it as a series of adds.
        other_balances = other.get_all_balances()
        for curr, amt in other_balances.items():
            if amt > 0:
                self.add(amt, curr, memo="Wallet Merge")
            elif amt < 0:
                 # Should not happen for balances usually, but if it's a delta wallet...
                 self.subtract(abs(amt), curr, memo="Wallet Merge")
        return self

    def __isub__(self, other: IWallet) -> IWallet:
        other_balances = other.get_all_balances()
        for curr, amt in other_balances.items():
             if amt > 0:
                 self.subtract(amt, curr, memo="Wallet Subtract")
        return self
