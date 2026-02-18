from typing import List, Dict, Any, Optional
from modules.common.interfaces import IPropertyOwner, IResident, IMortgageBorrower
from modules.government.welfare.api import IWelfareRecipient
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from modules.government.dtos import IAgent
from modules.finance.api import IFinancialAgent

class GoldenAgent(IPropertyOwner, IResident, IMortgageBorrower, IWelfareRecipient, IFinancialAgent, IAgent):
    """
    A compliant agent implementation for testing purposes (Golden Sample).
    Implements all major protocols required by Government and Housing modules.
    Stores monetary values in integer pennies.
    """
    def __init__(self, agent_id: int, initial_assets: int = 0):
        self.id = agent_id
        # Internal storage in pennies (int)
        self._assets: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: initial_assets}

        # IMortgageBorrower
        self.current_wage: int = 0

        # IPropertyOwner
        self.owned_properties: List[int] = []

        # IResident
        self.residing_property_id: Optional[int] = None
        self.is_homeless: bool = True

        # IWelfareRecipient
        self.is_active: bool = True
        self.is_employed: bool = False
        self.needs: Any = {} # Dictionary of needs

    @property
    def assets(self) -> Dict[CurrencyCode, int]:
        """Exposes assets dictionary. Values are in pennies."""
        return self._assets

    @assets.setter
    def assets(self, value: Dict[CurrencyCode, int]):
        self._assets = value

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self._assets.get(currency, 0)

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return self._assets.copy()

    @property
    def total_wealth(self) -> int:
        return self._assets.get(DEFAULT_CURRENCY, 0)

    def add_property(self, property_id: int) -> None:
        self.owned_properties.append(property_id)

    def remove_property(self, property_id: int) -> None:
        if property_id in self.owned_properties:
            self.owned_properties.remove(property_id)

    # Test helpers (and IFinancialAgent implementation)
    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if currency not in self._assets:
            self._assets[currency] = 0
        self._assets[currency] += amount

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        current = self._assets.get(currency, 0)
        if current < amount:
            raise ValueError("Insufficient funds")
        self._assets[currency] -= amount

def create_golden_agent(agent_id: int, assets_pennies: int = 0, is_employed: bool = False) -> GoldenAgent:
    """Factory function to create a GoldenAgent with specified parameters."""
    agent = GoldenAgent(agent_id, assets_pennies)
    agent.is_employed = is_employed
    return agent
