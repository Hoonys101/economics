from typing import Dict, List, Optional, Any
from modules.simulation.api import AgentID, IAgent

class EstateRegistry:
    """
    Registry for managing agents that have been liquidated or are deceased (The Estate).
    Maintains a record of agents removed from the active AgentRegistry to allow
    final financial settlements (escheatment, tax, dividends) to complete.
    """
    def __init__(self) -> None:
        self._estate: Dict[AgentID, IAgent] = {}

    def add_to_estate(self, agent: IAgent) -> None:
        """Moves an agent to the estate registry."""
        if agent and hasattr(agent, 'id'):
             self._estate[agent.id] = agent

    def get_agent(self, agent_id: Any) -> Optional[IAgent]:
        """Retrieves an agent from the estate."""
        # Handle int/str conversion if necessary, similar to AgentRegistry
        if agent_id in self._estate:
            return self._estate[agent_id]

        # Try casting to int if string
        if isinstance(agent_id, str) and agent_id.isdigit():
             return self._estate.get(int(agent_id))

        return None

    def get_all_estate_agents(self) -> List[IAgent]:
        """Returns all agents currently in the estate."""
        return list(self._estate.values())
