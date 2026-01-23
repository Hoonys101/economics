from typing import List, Optional, TYPE_CHECKING
import logging
from modules.finance.api import IFinancialEntity, InsufficientFundsError

if TYPE_CHECKING:
    from simulation.systems.settlement_system import SettlementSystem

logger = logging.getLogger(__name__)

class EconomicRefluxSystem(IFinancialEntity):
    def __init__(self, id: str = "reflux_system"):
        self.id = id
        self._balance: float = 0.0

    @property
    def assets(self) -> float:
        return self._balance

    @assets.setter
    def assets(self, value: float) -> None:
        # Allow direct setting for legacy compatibility or initialization,
        # but warn if possible? No, setter is often used by tests/frameworks.
        self._balance = value

    def deposit(self, amount: float) -> None:
        """Called by SettlementSystem."""
        if amount > 0:
            self._balance += amount

    def withdraw(self, amount: float) -> None:
        """Called by SettlementSystem."""
        if amount > 0:
            if self._balance < amount:
                 raise InsufficientFundsError(f"Reflux System has insufficient funds. Needed {amount:.2f}, has {self._balance:.2f}")
            self._balance -= amount

    def capture(self, amount: float, source: str, category: str):
        """
        Captures money that would otherwise vanish.
        If callers invoke this manually, we assume it's an injection or manual capture
        that is NOT handled by SettlementSystem (e.g. shadow leakage).
        If SettlementSystem is used, deposit() is called, so capture() should purely be for logging
        IF we can distinguish. But we can't easily.

        So we keep the logic: capture ADDS to balance.
        If a system uses SettlementSystem to transfer to Reflux, it should NOT call capture()
        unless capture() is changed to strictly logging.

        Refactoring Strategy:
        - Callers using SettlementSystem to transfer to Reflux should NOT call capture().
        - Callers strictly injecting money (e.g. LifecycleManager vaporization) call capture().
        """
        if amount > 0:
            self._balance += amount
            logger.debug(f"REFLUX_CAPTURE | Captured {amount:.2f} from {source} ({category})")

    def distribute(self, households: list, settlement_system: Optional['SettlementSystem'] = None):
        """
        Distributes the total balance equally to all active households.
        Simulates dividends and service sector wages.
        """
        if self._balance <= 0:
            return

        # Filter for active households only
        active_households = [h for h in households if getattr(h, "is_active", True)]

        if not active_households:
            return

        total_amount = self._balance
        # Calculate share
        amount_per_household = total_amount / len(active_households)

        # Distribute
        for agent in active_households:
            if settlement_system:
                # Atomic Transfer
                try:
                    settlement_system.transfer(self, agent, amount_per_household, "reflux_distribution")
                except Exception as e:
                    logger.error(f"REFLUX_DIST_ERROR | Failed to transfer to {agent.id}: {e}")
            else:
                # Legacy Fallback (Direct Modification)
                # self.withdraw(amount_per_household) # This modifies balance
                # But we iterate. Let's modify balance locally.
                self._balance -= amount_per_household

                if hasattr(agent, '_add_assets'):
                    agent._add_assets(amount_per_household)
                else:
                    agent.assets += amount_per_household

            # Record as additional labor income (Service Sector)
            if hasattr(agent, "labor_income_this_tick"):
                agent.labor_income_this_tick += amount_per_household

            # Legacy support if needed
            if hasattr(agent, 'income_history') and isinstance(agent.income_history, dict):
                 agent.income_history['service'] = agent.income_history.get('service', 0.0) + amount_per_household

        logger.info(
            f"REFLUX_DISTRIBUTE | Distributed {total_amount:.2f} to {len(active_households)} households. ({amount_per_household:.2f} each)",
            extra={"tags": ["reflux", "distribution"], "total_amount": total_amount}
        )

        # Ensure balance is reset/zeroed if logic was perfect.
        # If Settlement failed for some, balance remains.
        # If fallback used, balance decremented.
        # Ideally we don't force set to 0.0 unless we are sure.
