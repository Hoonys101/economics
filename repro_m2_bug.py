import logging
from typing import Dict, Any, List
from simulation.systems.settlement_system import SettlementSystem
from modules.system.constants import ID_CENTRAL_BANK
from modules.system.api import DEFAULT_CURRENCY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("repro_m2")

class MockWallet:
    def __init__(self, balance: int, owner_id: int):
        self._balance = balance
        self.owner_id = owner_id
    
    def get_balance(self, currency: str = DEFAULT_CURRENCY) -> int:
        return self._balance

class MockEconState:
    def __init__(self, wallet):
        self.wallet = wallet
        self.assets = wallet.get_balance()
        self.inventory = {}

class MockAgent:
    def __init__(self, agent_id: int, wallet: MockWallet):
        self.id = agent_id
        self._econ_state = MockEconState(wallet)
        self.is_active = True

    # Implement IFinancialAgent protocol
    @property
    def balance_pennies(self) -> int:
        return self.get_balance()

    @property
    def total_wealth(self) -> int:
        return self.get_balance()

    def get_balance(self, currency: str = DEFAULT_CURRENCY) -> int:
        return self._econ_state.wallet.get_balance(currency)

    def get_liquid_assets(self, currency: str = DEFAULT_CURRENCY) -> int:
        return self.get_balance(currency)

    def get_total_debt(self) -> int:
        return 0

    def get_all_balances(self) -> Dict[str, int]:
        return {DEFAULT_CURRENCY: self.get_balance()}

    def deposit(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None:
        pass

    def withdraw(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None:
        pass

    def _deposit(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None:
        pass

    def _withdraw(self, amount: int, currency: str = DEFAULT_CURRENCY) -> None:
        pass

class MockRegistry:
    def __init__(self, agents: List[MockAgent]):
        self.agent_map = {a.id: a for a in agents}
    
    def get_all_financial_agents(self) -> List[MockAgent]:
        return list(self.agent_map.values())

def test_m2_poisoning():
    # 1. Setup Shared Wallet
    shared_wallet = MockWallet(balance=1000, owner_id=100) # Household owns it
    
    cb = MockAgent(agent_id=ID_CENTRAL_BANK, wallet=shared_wallet)
    hh = MockAgent(agent_id=100, wallet=shared_wallet)
    
    registry = MockRegistry([cb, hh])
    
    # 2. Setup Settlement System
    ss = SettlementSystem(logger=logger, agent_registry=registry)
    
    # 3. Calculate M2
    total_m2 = ss.get_total_m2_pennies()
    
    print(f"\nRESULTS:")
    print(f"CB ID: {cb.id}")
    print(f"HH ID: {hh.id}")
    print(f"Shared Balance: {shared_wallet.get_balance()}")
    print(f"Calculated M2: {total_m2}")
    
    if total_m2 == 1000:
        print("SUCCESS: M2 poisoning fix verified!")
    else:
        print(f"FAILURE: M2 poisoning still occurring (Expected 1000, got {total_m2})")

if __name__ == "__main__":
    test_m2_poisoning()
