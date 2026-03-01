from typing import Any, Dict
from modules.simulation.api import (
    ICommerceTickContext,
    IGovernanceTickContext,
    IFinanceTickContext,
    IMutationTickContext,
    ISimulationState
)

class TickContextAdapter(
    ICommerceTickContext,
    IGovernanceTickContext,
    IFinanceTickContext,
    IMutationTickContext
):
    """
    Adapter that wraps a SimulationState and exposes restricted domain-specific contexts.
    Provides a transitional bridge from the God-class SimulationState to domain protocols.
    """
    def __init__(self, simulation_state: Any):
        self._state = simulation_state

    # ICommerceTickContext implementation
    @property
    def current_time(self) -> int:
        return self._state.time

    @property
    def market_data(self) -> Dict[str, Any]:
        return getattr(self._state, 'market_data', {})

    @property
    def goods_data(self) -> Dict[str, Any]:
        return getattr(self._state, 'goods_data', {})

    # IGovernanceTickContext implementation
    @property
    def primary_government(self) -> Any:
        return self._state.government

    @property
    def taxation_system(self) -> Any:
        return getattr(self._state, 'taxation_system', None)

    # IFinanceTickContext implementation
    @property
    def bank(self) -> Any:
        return self._state.bank

    @property
    def central_bank(self) -> Any:
        return self._state.central_bank

    @property
    def monetary_ledger(self) -> Any:
        return self._state.monetary_ledger

    @property
    def saga_orchestrator(self) -> Any:
        return getattr(self._state, 'saga_orchestrator', None)

    # IMutationTickContext implementation
    def append_transaction(self, transaction: Any) -> None:
        if hasattr(self._state, 'append_transaction'):
            self._state.append_transaction(transaction)
        elif hasattr(self._state, 'transactions'):
            self._state.transactions.append(transaction)

    def append_effect(self, effect: Dict[str, Any]) -> None:
        if hasattr(self._state, 'append_effect'):
            self._state.append_effect(effect)
        elif hasattr(self._state, 'effects_queue'):
            self._state.effects_queue.append(effect)

    def append_god_command(self, command: Any) -> None:
        if hasattr(self._state, 'append_god_command'):
            self._state.append_god_command(command)
        elif hasattr(self._state, 'god_commands'):
            self._state.god_commands.append(command)

    def __getattr__(self, name: str) -> Any:
        """
        Transitional fallback to support legacy tests expecting a full SimulationState.
        This allows the adapter to be passed where a SimulationState is expected during Phase 1.
        """
        if hasattr(self._state, name):
            return getattr(self._state, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
