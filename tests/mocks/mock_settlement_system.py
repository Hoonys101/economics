from typing import Optional, Dict, List, Any
from modules.finance.api import ISettlementSystem, IFinancialAgent, SettlementOrder, AgentID, CurrencyCode, DEFAULT_CURRENCY
from simulation.models import Transaction

class MockSettlementSystem(ISettlementSystem):
    def __init__(self):
        self.recorded_transfers: List[SettlementOrder] = []
        self.balances: Dict[AgentID, Dict[CurrencyCode, int]] = {}

    def setup_balance(self, agent_id: AgentID, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY):
        if agent_id not in self.balances:
            self.balances[agent_id] = {}
        self.balances[agent_id][currency] = amount_pennies

    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.balances.get(agent_id, {}).get(currency, 0)

    def transfer(self, sender: IFinancialAgent, receiver: IFinancialAgent, amount_pennies: int, memo: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> Optional[Transaction]:
        # Record the transfer attempt
        order = SettlementOrder(
            sender_id=sender.id,
            receiver_id=receiver.id,
            amount_pennies=amount_pennies,
            currency=currency,
            memo=memo,
            transaction_type="MOCK_TRANSFER"
        )
        self.recorded_transfers.append(order)

        # Update mock balances (simulate transfer success)
        # In mock, we assume success unless we want to test failure
        # But we should respect balance constraints if we want realistic mock
        sender_bal = self.get_balance(sender.id, currency)

        # For simplicity in mock, allow overdrafts unless explicitly configured not to?
        # Real system blocks overdrafts.
        # Let's enforce it to catch bugs in tests.
        if sender_bal >= amount_pennies:
            self.setup_balance(sender.id, sender_bal - amount_pennies, currency)
            receiver_bal = self.get_balance(receiver.id, currency)
            self.setup_balance(receiver.id, receiver_bal + amount_pennies, currency)

            # Also update agents using _deposit/_withdraw if available, to emulate real system side effects
            if isinstance(sender, IFinancialAgent):
                try:
                    sender._withdraw(amount_pennies, currency)
                except Exception:
                    pass # Ignore if mock agent doesn't support it
            if isinstance(receiver, IFinancialAgent):
                try:
                    receiver._deposit(amount_pennies, currency)
                except Exception:
                    pass

            return Transaction(
                buyer_id=sender.id,
                seller_id=receiver.id,
                item_id="currency",
                quantity=amount_pennies,
                price=1.0,
                market_id="mock",
                transaction_type="transfer",
                time=0
            )
        else:
            return None

    def get_recorded_transfers(self) -> List[SettlementOrder]:
        return self.recorded_transfers

    def audit_total_m2(self, expected_total: Optional[int] = None) -> bool:
        """
        Mock implementation of M2 audit.
        """
        # For mock purposes, just return True or check if expected matches sum of balances
        if expected_total is None:
            return True

        total = sum(
            sum(agent_bals.values())
            for agent_bals in self.balances.values()
        )
        # Note: Default currency only? Or all?
        # Real impl uses DEFAULT_CURRENCY + deposits.
        # Mock simplifies.
        return total == expected_total
