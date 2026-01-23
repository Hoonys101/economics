from typing import List, Optional, Any, TYPE_CHECKING
import logging
from modules.finance.api import IFinancialEntity, InsufficientFundsError

if TYPE_CHECKING:
    from simulation.systems.settlement_system import SettlementSystem
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class EconomicRefluxSystem(IFinancialEntity):
    """
    Captures money that leaks from the economy (sinks) and redistributes it
    to households, simulating a circular flow (or service sector wages).
    Implements IFinancialEntity to participate in SettlementSystem transfers.
    """
    def __init__(self):
        self._id = -100 # Special ID for Reflux System
        self._balance: float = 0.0

    @property
    def id(self) -> int:
        return self._id

    @property
    def assets(self) -> float:
        return self._balance

    @property
    def balance(self) -> float:
        """Alias for assets, used by verification scripts."""
        return self._balance

    def deposit(self, amount: float) -> None:
        """Deposits funds into the reflux system."""
        if amount > 0:
            self._balance += amount
            # logger.debug(f"REFLUX_DEPOSIT | Balance increased by {amount:.2f}. New Balance: {self._balance:.2f}")

    def withdraw(self, amount: float) -> None:
        """Withdraws funds from the reflux system."""
        if amount > 0:
            if self._balance < amount:
                 raise InsufficientFundsError(f"RefluxSystem has insufficient funds. Available: {self._balance:.2f}, Requested: {amount:.2f}")
            self._balance -= amount

    def capture(self, amount: float, source: str, category: str):
        """
        Legacy method for capturing money.
        DEPRECATED: Use SettlementSystem.transfer(source, reflux, amount, ...) instead.
        This method is kept for any remaining legacy calls but now manually adds assets,
        which bypasses SettlementSystem if used directly!
        Ideally, this should raise a warning or be removed if all callers are refactored.
        """
        if amount > 0:
            self._balance += amount
            logger.debug(f"REFLUX_CAPTURE | Captured {amount:.2f} from {source} ({category})")

    def distribute(self, households: list, settlement_system: 'SettlementSystem'):
        """
        Distributes the total balance equally to all active households
        using the SettlementSystem.
        """
        if self._balance <= 0.1: # Threshold to avoid tiny transfers
            return

        # Filter for active households only
        active_households = [h for h in households if getattr(h, "is_active", True)]

        if not active_households:
            return

        total_amount = self._balance
        amount_per_household = total_amount / len(active_households)

        successful_transfers = 0
        for agent in active_households:
            memo = "Reflux Distribution (Service Sector Wages)"
            if settlement_system.transfer(self, agent, amount_per_household, memo):
                successful_transfers += 1

                # Record as additional labor income (Service Sector)
                if hasattr(agent, "labor_income_this_tick"):
                    agent.labor_income_this_tick += amount_per_household

                # Legacy support if needed
                if hasattr(agent, 'income_history') and isinstance(agent.income_history, dict):
                     agent.income_history['service'] = agent.income_history.get('service', 0.0) + amount_per_household

        logger.info(
            f"REFLUX_DISTRIBUTE | Distributed {total_amount:.2f} to {successful_transfers}/{len(active_households)} households. ({amount_per_household:.2f} each)",
            extra={"tags": ["reflux", "distribution"], "total_amount": total_amount}
        )

        # Note: Balance is reduced by withdrawals in SettlementSystem.transfer
