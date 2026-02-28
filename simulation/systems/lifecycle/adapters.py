from typing import List, Dict, Any, Optional
from simulation.dtos.api import SimulationState
from modules.simulation.api import (
    IAgingContext, IBirthContext, IDeathContext, AgentID
)

class BaseLifecycleContextAdapter:
    def __init__(self, state: SimulationState):
        self._state = state

    @property
    def time(self) -> int:
        return self._state.time

    @property
    def agents(self) -> Dict[AgentID, Any]:
        return self._state.agents

    @property
    def markets(self) -> Dict[str, Any]:
        return self._state.markets

class AgingContextAdapter(BaseLifecycleContextAdapter):
    def __init__(self, state: SimulationState, demographic_manager: Any):
        super().__init__(state)
        self._demographic_manager = demographic_manager

    @property
    def demographic_registry(self) -> Any:
        return self._demographic_manager

    @property
    def households(self) -> List[Any]:
        return self._state.households

    @property
    def firms(self) -> List[Any]:
        return self._state.firms

    @property
    def market_data(self) -> Dict[str, Any]:
        return self._state.market_data

    @property
    def stock_market(self) -> Any:
        return self._state.stock_market

class BirthContextAdapter(BaseLifecycleContextAdapter):
    @property
    def government_agent(self) -> Any:
        return self._state.primary_government

    @property
    def next_agent_id(self) -> int:
        return self._state.next_agent_id

    @next_agent_id.setter
    def next_agent_id(self, value: int) -> None:
        self._state.next_agent_id = value

    @property
    def households(self) -> List[Any]:
        return self._state.households

    @property
    def currency_registry_handler(self) -> Any:
        return self._state.currency_registry_handler

    @property
    def currency_holders(self) -> List[Any]:
        return self._state.currency_holders

    @property
    def stock_market(self) -> Any:
        return self._state.stock_market

    @property
    def shareholder_registry(self) -> Any:
        return self._state.shareholder_registry

    @property
    def ai_training_manager(self) -> Any:
        return self._state.ai_training_manager

    @property
    def ai_trainer(self) -> Any:
        return self._state.ai_trainer

    @property
    def logger(self) -> Any:
        return self._state.logger

    @property
    def goods_data(self) -> Any:
        return self._state.goods_data

    @property
    def tracker(self) -> Any:
        return self._state.tracker

    @property
    def government(self) -> Any:
        return self._state.primary_government

    @property
    def bank(self) -> Any:
        return self._state.bank

class DeathContextAdapter(BaseLifecycleContextAdapter):
    @property
    def households(self) -> List[Any]:
        return self._state.households

    @property
    def firms(self) -> List[Any]:
        return self._state.firms

    @property
    def inactive_agents(self) -> Dict[AgentID, Any]:
        return self._state.inactive_agents

    @property
    def currency_registry_handler(self) -> Any:
        return self._state.currency_registry_handler

    @property
    def currency_holders(self) -> List[Any]:
        return self._state.currency_holders

    @property
    def settlement_system(self) -> Any:
        return self._state.settlement_system

    @property
    def primary_government(self) -> Any:
        return self._state.primary_government

    @property
    def real_estate_units(self) -> List[Any]:
        return self._state.real_estate_units

    @property
    def bank(self) -> Any:
        return self._state.bank

    @property
    def transaction_processor(self) -> Any:
        return self._state.transaction_processor

    @property
    def transactions(self) -> List[Any]:
        return self._state.transactions
