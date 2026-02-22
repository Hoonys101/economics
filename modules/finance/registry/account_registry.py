from typing import Dict, List, Set
from collections import defaultdict
from modules.simulation.api import AgentID
from modules.finance.api import IAccountRegistry

class AccountRegistry(IAccountRegistry):
    """
    Implementation of the Account Registry service.
    Manages the mapping between agents and their bank accounts.
    """

    def __init__(self) -> None:
        # BankID -> Set[AgentID]
        self._bank_depositors: Dict[AgentID, Set[AgentID]] = defaultdict(set)
        # AgentID -> Set[BankID]
        self._agent_banks: Dict[AgentID, Set[AgentID]] = defaultdict(set)

    def register_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
        """Registers an account link between a bank and an agent."""
        self._bank_depositors[bank_id].add(agent_id)
        self._agent_banks[agent_id].add(bank_id)

    def deregister_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
        """Removes an account link between a bank and an agent."""
        if bank_id in self._bank_depositors:
            self._bank_depositors[bank_id].discard(agent_id)
            if not self._bank_depositors[bank_id]:
                del self._bank_depositors[bank_id]

        if agent_id in self._agent_banks:
            self._agent_banks[agent_id].discard(bank_id)
            if not self._agent_banks[agent_id]:
                del self._agent_banks[agent_id]

    def get_account_holders(self, bank_id: AgentID) -> List[AgentID]:
        """Returns a list of all agents holding accounts at the specified bank."""
        if bank_id in self._bank_depositors:
            return list(self._bank_depositors[bank_id])
        return []

    def get_agent_banks(self, agent_id: AgentID) -> List[AgentID]:
        """Returns a list of banks where the agent holds an account."""
        if agent_id in self._agent_banks:
            return list(self._agent_banks[agent_id])
        return []

    def remove_agent_from_all_accounts(self, agent_id: AgentID) -> None:
        """Removes an agent from all bank account indices."""
        if agent_id in self._agent_banks:
            # Copy to avoid modification during iteration
            banks = list(self._agent_banks[agent_id])
            for bank_id in banks:
                self.deregister_account(bank_id, agent_id)
