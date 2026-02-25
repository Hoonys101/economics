from modules.simulation.api import AgentID as AgentID, IAgent as IAgent
from typing import Any

class EstateRegistry:
    """
    Registry for managing agents that have been liquidated or are deceased (The Estate).
    Maintains a record of agents removed from the active AgentRegistry to allow
    final financial settlements (escheatment, tax, dividends) to complete.
    """
    def __init__(self) -> None: ...
    def add_to_estate(self, agent: IAgent) -> None:
        """Moves an agent to the estate registry."""
    def get_agent(self, agent_id: Any) -> IAgent | None:
        """Retrieves an agent from the estate."""
    def get_all_estate_agents(self) -> list[IAgent]:
        """Returns all agents currently in the estate."""
