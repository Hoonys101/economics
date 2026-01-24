from typing import List, Optional
import logging
from modules.finance.api import IFinancialEntity, InsufficientFundsError

logger = logging.getLogger(__name__)

class EconomicRefluxSystem(IFinancialEntity):
    def __init__(self):
        self._id = 999999 # Special ID for Reflux
        self.balance: float = 0.0
        # Optional: Transaction log for debugging
        # self.transaction_log: list = []

    @property
    def id(self) -> int:
        return self._id

    @property
    def assets(self) -> float:
        return self.balance

    def deposit(self, amount: float) -> None:
        """IFinancialEntity implementation."""
        if amount > 0:
            self.capture(amount, "System", "Deposit")

    def withdraw(self, amount: float) -> None:
        """IFinancialEntity implementation."""
        if self.balance < amount:
            raise InsufficientFundsError(f"RefluxSystem has insufficient funds.")
        self.balance -= amount

    def capture(self, amount: float, source: str, category: str):
        """
        Captures money that would otherwise vanish.
        :param amount: Amount to capture
        :param source: 'Firm_ID' or 'Bank'
        :param category: 'marketing', 'capex', 'fixed_cost', 'net_profit'
        """
        if amount > 0:
            self.balance += amount
            logger.debug(f"REFLUX_CAPTURE | Captured {amount:.2f} from {source} ({category})")

    def distribute(self, households: list):
        """
        Distributes the total balance equally to all active households.
        Simulates dividends and service sector wages.
        """
        if self.balance <= 0:
            return

        # Filter for active households only
        active_households = [h for h in households if getattr(h, "is_active", True)]

        if not active_households:
            return

        total_amount = self.balance
        count = len(active_households)

        # WO-Fix: Exact Distribution to prevent floating point drift
        amount_per_household = total_amount / count

        distributed_so_far = 0.0

        for i, agent in enumerate(active_households):
            is_last = (i == count - 1)

            if is_last:
                # Give all remaining balance to the last agent to ensure zero-sum
                allocation = total_amount - distributed_so_far
            else:
                allocation = amount_per_household

            # We use _add_assets for now as this is a distribution phase separate from transactions?
            # Or should we generate transactions?
            # Reflux distribute happens in Phase 4 (Lifecycle/Post-Processing) in TickScheduler.
            # So direct modification is acceptable here as it's outside the Transaction Phase strictness?
            # Ideally yes, or we move it to Transaction Phase.
            # For now, leaving as direct modification (Legacy).
            agent._add_assets(allocation)
            distributed_so_far += allocation

            # Record as additional labor income (Service Sector)
            if hasattr(agent, "labor_income_this_tick"):
                agent.labor_income_this_tick += allocation

            # Legacy support if needed
            if hasattr(agent, 'income_history') and isinstance(agent.income_history, dict):
                 agent.income_history['service'] = agent.income_history.get('service', 0.0) + allocation

        logger.info(
            f"REFLUX_DISTRIBUTE | Distributed {total_amount:.4f} to {count} households. (Avg: {amount_per_household:.4f})",
            extra={"tags": ["reflux", "distribution"], "total_amount": total_amount}
        )

        self.balance = 0.0 # Reset
