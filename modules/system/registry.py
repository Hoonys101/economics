from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING
from modules.system.api import IAgentRegistry

if TYPE_CHECKING:
    from simulation.agents import Agent
    from simulation.dtos.api import SimulationState

class AgentRegistry(IAgentRegistry):
    def __init__(self):
        self._state: Optional[SimulationState] = None

    def set_state(self, state: SimulationState) -> None:
        self._state = state

    def get_agent(self, agent_id: Any) -> Optional[Agent]:
        if self._state is None:
            return None

        agent = self._state.agents.get(agent_id)
        if agent:
            return agent

        # Fallback for government if not in agents map
        if hasattr(self._state, 'government') and self._state.government:
            if agent_id == "government" or agent_id == self._state.government.id:
                return self._state.government

        return None
