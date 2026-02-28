from typing import Any, Dict, List
from unittest.mock import Mock

class SimulationStateBuilder:
    """
    Builder for SimulationState objects tailored for test setups.
    Avoids deep MagicMock dependency injections by instantiating PODs/Fakes where appropriate.
    """
    def __init__(self):
        self.state = Mock()
        self.state.agents = {}
        self.state.transactions = []
        self.state.time = 0
        self.state.primary_government = None
        self.state.central_bank = None
        self.state.settlement_system = None
        self.state.bank = None
        self.state.inactive_agents = {}
        self.state.taxation_system = None
        self.state.stock_market = None
        self.state.real_estate_units = []
        self.state.market_data = {}
        self.state.shareholder_registry = None

    def with_time(self, time: int) -> 'SimulationStateBuilder':
        self.state.time = time
        return self

    def with_agent(self, agent: Any) -> 'SimulationStateBuilder':
        self.state.agents[agent.id] = agent
        return self

    def with_primary_government(self, gov: Any) -> 'SimulationStateBuilder':
        self.state.primary_government = gov
        self.state.government = gov # Legacy compat
        if gov.id not in self.state.agents:
            self.state.agents[gov.id] = gov
        return self

    def with_central_bank(self, cb: Any) -> 'SimulationStateBuilder':
        self.state.central_bank = cb
        if cb.id not in self.state.agents:
            self.state.agents[cb.id] = cb
        return self

    def with_settlement_system(self, settlement: Any) -> 'SimulationStateBuilder':
        self.state.settlement_system = settlement
        return self

    def with_transactions(self, transactions: List[Any]) -> 'SimulationStateBuilder':
        self.state.transactions.extend(transactions)
        return self

    def build(self) -> Any:
        return self.state
