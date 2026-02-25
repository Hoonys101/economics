from _typeshed import Incomplete
from modules.simulation.api import IOrchestratorAgent as IOrchestratorAgent, ISensoryDataProvider as ISensoryDataProvider
from simulation.core_agents import Household as Household
from simulation.dtos.agents import AgentBasicDTO as AgentBasicDTO, AgentDetailDTO as AgentDetailDTO
from simulation.engine import Simulation as Simulation
from simulation.firms import Firm as Firm

logger: Incomplete

class AgentService:
    simulation: Incomplete
    def __init__(self, simulation: Simulation) -> None: ...
    def get_agents_basic(self, limit: int = 500) -> list[AgentBasicDTO]:
        """
        Returns a lightweight list of agents for scatter plot visualization.
        Uses IAgent/IOrchestratorAgent protocols for type safety.
        """
    def get_agent_detail(self, agent_id: int) -> AgentDetailDTO | None:
        """
        Returns detailed information for a specific agent.
        """
