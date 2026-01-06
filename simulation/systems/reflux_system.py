from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class EconomicRefluxSystem:
    def __init__(self):
        self.balance: float = 0.0
        # Optional: Transaction log for debugging
        # self.transaction_log: list = []

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
        amount_per_household = total_amount / len(active_households)

        for agent in active_households:
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

        self.balance = 0.0 # Reset
