from _typeshed import Incomplete
from modules.finance.api import ISettlementSystem as ISettlementSystem
from modules.simulation.api import AgentID as AgentID, IAgent as IAgent
from simulation.models import Transaction as Transaction
from typing import Any

logger: Incomplete

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
    def process_estate_distribution(self, agent: IAgent, settlement_system: ISettlementSystem, tick: int = 0) -> list[Transaction]:
        """
        Distributes assets of the dead agent.
        Priority: Taxes -> Creditors -> Heirs -> Escheatment (Government).

        This method is called POST-EXECUTION of an incoming transfer, so funds
        are already in the dead agent's account.

        Returns:
            List[Transaction]: A list of transactions generated during distribution.
        """
