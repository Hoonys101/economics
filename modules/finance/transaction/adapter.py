from typing import Any
from modules.finance.transaction.api import IAccountAccessor, InvalidAccountError
from modules.finance.wallet.api import IWallet
from modules.system.api import IAgentRegistry

class RegistryAccountAccessor(IAccountAccessor):
    def __init__(self, registry: IAgentRegistry):
        self.registry = registry

    def _get_agent(self, account_id: str) -> Any:
        # account_id in transaction is str, but agent id can be int.
        # We need to handle this conversion if registry expects int.
        # Agent IDs are often ints.

        agent_id: Any = account_id
        if isinstance(account_id, str) and account_id.isdigit():
             agent_id = int(account_id)

        agent = self.registry.get_agent(agent_id)
        if agent is None:
            # Try original string if conversion happened
            if agent_id != account_id:
                agent = self.registry.get_agent(account_id)

        return agent

    def get_wallet(self, account_id: str) -> IWallet:
        agent = self._get_agent(account_id)
        if agent is None:
            raise InvalidAccountError(f"Account (Agent) not found: {account_id}")

        if not hasattr(agent, 'wallet'):
             raise InvalidAccountError(f"Agent {account_id} does not have a wallet.")

        return agent.wallet

    def exists(self, account_id: str) -> bool:
        agent = self._get_agent(account_id)
        return agent is not None and hasattr(agent, 'wallet')
