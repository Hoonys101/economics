from modules.finance.api import IAccountRegistry as IAccountRegistry
from modules.simulation.api import AgentID as AgentID

class AccountRegistry(IAccountRegistry):
    """
    Implementation of the Account Registry service.
    Manages the mapping between agents and their bank accounts.
    """
    def __init__(self) -> None: ...
    def register_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
        """Registers an account link between a bank and an agent."""
    def deregister_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
        """Removes an account link between a bank and an agent."""
    def get_account_holders(self, bank_id: AgentID) -> list[AgentID]:
        """Returns a list of all agents holding accounts at the specified bank."""
    def get_agent_banks(self, agent_id: AgentID) -> list[AgentID]:
        """Returns a list of banks where the agent holds an account."""
    def remove_agent_from_all_accounts(self, agent_id: AgentID) -> None:
        """Removes an agent from all bank account indices."""
