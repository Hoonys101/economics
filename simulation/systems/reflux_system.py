from typing import List, Optional, Any
import logging
from modules.finance.api import InsufficientFundsError

logger = logging.getLogger(__name__)

class EconomicRefluxSystem:
    def __init__(self):
        self.balance: float = 0.0
        # Optional: Transaction log for debugging
        # self.transaction_log: list = []

    @property
    def id(self) -> int:
        return -100

    @property
    def assets(self) -> float:
        return self.balance

    def deposit(self, amount: float) -> None:
        if amount > 0:
            self.balance += amount

    def withdraw(self, amount: float) -> None:
        if amount > 0:
            if self.balance < amount:
                raise InsufficientFundsError(f"RefluxSystem has insufficient funds: {self.balance} < {amount}")
            self.balance -= amount

    def capture(self, amount: float, source: str, category: str):
        """
        Captures money that would otherwise vanish.
        :param amount: Amount to capture
        :param source: 'Firm_ID' or 'Bank'
        :param category: 'marketing', 'capex', 'fixed_cost', 'net_profit'
        """
        if amount > 0:
            self.deposit(amount)
            logger.debug(f"REFLUX_CAPTURE | Captured {amount:.2f} from {source} ({category})")

    def distribute(self, households: list, settlement_system: Any = None):
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
        amount_per_household = total_amount / len(active_households)

        for agent in active_households:
            if settlement_system:
                settlement_system.transfer(self, agent, amount_per_household, "reflux_distribution")
            else:
                agent._add_assets(amount_per_household)

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

        if not settlement_system:
             self.balance = 0.0 # Reset only if manual transfer
